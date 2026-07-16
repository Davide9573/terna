import utility
import simulator
from pathlib import Path

NPZ_PATH = Path(__file__).parent / "power_2025.npz"

def output_data(power_data: simulator.PowerData, title: str):
    utility.compute_peaks(power_data)  # Compute the peaks of the loaded power data
    print(f"\n{title}:")
    utility.print_power_data_summary((power_data, utility.to_energy(power_data)))
    utility.plot_power_data(power_data)
    

if __name__ == "__main__":
    # Load consumption, generation and import/export data from .npz file
    power_data = utility.load_power_data_from_npz(NPZ_PATH)
    # Plot and print the loaded data for consumption, generation and import/export
    title = f"Summary of power data loaded from {NPZ_PATH}"
    # output_data(power_data, title)
    
    # Simulate the production of electricity with surplus from photovoltaic, wind and storage
    max_capacity_=100
    k_pv_=3
    k_w_=2
    nuke =True
    simulated_data = simulator.simulate_alternative_scenario(power_in=power_data, max_capacity=max_capacity_, k_pv=k_pv_, k_w=k_w_, nuke=nuke)

    # Plot and print the simulated data for consumption, generation and import/export
    title = (f"Summary of power data simulated by\n"
             f"          - multiplying by {k_pv_} the installed photovoltaic power\n"
             f"          - multiplying by {k_w_} the installed wind power\n"
             f"          - adding {max_capacity_} GWh of storage capacity\n")
    output_data(simulated_data[0], title)

    # Compute and print the additional costs and of the simulated scenario compared to the original one
    simulated_costs = simulator.simulate_costs(energy_before=utility.to_energy(power_data), energy_after=utility.to_energy(simulated_data[0]))
    print(title)
    utility.print_cost_data_summary(simulated_costs)
