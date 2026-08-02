#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <thread>
#include <unordered_map>
#include <utility>
#include <vector>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

namespace {

constexpr std::array<std::string_view, 12> kSources = {
    "Net Import", "Thermal", "Nuclear", "Storage", "Self-consumption",
    "Photovoltaic", "Hydro", "Wind", "Geothermal", "Import", "Export",
    "Consumption",
};

enum Source : std::size_t {
    NetImport,
    Thermal,
    Nuclear,
    Storage,
    SelfConsumption,
    Photovoltaic,
    Hydro,
    Wind,
    Geothermal,
    Import,
    Export,
    Consumption,
};

constexpr std::size_t source_count = kSources.size();
constexpr double kMwhPerGwh = 1'000.0;
constexpr double kGeurPerEur = 1e-9;
using Series = std::array<std::vector<double>, source_count>;

struct SimulationParameters {
    double eta_charge;
    double eta_discharge;
    double nuclear_base_load_factor;
    double storage_capacity_cost;
    std::unordered_map<std::string, double> source_costs;
};

struct ScenarioResult {
    Series values;
    double final_capacity;
};

struct LocalDateTime {
    int year;
    unsigned month;
    unsigned day;
    unsigned hour;
    unsigned minute;
};

std::int64_t days_from_civil(int year, unsigned month, unsigned day) {
    year -= month <= 2;
    const int era = (year >= 0 ? year : year - 399) / 400;
    const unsigned year_of_era = static_cast<unsigned>(year - era * 400);
    const unsigned day_of_year = (153 * (month + (month > 2 ? -3 : 9)) + 2) / 5 + day - 1;
    const unsigned day_of_era = year_of_era * 365 + year_of_era / 4 - year_of_era / 100 + day_of_year;
    return era * 146097 + static_cast<int>(day_of_era) - 719468;
}

LocalDateTime civil_from_days(std::int64_t days) {
    days += 719468;
    const std::int64_t era = (days >= 0 ? days : days - 146096) / 146097;
    const unsigned day_of_era = static_cast<unsigned>(days - era * 146097);
    const unsigned year_of_era = (day_of_era - day_of_era / 1460 + day_of_era / 36524 - day_of_era / 146096) / 365;
    const int year = static_cast<int>(year_of_era + era * 400);
    const unsigned day_of_year = day_of_era - (365 * year_of_era + year_of_era / 4 - year_of_era / 100);
    const unsigned month_prime = (5 * day_of_year + 2) / 153;
    const unsigned day = day_of_year - (153 * month_prime + 2) / 5 + 1;
    const unsigned month = month_prime + (month_prime < 10 ? 3 : -9);
    return {year + (month <= 2), month, day, 0, 0};
}

unsigned weekday_sunday_zero(int year, unsigned month, unsigned day) {
    return static_cast<unsigned>((days_from_civil(year, month, day) + 4) % 7 + 7) % 7;
}

unsigned days_in_month(int year, unsigned month) {
    static constexpr std::array<unsigned, 12> days = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    if (month == 2 && (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0))) {
        return 29;
    }
    return days[month - 1];
}

unsigned last_sunday(int year, unsigned month) {
    const unsigned last_day = days_in_month(year, month);
    return last_day - weekday_sunday_zero(year, month, last_day);
}

LocalDateTime parse_local_datetime(const std::string& value) {
    LocalDateTime result{};
    char first = 0;
    char second = 0;
    char third = 0;
    char fourth = 0;
    std::istringstream stream(value);
    int day = 0;
    int month = 0;
    int hour = 0;
    int minute = 0;
    int seconds = 0;
    if (!(stream >> day >> first >> month >> second >> result.year >> hour >> third >> minute >> fourth >> seconds)
        || first != '/' || second != '/' || third != ':' || fourth != ':') {
        throw std::invalid_argument("Invalid CSV timestamp: " + value);
    }
    result.month = static_cast<unsigned>(month);
    result.day = static_cast<unsigned>(day);
    result.hour = static_cast<unsigned>(hour);
    result.minute = static_cast<unsigned>(minute);
    return result;
}

