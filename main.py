from numpy import empty

import utility
import simulator
from pathlib import Path

NPZ_PATH = Path(__file__).parent / "power_2025.npz"

def output_data(power_data: utility.ElectricData, title: str):
    power_data.compute_peaks()
    power_data.compute_energy()
    print(f"\n{title}:")
    utility.print_power_data_summary(power_data)
    utility.plot_power_data(power_data)
    

if __name__ == "__main__":
    # Load consumption, generation and import/export data from .npz file
    power_data = utility.load_power_data_from_npz(NPZ_PATH)
    # Plot and print the loaded data for consumption, generation and import/export
    title = f"Summary of power data loaded from {NPZ_PATH}"
    output_data(power_data, title)
    
    # Simulate the production of electricity with surplus from photovoltaic, wind and storage
    max_capacity_=2000
    k_pv_=10
    k_w_=1
    nuke =False
    simulated_data = simulator.simulate_alternative_scenario(power_in=power_data, max_capacity=max_capacity_, k_pv=k_pv_, k_w=k_w_, nuke=nuke)

    # Plot and print the simulated data for consumption, generation and import/export
    title = (f"Summary of power data simulated by\n"
             f"          - multiplying by {k_pv_} the installed photovoltaic power\n"
             f"          - multiplying by {k_w_} the installed wind power\n"
             f"           - adding {max_capacity_} GWh of storage capacity\n")
    output_data(simulated_data, title)

    # Compute and print the additional costs and of the simulated scenario compared to the original one
    print("\nAdditional costs of the simulated scenario compared to the original one:")
    power_data.compute_energy()
    utility.print_differential_costs(power_data, simulated_data)

    decarbonization_data = simulator.compute_decarbonization_surface(
        power_data, k_pv_range=20.0, k_w_range=20.0, capacity_range=10000.0)
    if decarbonization_data is not None and len(decarbonization_data) > 0:
        utility.plot_decarbonization_surface(decarbonization_data)
