from dataclasses import dataclass, field
from parameters import SOURCE_COLORS, SOURCE_COSTS, SOURCES, OTHER_POWER_ITEMS, OTHER_POWER_ITEM_COLORS
from pathlib import Path
import numpy as np
import pandas as pd


@dataclass
class PowerData:
    """Data structure collecting:
    - power production (per source), consumption and import/export data,
    - power peaks (per item) and respective date/time of occurrence,
    - start and end timestamp
    duration of samples is assumed to be 15 minutes."""
    power_item: dict[str, np.ndarray] = field(default_factory=dict)  # power values in GW
    power_peaks: dict[str, tuple[float, str]] = field(default_factory=dict)  # power values in GW
    start: pd.Timestamp = pd.Timestamp("1970-01-01")
    end: pd.Timestamp = pd.Timestamp("1970-01-01")


@dataclass
class EnergyData:
    """Data structure collecting:
    - energy production (per source), consumption and import/export data,
    - cost data for different energy sources,
    - duration of the time period considered."""
    energy_item: dict[str, tuple[float, float]] = field(default_factory=dict)  # energy values in TWh, 
    duration: pd.Timedelta = pd.Timedelta("0h") # in hours


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


def load_generation_data_from_csv(csv_path: Path) -> PowerData:
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

    return PowerData(power_item=generation, start=start, end=end + pd.Timedelta(minutes=15))  # Include the last interval in the end timestamp


def load_consumption_data_from_csv(csv_path: Path) -> PowerData:
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
    return PowerData(power_item=consumption, start=start, end=end + pd.Timedelta(minutes=15))


def load_import_export_data_from_csv(csv_path: Path) -> PowerData:
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

    return PowerData(power_item=import_export, start=start, end=end + pd.Timedelta(minutes=15))


def save_power_data_to_npz(data: PowerData, npz_path: Path) -> None:
    """Save PowerData to a .npz file (compressed NumPy format)."""
    np.savez(npz_path, __start__=np.array([data.start.isoformat()]), __end__=np.array([data.end.isoformat()]), **data.power_item)


def load_power_data_from_npz(npz_path: Path) -> PowerData:
    """
    Load and return a PowerData instance from a .npz file
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
    return PowerData(power_item=generation, start=start, end=end)


def merge_power_data(*datasets: PowerData) -> PowerData:
    """
    Merge multiple PowerData structures into a single one.

    All datasets must have the same frequency. The common temporal index
    is constructed as the union of the ranges of each dataset;
    duplicate keys in power_item are summed element-wise, treating NaN
    as zero before the summation.

    Parameters
    ----------
    *datasets : PowerData
        Two or more instances of PowerData to merge.

    Returns
    -------
    PowerData
        Unified structure with start equal to the minimum among the datasets.
    """
    if not datasets:
        raise ValueError("At least one PowerData instance must be provided for merging.")

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

    return PowerData(
        power_item=merged_power_item,
        start=global_start,
        end=global_end
    )


def compute_peaks(power_data: PowerData):
    power_data.power_peaks = {}
    # Compute the total production across all sources for each time interval
    total_power = np.zeros(len(next(iter(power_data.power_item.values()))))  # Initialize total power array
    for key in power_data.power_item.keys():
        if key in SOURCES:
            total_power += np.nan_to_num(power_data.power_item[key], nan=0.0)
    power_data.power_item["Total Production"] = total_power
    # Compute the power curtailment across all sources for each time interval
    curtailed_power = total_power.copy()  # Initialize curtailment power array
    curtailed_power -= np.nan_to_num(power_data.power_item["Consumption"], nan=0.0)
    power_data.power_item["Curtailment"] = curtailed_power
    # Compute the peak power and corresponding time for each source and other power items
    for key in power_data.power_item.keys():
        power_peak = np.nanmax(power_data.power_item[key])
        peak_time = (power_data.start + int(np.nanargmax(power_data.power_item[key])) * pd.Timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M")
        power_data.power_peaks[key] = (power_peak, peak_time)


def to_energy(power_data: PowerData) -> EnergyData:
    energy_data = EnergyData()
    energy_data.duration = power_data.end - power_data.start
    # Reparametrization factor to convert the costs to a solar year, based on the duration of the simulation, in hours
    k_year = 365 / energy_data.duration.days if energy_data.duration.days > 0 else 0
    for key in SOURCES:
        energy_value = 0
        if key in power_data.power_item:
            energy_value = np.nansum(power_data.power_item[key]) / 4000  # Convert from GW to TWh, assuming 15-minute intervals
        cost_value = energy_value * SOURCE_COSTS[key] * k_year * 1e-6  # Convert the costs to billions of dollars per year
        energy_data.energy_item[key] = (energy_value, cost_value)
    energy_data.energy_item["Total Production"] = (np.nansum([energy_data.energy_item[key][0] for key in SOURCES]) , np.nansum([energy_data.energy_item[key][1] for key in SOURCES]))
    consumed_energy = np.nansum(power_data.power_item["Consumption"]) / 4000
    energy_data.energy_item["Consumption"] = (consumed_energy, 0.0)  # Consumption has no associated cost
    if "Curtailment" in power_data.power_item:
        curtailed_energy = np.nansum(power_data.power_item["Curtailment"]) / 4000
        energy_data.energy_item["Curtailment"] = (curtailed_energy, 0.0)  # Curtailment has no associated cost
    # sort the energy_item dictionary by energy values in descending order
    energy_data.energy_item = {k: v for k, v in sorted(energy_data.energy_item.items(), key=lambda item: item[1][0], reverse=True)}
    return energy_data


def plot_power_data(data: PowerData) -> None:
    """
    Plot a stacked graph of production by source, overlaying the consumption, import and export curves.

    Parameters
    ----------
    data : PowerData
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