std::int64_t to_reference_minutes(const LocalDateTime& local, bool ambiguous_dst) {
    const unsigned march_sunday = last_sunday(local.year, 3);
    const unsigned october_sunday = last_sunday(local.year, 10);
    bool dst = false;
    if (local.month > 3 && local.month < 10) {
        dst = true;
    } else if (local.month == 3) {
        dst = local.day > march_sunday || (local.day == march_sunday && local.hour >= 2);
    } else if (local.month == 10) {
        dst = local.day < october_sunday || (local.day == october_sunday && local.hour < 3);
        if (local.day == october_sunday && local.hour == 2) {
            dst = ambiguous_dst;
        }
    }
    const auto local_minutes = days_from_civil(local.year, local.month, local.day) * 24 * 60
        + static_cast<std::int64_t>(local.hour) * 60 + local.minute;
    return local_minutes + (dst ? 0 : 60);
}

std::string reference_timestamp(std::int64_t minutes) {
    const auto days = minutes / (24 * 60);
    const auto minutes_of_day = minutes - days * 24 * 60;
    auto civil = civil_from_days(days);
    civil.hour = static_cast<unsigned>(minutes_of_day / 60);
    civil.minute = static_cast<unsigned>(minutes_of_day % 60);
    char buffer[32]{};
    std::snprintf(buffer, sizeof(buffer), "%04d-%02u-%02uT%02u:%02u:00", civil.year, civil.month, civil.day, civil.hour, civil.minute);
    return buffer;
}

std::vector<std::string> parse_csv_row(const std::string& line) {
    std::vector<std::string> fields;
    std::string field;
    bool quoted = false;
    for (std::size_t index = 0; index < line.size(); ++index) {
        const char character = line[index];
        if (character == '"') {
            if (quoted && index + 1 < line.size() && line[index + 1] == '"') {
                field += character;
                ++index;
            } else {
                quoted = !quoted;
            }
        } else if (character == ',' && !quoted) {
            fields.push_back(field);
            field.clear();
        } else {
            field += character;
        }
    }
    fields.push_back(field);
    for (auto& value : fields) {
        if (!value.empty() && value.back() == '\r') {
            value.pop_back();
        }
    }
    return fields;
}

double parse_number(const std::string& value) {
    try {
        return std::stod(value);
    } catch (const std::exception&) {
        return std::numeric_limits<double>::quiet_NaN();
    }
}

