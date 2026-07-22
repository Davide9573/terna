from dataclasses import dataclass, field
from parameters import SOURCE_COLORS, SOURCE_COSTS, SOURCES, OTHER_POWER_ITEMS, OTHER_POWER_ITEM_COLORS
from pathlib import Path
import numpy as np
import pandas as pd


@dataclass
class ElectricData:
    """Electric power, energy, storage capacity, and timing data for one scenario."""
    power_item: dict[str, np.ndarray] = field(default_factory=dict)  # Dictionary of power values per source, in GW, with keys as source names and values as NumPy arrays of power values over time
    power_peak: dict[str, tuple[float, str]] = field(default_factory=dict)  # Dictionary of peak power values per source, in GW, with keys as source names and values as tuples of (peak power value, timestamp of peak)
    energy_item: dict[str, tuple[float, float]] = field(default_factory=dict)  # Dictionary of energy values per source, in GWh, with keys as source names and values as tuples of (energy value, cost)
    start: pd.Timestamp = pd.Timestamp("1970-01-01")  # Start timestamp of the data, in UTC+02:00 timezone
    end: pd.Timestamp = pd.Timestamp("1970-01-01")      # End timestamp of the data, in UTC+02:00 timezone
    duration: pd.Timedelta = pd.Timedelta("0h")  # Duration of the data, calculated as end - start
    storage_capacity: float = 0.0  # Storage capacity, in GWh

    def compute_peaks(self) -> None:
        self.power_peak = {}
        total_power = np.zeros(len(next(iter(self.power_item.values()))))
        for key in self.power_item:
            if key in SOURCES:
                total_power += np.nan_to_num(self.power_item[key], nan=0.0)
        self.power_item["Total Production"] = total_power
        self.power_item["Curtailment"] = total_power - np.nan_to_num(
            self.power_item["Consumption"], nan=0.0
        )
        for key, values in self.power_item.items():
            power_peak = np.nanmax(values)
            peak_time = (
                self.start + int(np.nanargmax(values)) * pd.Timedelta(minutes=15)
            ).strftime("%Y-%m-%d %H:%M")
            self.power_peak[key] = (power_peak, peak_time)

    def compute_energy(self) -> None:
        self.duration = self.end - self.start
        k_year = 365 / self.duration.days if self.duration.days > 0 else 0
        self.energy_item = {}
        for key in SOURCES:
            energy_value = 0.0
            if key in self.power_item:
                energy_value = np.nansum(self.power_item[key]) / 4000
            if key == "Storage":
                cost_value = self.storage_capacity * SOURCE_COSTS[key] * k_year * 1e-6
            else:
                cost_value = energy_value * SOURCE_COSTS[key] * k_year * 1e-6
            self.energy_item[key] = (energy_value, cost_value)
        self.energy_item["Total Production"] = (
            np.nansum([self.energy_item[key][0] for key in SOURCES]),
            np.nansum([self.energy_item[key][1] for key in SOURCES]),
        )
        consumed_energy = np.nansum(self.power_item["Consumption"]) / 4000
        self.energy_item["Consumption"] = (consumed_energy, 0.0)
        if "Curtailment" in self.power_item:
            curtailed_energy = np.nansum(self.power_item["Curtailment"]) / 4000
            self.energy_item["Curtailment"] = (curtailed_energy, 0.0)
        self.energy_item = dict(
            sorted(self.energy_item.items(), key=lambda item: item[1][0], reverse=True)
        )


