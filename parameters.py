
# Physical/Engineering parameters for the energy simulation
ETA_CHARGE = 0.9  # Charge efficiency of the storage
ETA_DISCHARGE = 0.9  # Discharge efficiency of the storage
NUCLEAR_BASE_LOAD_FACTOR = 0.3  # Nuclear base load factor, assumed to be 30% of the peak power


# LCOE values from https://www.eia.gov/outlooks/aeo/electricity_generation/pdf/LCOE_report.pdf
# Notice that LCOE is limited because it only reflects the cost to build and operate a plant, not the value of the plant to the grid
THERMAL_LCOE = 58470  # Levelized cost of electricity for thermal power ($/GWh)
PV_LCOE = 40380  # Levelized cost of electricity for photovoltaic power ($/GWh)
WIND_LCOE = 58330  # Levelized cost of electricity for wind power ($/GWh)
NUKE_LCOE = 87810  # Levelized cost of electricity for nuclear power ($/GWh)

# LCOS, the levelized cost of the storage, counterpart to LCOE
# LCOS values from https://www.pnnl.gov/projects/esgc-cost-performance/lcos-estimates
LCOS = 353000  # Levelized cost of storage ($/GWh)

# The price Italy pays, on average, for imported electricity
# Values from https://wits.worldbank.org/trade/comtrade/en/country/ITA/year/2024/tradeflow/Imports/partner/ALL/product/271600
IMPORT_COST = 96055  # Cost of imported electricity ($/GWh)


# List of power sources and their corresponding costs for simulation
SOURCE_COSTS = {
    "Net Import":       IMPORT_COST,
    "Thermal":          THERMAL_LCOE,
    "Nuclear":          NUKE_LCOE,
    "Storage":          LCOS,
    "Wind":             WIND_LCOE,
    "Photovoltaic":     PV_LCOE
}

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