from dataclasses import dataclass, field
from parameters import SOURCE_COLORS, SOURCES, OTHER_POWER_ITEMS, OTHER_POWER_ITEM_COLORS
from pathlib import Path
import numpy as np
import pandas as pd


@dataclass
class PowerData:
    """Data structure that collects production data (per source), consumption and import/export data, and the start timestamp."""
    power_item: dict[str, np.ndarray] = field(default_factory=dict)
    start: pd.Timestamp = pd.Timestamp("1970-01-01")
    freq: str = "15min"

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

    return PowerData(power_item=generation, start=start)


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
    return PowerData(power_item=consumption, start=start)


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

    return PowerData(power_item=import_export, start=start)


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

    freq = datasets[0].freq
    if any(d.freq != freq for d in datasets):
        raise ValueError("All datasets must have the same frequency.")

    # Construct the common temporal index as the union of all dataset ranges
    all_starts = [d.start for d in datasets]
    global_start = min(all_starts)

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

    return PowerData(
        power_item=merged_power_item,
        start=global_start,
        freq=freq,
    )


def save_power_data_to_npz(data: PowerData, npz_path: Path) -> None:
    """Save PowerData to a .npz file (compressed NumPy format)."""
    np.savez(npz_path, __start__=np.array([data.start.isoformat()]), **data.power_item)


def load_power_data_from_npz(npz_path: Path) -> PowerData:
    """
    Load and return a PowerData instance from a .npz file
    previously saved with save_data_to_npz().
    """
    raw = np.load(npz_path, allow_pickle=False)
    start = pd.Timestamp(str(raw["__start__"][0])) if "__start__" in raw.files else pd.Timestamp("1970-01-01")
    generation = {
        key: np.nan_to_num(raw[key], nan=0.0)
        for key in raw.files
        if key != "__start__"
    }
    return PowerData(power_item=generation, start=start)


def plot_power_data(data: PowerData) -> None:
    """
    Plot a stacked graph of production by source, overlaying the consumption, import and export curves.

    Parameters
    ----------
    data : PowerData
        Data structure to plot.
    """
    power_item = data.power_item
    start = data.start
    freq = data.freq
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


def print_power_data_summary(data: PowerData) -> None:
    """Print a summary of the power data to the console."""

    # Print the table header
    print("-" * 93)
    print(f"{'Source':<18} {'Energy (TWh)':>14} {'Power Peak (GW)':>16} {'Peak Time':>20}")

    # Print the energy production, peak power, and corresponding time for each source
    energy_production = {source: np.nansum(vec) / 4000 for source, vec in data.power_item.items() if source in SOURCES} # Convert to TWh
    energy_production_sorted = dict(sorted(energy_production.items(), key=lambda item: item[1], reverse=True))
    power_peaks = {source: np.nanmax(vec) for source, vec in data.power_item.items() if source in SOURCES}
    peak_times = {
        source: (data.start + int(np.nanargmax(vec)) * pd.Timedelta(data.freq)).strftime("%Y-%m-%d %H:%M")
        for source, vec in data.power_item.items() if source in SOURCES
    }
    print("-" * 93)
    for source, source_production in energy_production_sorted.items():
        if source_production > 0:
            print(f"{source:<18} {source_production:>14.2f} {power_peaks[source]:>16.2f} {peak_times[source]:>20}")

    # Print the total energy production (sum of all sources), the maximum power peak, and the corresponding time
    total_power = sum(np.nan_to_num(vec, nan=0.0) for source, vec in data.power_item.items() if source in SOURCES)
    total_power_peak_idx = int(np.argmax(total_power))
    total_power_peak = total_power[total_power_peak_idx]
    total_power_peak_time = (data.start + total_power_peak_idx * pd.Timedelta(data.freq)).strftime("%Y-%m-%d %H:%M")
    total_all_sources = sum(energy_production.values())
    print("-" * 93)
    print(f"{'Total Production':<18} {total_all_sources:>14.2f} {total_power_peak:>16.2f} {total_power_peak_time:>20}")

    # Print the cumulative energy, the maximum peak, and the corresponding time, for each non-source power item
    energy_production = {power_item: np.nansum(vec) / 4000 for power_item, vec in data.power_item.items() if power_item in OTHER_POWER_ITEMS} # Convert to TWh
    energy_production_sorted = dict(sorted(energy_production.items(), key=lambda item: item[1], reverse=True))
    power_peaks = {power_item: np.nanmax(vec) for power_item, vec in data.power_item.items() if power_item in OTHER_POWER_ITEMS}
    peak_times = {
        power_item: (data.start + int(np.nanargmax(vec)) * pd.Timedelta(data.freq)).strftime("%Y-%m-%d %H:%M")
        for power_item, vec in data.power_item.items() if power_item in OTHER_POWER_ITEMS
    }
    print("-" * 93)
    for power_item, item_energy in energy_production_sorted.items():
        if item_energy > 0:
            print(f"{power_item:<18} {item_energy:>14.2f} {power_peaks[power_item]:>16.2f} {peak_times[power_item]:>20}")
    print("-" * 93)

    # Calculate the total nuclear energy produced, in GWh
    if "Nuclear" in data.power_item:
        total_nuclear_energy = sum(data.power_item["Nuclear"]) / 4  # Assuming the power is in GW and the time step is 15 minutes