def normalize_to_daylight_saving_time(df: pd.DataFrame) -> pd.DataFrame:
    """Express local Italian timestamps using a continuous UTC+02:00 reference."""
    sample_key = next((column for column in ("Source", "Country") if column in df), None)
    if sample_key is None:
        sample_occurrence = df.groupby("Date", sort=False).cumcount()
    else:
        sample_occurrence = df.groupby(["Date", sample_key], sort=False).cumcount()

    sample_times = pd.DataFrame(
        {"Date": df["Date"], "occurrence": sample_occurrence}
    ).drop_duplicates()
    is_descending = df["Date"].iloc[0] > df["Date"].iloc[-1]
    is_daylight_saving_occurrence = (
        sample_times["occurrence"].gt(0)
        if is_descending
        else sample_times["occurrence"].eq(0)
    )
    daylight_saving_times = (
        sample_times["Date"].dt.tz_localize(
            "Europe/Rome", ambiguous=is_daylight_saving_occurrence.to_numpy()
        )
        .dt.tz_convert("UTC")
        .dt.tz_localize(None)
        + pd.Timedelta(hours=2)
    )
    daylight_saving_by_sample = pd.Series(
        daylight_saving_times.to_numpy(),
        index=pd.MultiIndex.from_frame(sample_times),
    )
    row_samples = pd.MultiIndex.from_arrays([df["Date"], sample_occurrence])
    df["Date"] = daylight_saving_by_sample.reindex(row_samples).to_numpy()
    return df


