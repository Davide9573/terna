import utility
import simulator
from pathlib import Path

NPZ_PATH = Path(__file__).parent / "power_2025.npz"

if __name__ == "__main__":
    # Load consumption, generation and import/export data from .npz file
    data = utility.load_power_data_from_npz(NPZ_PATH)
    print(f"\nSummary of power data loaded from {NPZ_PATH}:")
    utility.print_power_data_summary(data)
    utility.plot_power_data(data)
    
    # Simulate the production of electricity with surplus from photovoltaic, wind and storage
    max_capacity_=100
    k_pv_=3
    k_w_=3
    simulated_data = simulator.simulate_surplus(data, max_capacity=max_capacity_, k_pv=k_pv_, k_w=k_w_)

    # Plot the simulated data for consumption, generation and import/export
    print(f"\nSummary of power data simulated by\n"
          f"          - multiplying by {k_pv_} the installed photovoltaic power\n"
          f"          - multiplying by {k_w_} the installed wind power\n"
          f"          - adding {max_capacity_} GWh of storage capacity:")
    utility.print_power_data_summary(simulated_data)
    utility.plot_power_data(simulated_data)