def plot_decarbonization_map(points: list[tuple[float, float, float, float]]) -> None:
    """
    Plot decarbonization storage capacity and additional costs in the k_pv-k_w plane.

    Parameters
    ----------
    points : list[tuple[float, float, float, float]]
        a list of tuples containing (k_pv_factor, k_w_factor, storage_capacity, cost) for each point on the curve.
    """
    import matplotlib.pyplot as plt
    if not points:
        return
    # Unzip the points into separate lists
    k_pv_factors, k_w_factors, storage_capacities, costs = zip(*points)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharex=True, sharey=True)
    maps = (
        (axes[0], storage_capacities, 'Storage Capacity (GWh)',
         'Storage Capacity\n(needed to decarbonize without nuclear power)'),
        (axes[1], costs, 'Costs (b€/year)',
         'Additional Costs\n(to decarbonize without nuclear power)'),
    )
    for ax, values, colorbar_label, title in maps:
        scatter = ax.scatter(k_pv_factors, k_w_factors, c=values, cmap='viridis', s=100)
        colorbar = fig.colorbar(scatter, ax=ax)
        colorbar.set_label(colorbar_label, rotation=90, labelpad=15)
        ax.set_xlabel('k_pv Factor')
        ax.set_title(title)
        ax.grid(True)

    axes[0].set_ylabel('k_w Factor')
    fig.suptitle('Decarbonization Map')
    plt.tight_layout()
    plt.show()


def plot_decarbonization_3d_map(points: list[tuple[float, float, float, float]]) -> None:
    """Plot interpolated 3D decarbonization surfaces for storage capacity and costs.

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

    fig = plt.figure(figsize=(16, 7))
    maps = (
        ('Storage Capacity (GWh)', storage_capacities,
         'Storage Capacity\n(needed to decarbonize without nuclear power)'),
        ('Costs (b€/year)', costs,
         'Additional Costs\n(to decarbonize without nuclear power)'),
    )
    for index, (z_label, values, title) in enumerate(maps, start=1):
        ax = fig.add_subplot(1, 2, index, projection='3d')
        interpolator = mtri.LinearTriInterpolator(triangulation, values)
        grid_values = interpolator(grid_k_pv, grid_k_w)
        surface = ax.plot_surface(
            grid_k_pv, grid_k_w, grid_values, cmap='viridis', linewidth=0, antialiased=True
        )
        ax.scatter(k_pv_factors, k_w_factors, values, color='black', s=20)
        fig.colorbar(surface, ax=ax, shrink=0.7, pad=0.1, label=z_label)
        ax.set_xlabel('k_pv Factor')
        ax.set_ylabel('k_w Factor')
        ax.set_zlabel(z_label)
        ax.set_title(title)

    fig.suptitle('Decarbonization Map')
    plt.tight_layout()
    plt.show()


def print_power_data_summary(data: tuple[PowerData, EnergyData]) -> None:
    """Print a summary of the power data to the console.
    
    Parameters
    ----------
    data : tuple[PowerData, EnergyData]
        the power data and corresponding energy data to print.
    """

    power_data = data[0]
    energy_data = data[1]
    # Print the table header
    print("-" * 93)
    print(f"{'Source':<18} {'Energy (TWh)':>14} {'Cost (G€)':>14} {'Power Peak (GW)':>16} {'Peak Time':>20}")

    # Print the energy production, peak power, and corresponding time for each source
    print("-" * 93)
    for source in energy_data.energy_item.keys():
        if source in SOURCES and energy_data.energy_item[source][0] > 0:
                print(f"{source:<18} {energy_data.energy_item[source][0]:>14.2f} {energy_data.energy_item[source][1]:>14.2f} {power_data.power_peaks[source][0]:>16.2f} {power_data.power_peaks[source][1]:>20}")

    # Print the total energy production (sum of all sources) and curtailment, including respective maximum power peaks and time
    print("-" * 93)
    print(f"{'Total Production':<18} {energy_data.energy_item['Total Production'][0]:>14.2f} {energy_data.energy_item['Total Production'][1]:>14.2f} {power_data.power_peaks['Total Production'][0]:>16.2f} {power_data.power_peaks['Total Production'][1]:>20}")
    print(f"{'Curtailment':<18} {energy_data.energy_item['Curtailment'][0]:>14.2f} {'---':>14} {power_data.power_peaks['Curtailment'][0]:>16.2f} {power_data.power_peaks['Curtailment'][1]:>20}")

    # Print the cumulative energy, the maximum peak, and the corresponding time, for each non-source power item
    print("-" * 93)
    for source in energy_data.energy_item.keys():
        if source in OTHER_POWER_ITEMS and energy_data.energy_item[source][0] > 0:
            print(f"{source:<18} {energy_data.energy_item[source][0]:>14.2f} {energy_data.energy_item[source][1]:>14.2f} {power_data.power_peaks[source][0]:>16.2f} {power_data.power_peaks[source][1]:>20}")
    print("-" * 93)


def print_differential_costs(data1: EnergyData, data2: EnergyData) -> None:
    """Print a summary of the differential cost data to the console.

    Parameters
    ----------
    data1 : EnergyData
        the energy data for the original scenario.
    data2 : EnergyData
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