def load_generation_data_from_csv(csv_path: Path) -> ElectricData:
    """
    Read the CSV and return (dictionary { source: np.ndarray }, start timestamp).
    
    Sources and time range are derived from the data itself.
    Missing intervals are filled with NaN.
    """
    df = pd.read_csv(
        csv_path,
        encoding="utf-8-sig",
        dtype={"Date": str, "Generation": str, "Source": str},
    )
    # Neglect any metadata rows (e.g., "Applied filters: ...")
    df = df[df["Date"].str.match(r"\d{2}/\d{2}/\d{4}", na=False)].copy()
    df["Generation"] = pd.to_numeric(df["Generation"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, format="%d/%m/%Y %H:%M:%S")
    df = normalize_to_daylight_saving_time(df)
    df.sort_values("Date", inplace=True)

    sources = df["Source"].dropna().unique().tolist()

    # Temporal Index derived from the actual data range
    start = df["Date"].min().floor("15min")
    end   = df["Date"].max().floor("15min")
    expected_index = pd.date_range(start=start, end=end, freq="15min")

    generation: dict[str, np.ndarray] = {}
    for source in sources:
        src_df = df[df["Source"] == source].copy()
        src_series = (
            src_df.groupby("Date")["Generation"]
            .mean()
            .reindex(expected_index)   # NaN where data is missing
        )
        generation[source] = src_series.to_numpy(dtype=np.float64)

    return ElectricData(power_item=generation, start=start, end=end + pd.Timedelta(minutes=15))  # Include the last interval in the end timestamp


def load_consumption_data_from_csv(csv_path: Path) -> ElectricData:
    """
    Read the CSV and return (dictionary { direction: np.ndarray }, start timestamp).

    The time range is derived from the data itself.
    Missing intervals are filled with NaN.
    """
    df = pd.read_csv(
        csv_path,
        encoding="utf-8-sig",
        dtype={"Date": str, "Consumption": str},
    )
    # Neglect any metadata rows (e.g., "Applied filters: ...")
    df = df[df["Date"].str.match(r"\d{2}/\d{2}/\d{4}", na=False)].copy()
    df["Consumption"] = pd.to_numeric(df["Consumption"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, format="%d/%m/%Y %H:%M:%S")
    df = normalize_to_daylight_saving_time(df)
    df.sort_values("Date", inplace=True)

    # Temporal Index derived from the actual data range
    start = df["Date"].min().floor("15min")
    end   = df["Date"].max().floor("15min")
    expected_index = pd.date_range(start=start, end=end, freq="15min")

    consumption: dict[str, np.ndarray] = {
        "Consumption": (
            df.groupby("Date")["Consumption"]
            .mean()
            .reindex(expected_index)   # NaN where data is missing
            .to_numpy(dtype=np.float64)
        )
    }
    return ElectricData(power_item=consumption, start=start, end=end + pd.Timedelta(minutes=15))


def load_import_export_data_from_csv(csv_path: Path) -> ElectricData:
    """
    Read the CSV and return (dictionary { direction: np.ndarray }, start timestamp).

    Sources and time range are derived from the data itself.
    Missing intervals are filled with NaN.
    """
    df = pd.read_csv(
        csv_path,
        encoding="utf-8-sig",
        dtype={"Date": str, "Country": str, "Import": str, "Export": str},
    )
    # Neglect any metadata rows (e.g., "Applied filters: ...")
    df = df[df["Date"].str.match(r"\d{2}/\d{2}/\d{4}", na=False)].copy()
    df["Import"] = pd.to_numeric(df["Import"], errors="coerce")
    df["Export"] = pd.to_numeric(df["Export"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, format="%d/%m/%Y %H:%M:%S")
    df = normalize_to_daylight_saving_time(df)
    df.sort_values("Date", inplace=True)

    # Temporal Index derived from the actual data range
    start = df["Date"].min().floor("15min")
    end   = df["Date"].max().floor("15min")
    expected_index = pd.date_range(start=start, end=end, freq="15min")

    # Aggregate import and export data for all countries
    aggregated = df.groupby("Date")[["Import", "Export"]].sum()
    # Calculate the net import as the difference between import and export
    net_import = aggregated["Import"] - aggregated["Export"]

    import_export: dict[str, np.ndarray] = {
        "Import": aggregated["Import"].reindex(expected_index).to_numpy(dtype=np.float64),
        "Export": aggregated["Export"].reindex(expected_index).to_numpy(dtype=np.float64),
        "Net Import": net_import.reindex(expected_index).to_numpy(dtype=np.float64),
    }

    return ElectricData(power_item=import_export, start=start, end=end + pd.Timedelta(minutes=15))


def save_power_data_to_npz(data: ElectricData, npz_path: Path) -> None:
    """Save ElectricData to a .npz file (compressed NumPy format)."""
    np.savez(npz_path, __start__=np.array([data.start.isoformat()]), __end__=np.array([data.end.isoformat()]), **data.power_item)


def save_decarbonization_surface_to_csv(points: list[tuple[float, float, float]], csv_path: Path) -> None:
    """
    Save the decarbonization surface points to a CSV file.

    Parameters
    ----------
    points : list[tuple[float, float, float]]
        A list of tuples containing (k_pv_factor, k_w_factor, storage_capacity).
    csv_path : Path
        The path to the output CSV file.
    """
    df = pd.DataFrame(points, columns=["k_pv_factor", "k_w_factor", "storage_capacity"])
    df.to_csv(csv_path, index=False)


def load_decarbonization_surface_from_csv(csv_path: Path) -> list[tuple[float, float, float]]:
    """
    Load the decarbonization surface points from a CSV file.

    Parameters
    ----------
    csv_path : Path
        The path to the input CSV file.

    Returns
    -------
    list[tuple[float, float, float]]
        A list of tuples containing (k_pv_factor, k_w_factor, storage_capacity).
    """
    df = pd.read_csv(csv_path)
    return list(df.itertuples(index=False, name=None))


def load_power_data_from_npz(npz_path: Path) -> ElectricData:
    """
    Load and return an ElectricData instance from a .npz file
    previously saved with save_data_to_npz().
    """
    raw = np.load(npz_path, allow_pickle=False)
    start = pd.Timestamp(str(raw["__start__"][0])) if "__start__" in raw.files else pd.Timestamp("1970-01-01")
    end = pd.Timestamp(str(raw["__end__"][0])) if "__end__" in raw.files else pd.Timestamp("1970-01-01")
    generation = {
        key: np.nan_to_num(raw[key], nan=0.0)
        for key in raw.files
        if key != "__start__" and key != "__end__"
    }
    return ElectricData(power_item=generation, start=start, end=end)


def merge_power_data(*datasets: ElectricData) -> ElectricData:
    """
    Merge multiple ElectricData structures into a single one.

    All datasets must have the same frequency. The common temporal index
    is constructed as the union of the ranges of each dataset;
    duplicate keys in power_item are summed element-wise, treating NaN
    as zero before the summation.

    Parameters
    ----------
    *datasets : ElectricData
        Two or more instances of ElectricData to merge.

    Returns
    -------
    ElectricData
        Unified structure with start equal to the minimum among the datasets.
    """
    if not datasets:
        raise ValueError("At least one ElectricData instance must be provided for merging.")

    # Construct the common temporal index as the union of all dataset ranges
    all_starts = [d.start for d in datasets]
    global_start = min(all_starts)
    all_ends = [d.end for d in datasets]
    global_end = max(all_ends)
    freq = "15min"  # Assuming all datasets have the same frequency of 15 minutes

    def _array_to_series(arr: np.ndarray, start: pd.Timestamp, freq: str) -> pd.Series:
        idx = pd.date_range(start=start, periods=len(arr), freq=freq)
        return pd.Series(arr, index=idx, dtype=np.float64)

    def _merge_dicts(dicts: list[dict[str, np.ndarray]]) -> dict[str, np.ndarray]:
        """Sum the arrays with the same keys, treating NaN as 0."""
        all_keys: set[str] = set()
        for d in dicts:
            all_keys.update(d.keys())
    
        # Global index (union of all present ranges)
        all_indices: list[pd.DatetimeIndex] = []
        for i, d in enumerate(dicts):
            for arr in d.values():
                idx = pd.date_range(start=datasets[i].start, periods=len(arr), freq=freq)
                all_indices.append(idx)
        if not all_indices:
            return {}
        global_index = all_indices[0]
        for idx in all_indices[1:]:
            global_index = global_index.union(idx)

        result: dict[str, np.ndarray] = {}
        for key in all_keys:
            total = pd.Series(0.0, index=global_index, dtype=np.float64)
            for i, d in enumerate(dicts):
                if key in d:
                    s = _array_to_series(d[key], datasets[i].start, freq).reindex(global_index, fill_value=0.0)
                    total = total.add(s, fill_value=0.0)
            result[key] = total.to_numpy(dtype=np.float64)
        return result
    
    # Merge all poweritem of the dataset dictionaries, summing the duplicate keys
    merged_power_item = _merge_dicts([d.power_item for d in datasets])

    # Add the "Consumption" key if not present, with an array of NaNs of the correct length
    if "Consumption" not in merged_power_item:
        n_intervals = len(next(iter(merged_power_item.values())))
        # Consumption is the sum of all consumption sources, i.e., the arrays with keys in SOURCES.
        merged_power_item["Consumption"] = np.full(n_intervals, np.nan, dtype=np.float64)

    # Compute the global end time assuming frequency is 15 minutes and the length of the arrays is consistent
    all_ends = [d.end for d in datasets]
    global_end = max(all_ends)

    return ElectricData(
        power_item=merged_power_item,
        start=global_start,
        end=global_end
    )


def plot_power_data(data: ElectricData) -> None:
    """
    Plot a stacked graph of production by source, overlaying the consumption, import and export curves.

    Parameters
    ----------
    data : ElectricData
        the power data and corresponding energy data to plot.
    """
    power_item = data.power_item
    start = data.start
    freq = pd.Timedelta(minutes=15)  # Assuming 15-minute intervals for the power data
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker

    _default_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    # The stack plot is limited to the sources in SOURCES, in the order defined by SOURCE_COLORS.
    gen_keys = set(power_item.keys())
    sources = [s for s in SOURCE_COLORS if s in gen_keys and s in SOURCES]

    n = len(next(iter(power_item.values())))
    colors = [
        SOURCE_COLORS.get(s, _default_colors[i % len(_default_colors)])
        for i, s in enumerate(sources)
    ]

    x    = np.arange(n)
    data = [np.nan_to_num(power_item[s], nan=0.0) for s in sources]

    fig, ax = plt.subplots(figsize=(16, 6))
    ax.stackplot(x, data, labels=sources, colors=colors)

    # Overlay the export curve, if present in the data
    if "Export" in power_item:
        color = OTHER_POWER_ITEM_COLORS.get("Export", _default_colors[len(colors) % len(_default_colors)])
        ax.plot(x, np.nan_to_num(-power_item["Export"], nan=0.0), label="Export", color=color, linewidth=1.5)
    # Overlay the import curve, if present in the data
    if "Import" in power_item:
        color = OTHER_POWER_ITEM_COLORS.get("Import", _default_colors[len(colors) % len(_default_colors)])
        ax.plot(x, np.nan_to_num(power_item["Import"], nan=0.0), label="Import", color=color, linewidth=1.5)
    # Overlay the consumption curve, if present in the data
    if "Consumption" in power_item:
        color = OTHER_POWER_ITEM_COLORS.get("Consumption", _default_colors[len(colors) % len(_default_colors)])
        ax.plot(x, np.nan_to_num(power_item["Consumption"], nan=0.0), label="Consumption", color=color, linewidth=1.5)

    # Adaptive ticks: MaxNLocator keeps ~10 visible ticks at any zoom level
    if start is not None:
        timestamps = pd.date_range(start=start, periods=n, freq=freq)
        slots_per_day = int(pd.Timedelta("1D") / pd.Timedelta(freq))

        def _fmt(val, pos):
            idx = int(round(val))
            if 0 <= idx < n:
                visible = ax.get_xlim()[1] - ax.get_xlim()[0]
                fmt = "%Y-%m-%d" if visible > 4 * slots_per_day else "%m-%d %H:%M"
                return timestamps[idx].strftime(fmt)
            return ""
    else:
        def _fmt(val, pos):
            return str(int(round(val)))

    ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=10, integer=True))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_fmt))
    plt.setp(ax.get_xticklabels(), rotation=90, ha="center", va="top")
    ax.set_xlabel("")

    ax.set_title("Italian Electric Balance over Time", fontsize=16)
    ax.set_ylabel("Electric power generated (GW)")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="upper left")
    ax.grid(True, axis="y")
    plt.tight_layout()
    plt.show()