py::dict load_csv(const std::string& path, const std::string& kind) {
    std::ifstream file(path, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Cannot open CSV file: " + path);
    }
    std::string line;
    if (!std::getline(file, line)) {
        throw std::runtime_error("CSV file is empty: " + path);
    }
    if (line.starts_with("\xEF\xBB\xBF")) {
        line.erase(0, 3);
    }
    const auto header = parse_csv_row(line);
    std::unordered_map<std::string, std::size_t> columns;
    for (std::size_t index = 0; index < header.size(); ++index) {
        columns.emplace(header[index], index);
    }
    const auto column = [&columns](const char* name) {
        const auto iterator = columns.find(name);
        if (iterator == columns.end()) {
            throw std::invalid_argument(std::string("Missing CSV column: ") + name);
        }
        return iterator->second;
    };
    const auto date_column = column("Date");
    const auto source_column = kind == "generation" ? column("Source") : (kind == "import_export" ? column("Country") : 0);
    const auto first_value_column = kind == "generation" ? column("Generation") : (kind == "consumption" ? column("Consumption") : column("Import"));
    const auto second_value_column = kind == "import_export" ? column("Export") : 0;

    using Values = std::vector<double>;
    std::unordered_map<std::string, std::map<std::int64_t, Values>> grouped;
    std::map<std::int64_t, Values> import_export;
    std::unordered_map<std::string, std::size_t> occurrences;
    bool descending = false;
    bool direction_known = false;
    std::int64_t first_local_minute = 0;
    while (std::getline(file, line)) {
        const auto fields = parse_csv_row(line);
        if (date_column >= fields.size() || fields[date_column].size() < 10 || fields[date_column][2] != '/') {
            continue;
        }
        const auto local = parse_local_datetime(fields[date_column]);
        const auto local_minute = days_from_civil(local.year, local.month, local.day) * 24 * 60
            + static_cast<std::int64_t>(local.hour) * 60 + local.minute;
        if (!direction_known) {
            if (occurrences.empty()) {
                first_local_minute = local_minute;
            } else if (local_minute != first_local_minute) {
                descending = local_minute < first_local_minute;
                direction_known = true;
            }
        }
        const std::string occurrence_key = fields[date_column] + "\x1f" + (source_column < fields.size() ? fields[source_column] : "");
        const std::size_t occurrence = occurrences[occurrence_key]++;
        const auto minute = to_reference_minutes(local, descending ? occurrence > 0 : occurrence == 0);
        if (kind == "import_export") {
            if (first_value_column >= fields.size() || second_value_column >= fields.size()) {
                continue;
            }
            auto& values = import_export[minute];
            if (values.empty()) {
                values.assign(2, 0.0);
            }
            const double import_value = parse_number(fields[first_value_column]);
            const double export_value = parse_number(fields[second_value_column]);
            if (!std::isnan(import_value)) {
                values[0] += import_value;
            }
            if (!std::isnan(export_value)) {
                values[1] += export_value;
            }
        } else {
            if (source_column >= fields.size() || first_value_column >= fields.size()) {
                continue;
            }
            const std::string source = kind == "consumption" ? "Consumption" : fields[source_column];
            grouped[source][minute].push_back(parse_number(fields[first_value_column]));
        }
    }
    py::dict output;
    py::dict series;
    std::int64_t start = std::numeric_limits<std::int64_t>::max();
    std::int64_t end = std::numeric_limits<std::int64_t>::min();
    const auto observe_range = [&start, &end](const auto& series_map) {
        for (const auto& [minute, values] : series_map) {
            (void)values;
            start = std::min(start, minute);
            end = std::max(end, minute);
        }
    };
    if (kind == "import_export") {
        observe_range(import_export);
    } else {
        for (const auto& [source, value_map] : grouped) {
            (void)source;
            observe_range(value_map);
        }
    }
    if (start > end) {
        throw std::runtime_error("CSV contains no data rows: " + path);
    }
    start = (start / 15) * 15;
    end = (end / 15) * 15;
    const auto length = static_cast<std::size_t>((end - start) / 15 + 1);
    const auto build_array = [start, length](const auto& value_map, std::size_t component, bool average_values) {
        py::array_t<double> array(length);
        auto output_values = array.mutable_unchecked<1>();
        for (std::size_t index = 0; index < length; ++index) {
            output_values(index) = std::numeric_limits<double>::quiet_NaN();
        }
        for (const auto& [minute, values] : value_map) {
            const auto index = static_cast<std::size_t>((minute - start) / 15);
            if (component < values.size()) {
                if (!average_values) {
                    output_values(index) = values[component];
                    continue;
                }
                double sum = 0.0;
                std::size_t valid_count = 0;
                for (const double value : values) {
                    if (!std::isnan(value)) {
                        sum += value;
                        ++valid_count;
                    }
                }
                if (valid_count > 0) {
                    output_values(index) = sum / static_cast<double>(valid_count);
                }
            }
        }
        return array;
    };
    if (kind == "import_export") {
        py::array_t<double> imports = build_array(import_export, 0, false);
        py::array_t<double> exports = build_array(import_export, 1, false);
        py::array_t<double> net(length);
        auto import_values = imports.unchecked<1>();
        auto export_values = exports.unchecked<1>();
        auto net_values = net.mutable_unchecked<1>();
        for (std::size_t index = 0; index < length; ++index) {
            net_values(index) = import_values(index) - export_values(index);
        }
        series["Import"] = std::move(imports);
        series["Export"] = std::move(exports);
        series["Net Import"] = std::move(net);
    } else {
        for (const auto& [source, values] : grouped) {
            series[py::str(source)] = build_array(values, 0, true);
        }
    }
    output["series"] = std::move(series);
    output["start"] = reference_timestamp(start);
    output["end"] = reference_timestamp(end + 15);
    return output;
}

