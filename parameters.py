
# Physical/Engineering parameters for the energy simulation
ETA_CHARGE = 0.9  # Charge efficiency of the storage
ETA_DISCHARGE = 0.9  # Discharge efficiency of the storage
NUCLEAR_BASE_LOAD_FACTOR = 0.3  # Nuclear base load factor, assumed to be 30% of the peak power


# LCOE values from https://www.eia.gov/outlooks/aeo/electricity_generation/pdf/LCOE_report.pdf
# Notice that LCOE is limited because it only reflects the cost to build and operate a plant, not the value of the plant to the grid
THERMAL_LCOE = 65000  # Levelized cost of electricity for thermal power (€/GWh)
PV_LCOE = 44000  # Levelized cost of electricity for photovoltaic power (€/GWh)
WIND_LCOE = 64000  # Levelized cost of electricity for wind power (€/GWh)
NUKE_LCOE = 95000  # Levelized cost of electricity for nuclear power (€/GWh)

# from https://www.pv-magazine.it/2025/05/14/irex-annual-report-nel-2025-moduli-in-aumento-ma-operazioni-stabili/
SELF_LCOE = 100000  # Levelized cost of electricity for self-consumption (€/GWh)

# European average LCOE values from https://renewablemarketwatch.com/blog/irenas-renewable-power-generation-costs-study-shows-renewable-energy-is-the-most-cost-effective-source-of-new-electricity-generation-in-2024/
HYDRO_LCOE = 68000  # Levelized cost of electricity for hydro power (€/GWh)
GEOTHERMAL_LCOE = 98000  # Levelized cost of electricity for geothermal power (€/GWh)

# LCOS, the levelized cost of the storage, counterpart to LCOE
# LCOS values from https://www.pnnl.gov/projects/esgc-cost-performance/lcos-estimates
LCOS = 388000  # Levelized cost of storage (€/GWh)

# The price Italy pays, on average, for imported electricity
# Values from https://wits.worldbank.org/trade/comtrade/en/country/ITA/year/2024/tradeflow/Imports/partner/ALL/product/271600
IMPORT_COST = 106000  # Cost of imported electricity (€/GWh)


# List of power sources
SOURCES = ["Net Import", "Thermal", "Nuclear", "Storage", "Self-consumption", "Photovoltaic", "Hydro", "Wind", "Geothermal"]

# Dictionary of power costs per source, in €/GWh
SOURCE_COSTS = {
    "Net Import":       IMPORT_COST,
    "Thermal":          THERMAL_LCOE,
    "Nuclear":          NUKE_LCOE,
    "Storage":          LCOS,
    "Self-consumption": SELF_LCOE,
    "Hydro":            HYDRO_LCOE,
    "Wind":             WIND_LCOE,
    "Geothermal":       GEOTHERMAL_LCOE,
    "Photovoltaic":     PV_LCOE
}

# Dictionary of power colors per source, for visualization purposes
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