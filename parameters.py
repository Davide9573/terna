
# Physical/Engineering parameters for the energy simulation
ETA_CHARGE = 0.9  # Charge efficiency of the storage
ETA_DISCHARGE = 0.9  # Discharge efficiency of the storage
NUCLEAR_BASE_LOAD_FACTOR = 0.3  # Nuclear base load factor, assumed to be 30% of the peak power


# Italian/European 2024 cost baseline for new capacity, expressed in real €/MWh.
# The values are central estimates, excluding network and wider system-integration costs.
# LCOE is a plant-level metric and does not represent the value a technology provides to the grid.
# Sources: IEA/NEA Projected Costs of Generating Electricity and IRENA Renewable Power
# Generation Costs in 2023. Italian conditions inform the gas, solar and onshore-wind uplift.
THERMAL_LCOE = 110  # Natural-gas combined-cycle generation, representative of Italy (€/MWh)
PV_LCOE = 55  # Utility-scale photovoltaic generation in Italy (€/MWh)
WIND_LCOE = 70  # Onshore wind generation in Italy; excludes offshore wind (€/MWh)
NUKE_LCOE = 160  # New European nuclear build; Italy has no operating nuclear fleet (€/MWh)

# Distributed photovoltaic generation behind the meter, not the avoided retail bill (€/MWh).
SELF_LCOE = 85

# New projects: these technologies are highly site-specific, particularly in Italy (€/MWh).
HYDRO_LCOE = 95
GEOTHERMAL_LCOE = 90

# Storage investment is modelled separately from its use to penalize unused capacity.
# This central estimate represents a four-hour grid-scale lithium-ion battery: annualized CAPEX,
# augmentation/replacement, and fixed O&M, expressed per MWh of installed usable capacity.
# A 1 TWh installation therefore costs 40 G€/year even if it is never discharged.
STORAGE_CAPACITY_COST = 40_000  # €/MWh-capacity/year

# Variable O&M per MWh discharged. The energy used to charge storage is already charged to its
# generating source, so it is not included here. Keep this separate from LCOS to avoid counting
# capital costs twice; LCOS normally spreads capital and O&M over assumed lifetime throughput.
STORAGE_VARIABLE_COST = 0  # €/MWh discharged

# 2024 Italian gross electricity-import unit value in €/MWh. WITS/Comtrade reports
# USD 5.602 bn for 58.3145 TWh; converting 96.07 USD/MWh at the 2024 ECB average
# EUR/USD rate (1.0824) gives 88.8 €/MWh, rounded to 89.
# Source: https://wits.worldbank.org/trade/comtrade/en/country/ITA/year/2024/tradeflow/Imports/partner/ALL/product/271600
IMPORT_COST = 89


# List of power sources
SOURCES = ["Net Import", "Thermal", "Nuclear", "Storage", "Self-consumption", "Photovoltaic", "Hydro", "Wind", "Geothermal"]

# Dictionary of power costs per source, in €/MWh
SOURCE_COSTS = {
    "Net Import":       IMPORT_COST,
    "Thermal":          THERMAL_LCOE,
    "Nuclear":          NUKE_LCOE,
    "Storage":          STORAGE_VARIABLE_COST,
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