SimulationParameters parse_parameters(const py::dict& parameters) {
    const auto get_double = [&parameters](const char* key) {
        if (!parameters.contains(key)) {
            throw std::invalid_argument(std::string("Missing simulation parameter: ") + key);
        }
        return py::cast<double>(parameters[key]);
    };

    SimulationParameters result{
        .eta_charge = get_double("ETA_CHARGE"),
        .eta_discharge = get_double("ETA_DISCHARGE"),
        .nuclear_base_load_factor = get_double("NUCLEAR_BASE_LOAD_FACTOR"),
        .storage_capacity_cost = get_double("STORAGE_CAPACITY_COST"),
        .source_costs = {},
    };
    if (parameters.contains("SOURCE_COSTS")) {
        result.source_costs = py::cast<std::unordered_map<std::string, double>>(parameters["SOURCE_COSTS"]);
    }
    return result;
}

Series parse_series(const py::dict& input) {
    Series result;
    std::size_t size = 0;
    bool has_size = false;
    for (std::size_t source = 0; source < source_count; ++source) {
        const auto key = py::str(kSources[source]);
        if (!input.contains(key)) {
            continue;
        }
        const auto array = py::array_t<double, py::array::c_style | py::array::forcecast>(input[key]);
        if (array.ndim() != 1) {
            throw std::invalid_argument(std::string(kSources[source]) + " must be a one-dimensional float64 array.");
        }
        if (!has_size) {
            size = static_cast<std::size_t>(array.shape(0));
            has_size = true;
        } else if (size != static_cast<std::size_t>(array.shape(0))) {
            throw std::invalid_argument("All power series must have the same length.");
        }
        const auto values = array.unchecked<1>();
        result[source].reserve(size);
        for (py::ssize_t index = 0; index < array.shape(0); ++index) {
            result[source].push_back(values(index));
        }
    }
    if (!has_size) {
        throw std::invalid_argument("At least one power series is required.");
    }
    for (auto& values : result) {
        if (values.empty()) {
            values.assign(size, 0.0);
        }
    }
    return result;
}

void redistribute(Series& output, const Series& input, std::size_t index, double& capacity,
                  double max_capacity, double k_pv, double k_w, bool nuke,
                  const SimulationParameters& parameters) {
    for (std::size_t source = 0; source < source_count; ++source) {
        output[source][index] = input[source][index];
    }

    output[Photovoltaic][index] = k_pv * input[Photovoltaic][index];
    output[Wind][index] = k_w * input[Wind][index];
    double surplus = input[Photovoltaic][index] * (k_pv - 1.0)
        + input[Wind][index] * (k_w - 1.0);

    if (surplus > input[Thermal][index]) {
        output[Thermal][index] = 0.0;
        surplus -= input[Thermal][index];
    } else {
        output[Thermal][index] -= surplus;
        surplus = 0.0;
    }
    if (surplus > input[Import][index]) {
        output[Import][index] = 0.0;
        output[NetImport][index] = -input[Export][index];
        surplus -= input[Import][index];
    } else {
        output[Import][index] -= surplus;
        output[NetImport][index] -= surplus;
        surplus = 0.0;
    }

    capacity += surplus / 4.0 * parameters.eta_charge;
    capacity = std::min(capacity, max_capacity);
    if (capacity > 0.0) {
        const double discharge = std::min(capacity * 4.0 * parameters.eta_discharge, output[Thermal][index]);
        output[Storage][index] += discharge;
        output[Thermal][index] -= discharge;
        capacity -= discharge / 4.0 / parameters.eta_discharge;
    }
    if (capacity > 0.0) {
        const double discharge = std::min(capacity * 4.0 * parameters.eta_discharge, output[Import][index]);
        output[Storage][index] += discharge;
        output[Import][index] -= discharge;
        output[NetImport][index] -= discharge;
        capacity -= discharge / 4.0 / parameters.eta_discharge;
    }
    if (nuke) {
        output[Nuclear][index] = output[Thermal][index];
        output[Thermal][index] = 0.0;
    }
}