def plot_decarbonization_surface(
    points: list[tuple[float, float, float, float]], show: bool = True) -> None:
    """
    Plot a 3D storage-capacity surface colored by interpolated costs.

    Parameters
    ----------
    points : list[tuple[float, float, float, float]]
        A list of tuples containing (k_pv_factor, k_w_factor, storage_capacity, cost).
    """
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri

    if len(points) < 3:
        return

    k_pv_factors, k_w_factors, storage_capacities, costs = map(np.asarray, zip(*points))
    triangulation = mtri.Triangulation(k_pv_factors, k_w_factors)
    grid_k_pv, grid_k_w = np.meshgrid(
        np.linspace(k_pv_factors.min(), k_pv_factors.max(), 100),
        np.linspace(k_w_factors.min(), k_w_factors.max(), 100),
    )

    storage_interpolator = mtri.LinearTriInterpolator(
        triangulation, storage_capacities / 1000
    )
    cost_interpolator = mtri.LinearTriInterpolator(triangulation, costs)
    grid_storage = storage_interpolator(grid_k_pv, grid_k_w)
    grid_costs = cost_interpolator(grid_k_pv, grid_k_w)
    cost_normalization = plt.Normalize(vmin=costs.min(), vmax=costs.max())
    colormap = plt.get_cmap('viridis')

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(projection='3d')
    ax.plot_surface(
        grid_k_pv,
        grid_k_w,
        grid_storage,
        facecolors=colormap(cost_normalization(grid_costs)),
        linewidth=0,
        antialiased=True,
    )
    points_scatter = ax.scatter(
        k_pv_factors,
        k_w_factors,
        storage_capacities / 1000,
        c=costs,
        cmap=colormap,
        norm=cost_normalization,
        edgecolors='black',
        s=30,
    )
    fig.colorbar(points_scatter, ax=ax, shrink=0.7, pad=0.1, label='Costs (b€/year)')
    ax.set_xlabel('minimum PV power multiplicator')
    ax.set_ylabel('minimum wind power multiplicator')
    ax.set_zlabel('minimum storage capacity (TWh)')
    ax.set_title('Decarbonization Surface\n' \
                 'Minimum (k_pv, k_w, C) needed to decarbonize\n' \
                 'the Italian electricity generation system without nuclear power,\n' \
                 'and related additional costs (w.r.t. the 2025 scenario)', fontsize=14)
    plt.tight_layout()
    if show:
        plt.show()
    else:
        plt.close(fig)


