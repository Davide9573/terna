
# Physical/Engineering parameters for the energy simulation
ETA_CHARGE = 0.9  # Charge efficiency of the storage
ETA_DISCHARGE = 0.9  # Discharge efficiency of the storage
NUCLEAR_BASE_LOAD_FACTOR = 0.3  # Nuclear base load factor, assumed to be 30% of the peak power

# List of power sources and their corresponding colors for visualization
SOURCES = ["Net Import", "Thermal", "Nuclear", "Storage", "Self-consumption", "Photovoltaic", "Hydro", "Wind", "Geothermal"]
SOURCE_COLORS = {
    "Net Import":       "#6600FF",
    "Thermal":          "#B22222",
    "Nuclear":          "#0055FF",
    "Storage":          "#FFA500",
    "Self-consumption": "#808080",
    "Hydro":            "#87CEEB",
    "Wind":             "#4CAF50",
    "Geothermal":       "#8B4513",
    "Photovoltaic":     "#FFD700"
}

# List of other power items and their corresponding colors for visualization
OTHER_POWER_ITEMS = ["Import", "Export", "Consumption"]
OTHER_POWER_ITEM_COLORS = {
    "Import":           "#0000FF",
    "Export":           "#FF0000",
    "Consumption":      "#000000"
}