ScenarioResult simulate(const Series& input, double max_capacity, double k_pv, double k_w, bool nuke,
                        const SimulationParameters& parameters) {
    if (max_capacity < 0.0 || parameters.eta_charge <= 0.0 || parameters.eta_discharge <= 0.0) {
        throw std::invalid_argument("Storage capacity and efficiencies must be positive.");
    }
    ScenarioResult result{.values = input, .final_capacity = max_capacity};
    const auto size = input[Photovoltaic].size();
    for (std::size_t index = 0; index < size; ++index) {
        redistribute(result.values, input, index, result.final_capacity, max_capacity, k_pv, k_w, nuke, parameters);
    }
    if (nuke) {
        const double nuclear_peak = *std::max_element(result.values[Nuclear].begin(), result.values[Nuclear].end());
        const double base_load = nuclear_peak * parameters.nuclear_base_load_factor;
        for (std::size_t index = 0; index < size; ++index) {
            if (result.values[Nuclear][index] >= base_load) {
                continue;
            }
            double surplus = base_load - result.values[Nuclear][index];
            result.values[Nuclear][index] = base_load;
            const double storage_used = std::min(result.values[Storage][index], surplus);
            result.values[Storage][index] -= storage_used;
            result.final_capacity += storage_used / 4.0 / parameters.eta_discharge;
            surplus -= storage_used;
            result.values[Import][index] = std::max(0.0, result.values[Import][index] - surplus);
            result.values[NetImport][index] = result.values[Import][index] - result.values[Export][index];
        }
    }
    return result;
}

bool feasible(const Series& input, double max_capacity, double k_pv, double k_w,
              const SimulationParameters& parameters) {
    const auto result = simulate(input, max_capacity, k_pv, k_w, false, parameters);
    for (std::size_t index = 0; index < input[Photovoltaic].size(); ++index) {
        if (result.values[Thermal][index] > 0.0 || result.values[Import][index] > 0.0) {
            return false;
        }
    }
    return true;
}

double minimum_capacity(const Series& input, double capacity_range, double k_pv, double k_w,
                        const SimulationParameters& parameters) {
    if (!feasible(input, capacity_range, k_pv, k_w, parameters)) {
        return -1.0;
    }
    double low = 0.0;
    double high = capacity_range;
    const double resolution = capacity_range / 100.0;
    while (high - low > resolution) {
        const double current = (low + high) / 2.0;
        if (feasible(input, current, k_pv, k_w, parameters)) {
            high = current;
        } else {
            low = current;
        }
    }
    return high < capacity_range ? high : -1.0;
}

py::dict series_to_python(const Series& series) {
    py::dict result;
    for (std::size_t source = 0; source < source_count; ++source) {
        py::array_t<double> array(series[source].size());
        auto values = array.mutable_unchecked<1>();
        for (std::size_t index = 0; index < series[source].size(); ++index) {
            values(index) = series[source][index];
        }
        result[py::str(kSources[source])] = std::move(array);
    }
    return result;
}

py::dict run_scenario(const py::dict& series, double max_capacity, double k_pv, double k_w,
                      bool nuke, const py::dict& parameter_values) {
    const auto parameters = parse_parameters(parameter_values);
    const auto result = simulate(parse_series(series), max_capacity, k_pv, k_w, nuke, parameters);
    py::dict output = series_to_python(result.values);
    output["final_capacity"] = result.final_capacity;
    return output;
}

