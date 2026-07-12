
# Physical/Engineering parameters for the energy simulation
ETA_CHARGE = 0.9  # Charge efficiency of the storage
ETA_DISCHARGE = 0.9  # Discharge efficiency of the storage
NUCLEAR_BASE_LOAD_FACTOR = 0.3  # Nuclear base load factor, assumed to be 30% of the peak power

# Below are representative LCOE values for new-build electricity in 2025 dollars per MWh from recent U.S. outlooks and analyses:
# utility thermal (natural gas combined-cycle) about $58.47/MWh,
# utility solar PV about $40.38/MWh, onshore wind about $58.33/MWh,
# and advanced nuclear about $87.81/MWh in EIA’s AEO2026 case for plants entering service in 2031.
# LCOE values from https://www.eia.gov/outlooks/aeo/electricity_generation/pdf/LCOE_report.pdf
# Notice that LCOE is limited because it only reflects the cost to build and operate a plant, not the value of the plant to the grid
THERMAL_LCOE = 58470  # Levelized cost of electricity for thermal power ($/GWh)
PV_LCOE = 40380  # Levelized cost of electricity for photovoltaic power ($/GWh)
WIND_LCOE = 58330  # Levelized cost of electricity for wind power ($/GWh)
NUKE_LCOE = 87810  # Levelized cost of electricity for nuclear power ($/GWh)

# LCOS is the storage counterpart to LCOE: instead of asking “what does it cost to generate electricity?”,
# it asks “what does it cost to store electricity and later release it?”. It typically includes capital cost,
# replacement/augmentation costs, operations and maintenance, and charging-related losses or costs, depending on the methodology used.
# LCOS values from https://www.pnnl.gov/projects/esgc-cost-performance/lcos-estimates
LCOS = 353000  # Levelized cost of storage ($/GWh)

# The price Italy pays for imported electricity averaged about €100/MWh in 2024 according to think tank Ember
# (see https://www.reuters.com/business/energy/italy-power-costs-stay-sky-high-despite-clean-energy-push-2024-09-20/).
# Italy imported about 58.3 TWh of electricity in 2024, worth about $5.42 billion,
# which implies an average import value of roughly $93/MWh using those trade figures. That is a trade-value estimate, not the same thing as the wholesale market price
IMPORT_COST = 93000  # Cost of imported electricity ($/GWh)


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