def print_power_data_summary(data: ElectricData) -> None:
    """
    Print a summary of the electric data to the console.
    
    Parameters
    ----------
    data : ElectricData
        The electric data to print.
    """

    power_data = data
    energy_data = data
    # Print the table header
    print("-" * 93)
    print(f"{'Source':<18} {'Energy (TWh)':>14} {'Cost (G€)':>14} {'Power Peak (GW)':>16} {'Peak Time':>20}")

    # Print the energy production, peak power, and corresponding time for each source
    print("-" * 93)
    for source in energy_data.energy_item.keys():
        if source in SOURCES and energy_data.energy_item[source][0] > 0:
                print(f"{source:<18} {energy_data.energy_item[source][0]:>14.2f} {energy_data.energy_item[source][1]:>14.2f} {power_data.power_peak[source][0]:>16.2f} {power_data.power_peak[source][1]:>20}")

    # Print the total energy production (sum of all sources) and curtailment, including respective maximum power peaks and time
    print("-" * 93)
    print(f"{'Total Production':<18} {energy_data.energy_item['Total Production'][0]:>14.2f} {energy_data.energy_item['Total Production'][1]:>14.2f} {power_data.power_peak['Total Production'][0]:>16.2f} {power_data.power_peak['Total Production'][1]:>20}")
    print(f"{'Curtailment':<18} {energy_data.energy_item['Curtailment'][0]:>14.2f} {'---':>14} {power_data.power_peak['Curtailment'][0]:>16.2f} {power_data.power_peak['Curtailment'][1]:>20}")

    # Print the cumulative energy, the maximum peak, and the corresponding time, for each non-source power item
    print("-" * 93)
    for source in energy_data.energy_item.keys():
        if source in OTHER_POWER_ITEMS and energy_data.energy_item[source][0] > 0:
            print(f"{source:<18} {energy_data.energy_item[source][0]:>14.2f} {energy_data.energy_item[source][1]:>14.2f} {power_data.power_peak[source][0]:>16.2f} {power_data.power_peak[source][1]:>20}")
    print("-" * 93)


def print_differential_costs(data1: ElectricData, data2: ElectricData) -> None:
    """Print a summary of the differential cost data to the console.

    Parameters
    ----------
    data1 : ElectricData
        the energy data for the original scenario.
    data2 : ElectricData
        the energy data for the simulated scenario.
    """

    print("-" * 60)
    print(f"{'Source':<18} {'Additional Cost (G€)':>20}")
    print("-" * 60)
    total_diff = 0.0
    for source in SOURCES:
        diff = 0.0
        if source in data1.energy_item:
            diff -= data1.energy_item[source][1]
        if source in data2.energy_item:
            diff += data2.energy_item[source][1]
        total_diff += diff
        print(f"{source:<18} {diff:>20.2f}")
    print("-" * 60)
    print(f"{'Total':<18} {total_diff:>20.2f}")
    print("-" * 60)