py::list run_surface(const py::dict& series, double k_pv_range, double k_w_range,
                     double capacity_range, const py::dict& parameter_values, unsigned int workers) {
    const auto input = parse_series(series);
    const auto parameters = parse_parameters(parameter_values);
    const double pv_step = k_pv_range / 10.0;
    const double wind_step = k_w_range / 10.0;
    std::vector<double> pv_values;
    for (double k_pv = k_pv_range; k_pv >= 1.0; k_pv -= pv_step) {
        pv_values.push_back(k_pv);
    }
    using SurfacePoint = std::array<double, 3>;
    std::vector<std::vector<SurfacePoint>> rows(pv_values.size());
    std::atomic<std::size_t> next_row{0};
    const unsigned int detected_workers = std::max(1U, std::thread::hardware_concurrency());
    const unsigned int requested_workers = workers == 0 ? detected_workers : workers;
    const unsigned int worker_count = std::min<unsigned int>(requested_workers, static_cast<unsigned int>(pv_values.size()));
    const auto compute_row = [&]() {
        while (true) {
            const std::size_t row_index = next_row.fetch_add(1);
            if (row_index >= pv_values.size()) {
                return;
            }
            const double k_pv = pv_values[row_index];
            auto& row = rows[row_index];
        for (double k_w = k_w_range; k_w >= 1.0; k_w -= wind_step) {
            const double capacity = minimum_capacity(input, capacity_range, k_pv, k_w, parameters);
            if (capacity < 0.0) {
                break;
            }
                row.push_back({k_pv, k_w, capacity});
            }
        }
    };
    std::vector<std::thread> pool;
    pool.reserve(worker_count);
    for (unsigned int index = 0; index < worker_count; ++index) {
        pool.emplace_back(compute_row);
    }
    for (auto& worker : pool) {
        worker.join();
    }
    py::list results;
    for (const auto& row : rows) {
        for (const auto& point : row) {
            results.append(py::make_tuple(point[0], point[1], point[2]));
        }
    }
    return results;
}

py::dict run_costs(const py::dict& series, double storage_capacity, double duration_days,
                   const py::dict& parameter_values) {
    const auto input = parse_series(series);
    const auto parameters = parse_parameters(parameter_values);
    if (duration_days < 0.0) {
        throw std::invalid_argument("duration_days cannot be negative.");
    }
    const double annualization = duration_days > 0.0 ? 365.0 / duration_days : 0.0;
    py::dict result;
    double total = 0.0;
    for (std::size_t source = 0; source < 9; ++source) {
        const std::string key(kSources[source]);
        const auto cost_it = parameters.source_costs.find(key);
        const double unit_cost = cost_it == parameters.source_costs.end() ? 0.0 : cost_it->second;
        double energy = 0.0;
        for (const double value : input[source]) {
            if (!std::isnan(value)) {
                energy += value;
            }
        }
        energy /= 4.0;
        double cost = energy * kMwhPerGwh * unit_cost * annualization * kGeurPerEur;
        if (source == Storage) {
            cost += storage_capacity * kMwhPerGwh * parameters.storage_capacity_cost * kGeurPerEur;
        }
        result[py::str(kSources[source])] = py::make_tuple(energy, cost);
        total += cost;
    }
    result["Total"] = total;
    return result;
}

}  // namespace

PYBIND11_MODULE(_terna_cpp, module) {
    module.doc() = "Native C++20 engine for Terna energy scenarios.";
    module.def("simulate", &run_scenario, py::arg("series"), py::arg("max_capacity"),
               py::arg("k_pv"), py::arg("k_w"), py::arg("nuke"), py::arg("parameters"));
    module.def("decarbonization_surface", &run_surface, py::arg("series"), py::arg("k_pv_range"),
               py::arg("k_w_range"), py::arg("capacity_range"), py::arg("parameters"), py::arg("workers") = 0);
    module.def("energy_costs", &run_costs, py::arg("series"), py::arg("storage_capacity"),
               py::arg("duration_days"), py::arg("parameters"));
    module.def("load_csv", &load_csv, py::arg("path"), py::arg("kind"));
}