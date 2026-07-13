# terna
Analysis and simulation of electricity production in Italy

## Project Summary

This project analyzes and visualizes the Italian electricity budget over a specified period (typically a full year), using data from Terna, the Italian transmission grid operator. It then runs an alternative scenario simulation that explores how increased photovoltaic (PV) and wind generation capacity, combined with energy storage systems, could completely replace thermal (fossil-fueled) generation, and how much storage capacity and photovoltaic and wind generation would be needed to achieve this goal.

---

## Environment Setup

### Prerequisites

- Python 3.11 or later
- A virtual environment (recommended)

### Create and activate the virtual environment

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### Install dependencies

```bash
pip install numpy pandas matplotlib
```

## Code execution

### Prepare the data

The project ships with a pre-built `power_2025.npz` binary file ready to use. If you need to rebuild it from the raw CSVs (e.g. after updating any of the source files), run:

```bash
python convert_csv_into_pnz.py
```

This reads `power_generation_2025.csv`, `power_imp_exp_2025.csv`, and `power_consumption_2025.csv`, aligns every source to a common 15-minute time grid, fills missing slots with NaN, merges the three datasets, and saves the result to `power_2025.npz`.

### Run the main script

```bash
python main.py
```

This reads `power_2025.npz` and plots the temporal distribution of each power source in a stacked chart, alongside charts showing power consumption, imports and exports.

<div align="center">
  <img src="Energy_Balance_2025.png" alt="Immagine" width="800">

  Italian energy balance (year 2025).
</div>

Then it prints a table summarizing energy production over the entire period considered, as well as the peak power and peak time for each source.

<div align="center">
  <img src="Energy_Balance_Summary_2025.png" alt="Immagine" width="500">

  Summary of energy balance.
</div>

The main script also performs a simple simulation of the temporal distribution and energy balance, based on various assumptions (see next section) regarding photovoltaic, wind and nuclear installed power. The simulation results are presented graphically and summarized in tabular form in a similar manner.

---

### Simulation

The simulation answers the question:

> *"If PV capacity were multiplied by a factor **k\_pv**, wind capacity by **k\_w**, and a storage with maximum capacity **C** GWh were added to the grid, how much thermal generation and net import could be avoided? And what if nuclear power is added?"*

#### Parameters

| Parameter | Symbol | Unit | Description |
|---|---|---|---|
| `max_capacity` | $C$ | GWh | Maximum usable storage capacity |
| `k_pv` | $k_{\text{pv}}$ | — | Multiplicative scale factor applied to the historical PV output |
| `k_w` | $k_w$ | — | Multiplicative scale factor applied to the historical wind output |
| `nuke` | — | boolean | Whether a simulated contribution from nuclear power has to be considered |
| `nuclear_base_load_factor` | $f_{\text{nuke}}$ | — | Minimum nuclear output as a fraction of peak nuclear power (= 0.3) |

Storage round-trip efficiency is modelled with separate charge and discharge efficiencies:

$$\eta_{\text{charge}} = \eta_{\text{discharge}} = 0.9$$

#### Simulation assumptions

1. Consumption remains unchanged, as do all other power-related parameters not specified below.

2. Photovoltaic and wind generation are simply multiplied by the respective $k$ factor.

3. Whether possible, excess energy is used to reduce thermal generation and, secondarily, to charge the storage system with a specified charge efficiency $\eta_{\text{charge}}$.

4. Whether possible, stored energy is used to reduce thermal generation and, secondarily, energy import, with a specified discharge efficiency $\eta_{\text{discharge}}$.

5. Storage capacity can never exceed the specified maximum capacity.

In case of added nuclear power:  

6. Residual thermal generation (after all surplus and storage displacements) is completely replaced by nuclear power.

7. Nuclear power cannot be modulated arbitrarily: a minimum base load equal to $f_{\text{nuke}} = 0.3$ of the simulated nuclear peak is enforced.

8. When nuclear base load exceeds the interval demand, the excess first displaces storage discharge (the storage is re-charged accordingly), then reduces energy imports.

#### Step-by-step logic (per 15-minute interval $t$)

The storage state is initialised at full capacity: $C_0 = C$.

1. **Scale renewable sources** — update PV and wind output with their respective scale factors:

$$P_{\text{PV},t}^{\text{new}} = k_{\text{pv}} \cdot P_{\text{PV},t}, \qquad P_{W,t}^{\text{new}} = k_w \cdot P_{W,t}$$

2. **Compute total renewable surplus**:

$$\text{surplus}_t = P_{\text{PV},t} \cdot (k_{\text{pv}} - 1) + P_{W,t} \cdot (k_w - 1)$$

3. **Displace thermal generation** with the surplus:
   - If $\text{surplus}_t > \text{Thermal}_t$: thermal is zeroed and the residual surplus carries over.
   - Otherwise: thermal is reduced by the surplus and the surplus is exhausted.

4. **Displace imports** with the remaining surplus:
   - If $\text{surplus}_t > \text{Import}_t$: imports are zeroed and the residual surplus carries over.
   - Otherwise: imports (and `Net Import`) are reduced by the surplus and the surplus is exhausted.

5. **Charge storage** with any remaining surplus (capped at $C$, excess is curtailed):

$$C_{t+1} = \min\!\left(C_t + \text{surplus} \cdot \frac{\eta_{\text{charge}}}{4},\; C\right)$$

6. **Discharge storage to cover residual thermal demand**:

$$P_{\text{storage},t} = \min\!\left(C_t \cdot 4 \cdot \eta_{\text{discharge}},\; \text{Thermal}_t\right)$$

$$C_{t+1} = C_t - \frac{P_{\text{storage},t}}{4 \cdot \eta_{\text{discharge}}}$$

7. **Discharge storage to cover residual imports** (if storage still has charge):

$$P_{\text{storage},t} \mathrel{+}= \min\!\left(C_t \cdot 4 \cdot \eta_{\text{discharge}},\; \text{Import}_t\right)$$

$$C_{t+1} = C_t - \frac{\Delta P}{4 \cdot \eta_{\text{discharge}}}$$

8. **Assign nuclear** (only if `nuke = True`): the residual thermal output is transferred to nuclear and thermal is zeroed:

$$P_{\text{Nuclear},t} = \text{Thermal}_t, \qquad \text{Thermal}_t = 0$$

#### Nuclear base-load post-processing (only if `nuke = True`)

After the main loop, a nuclear base load is computed as:

$$P_{\text{nuke,base}} = f_{\text{nuke}} \cdot \max_t\!\left(P_{\text{Nuclear},t}\right)$$

For each interval $t$ where $P_{\text{Nuclear},t} < P_{\text{nuke,base}}$, nuclear output is raised to the base load and the shortfall $\delta_t = P_{\text{nuke,base}} - P_{\text{Nuclear},t}$ is absorbed as follows:

1. **Displace storage discharge first** — if $P_{\text{Storage},t} \ge \delta_t$:

$$P_{\text{Storage},t} \mathrel{-}= \delta_t, \qquad C \mathrel{+}= \frac{\delta_t}{4 \cdot \eta_{\text{discharge}}}$$

2. **Otherwise**, storage is fully displaced and the remaining shortfall reduces imports:

$$\delta_t \mathrel{-}= P_{\text{Storage},t}, \quad P_{\text{Storage},t} = 0, \quad P_{\text{Import},t} = \max\!\left(0,\; P_{\text{Import},t} - \delta_t\right)$$

$$P_{\text{Net Import},t} = P_{\text{Import},t} - P_{\text{Export},t}$$

The result is a new `PowerData` that shows the modified mix: reduced (or zeroed) thermal and imports, scaled-up PV and wind, and an additional `Storage` source representing storage discharge.

<div align="center">
  <img src="Simulated_Balance_2025.png" alt="Immagine" width="800">

  Simulated energy balance, with 3 times photovoltaic available power and 50 GWh storage capacity.
</div>
<div align="center">
  <img src="Simulated_Balance_Summary_2025.png" alt="Immagine" width="500">

  Summary of simulated energy balance.
</div>

---

### Cost Computation

The function computes the cost difference of the simulated scenario with respect to the real one.  
Generally, the simulated scenario entails additional costs due to increased photovoltaic, wind and nuclear power and, above all, increased storage capacity.
On the other hand, savings are also achieved by reducing thermal energy production and net energy imports.
The costs are computed taking into account:
- Levelized Costs of Electricity (LCOE) for the different power sources, from https://www.eia.gov/outlooks/aeo/electricity_generation/pdf/LCOE_report.pdf
- Levelized Costs of Storage (LCOS), the counterpoart to LCOE, from https://www.pnnl.gov/projects/esgc-cost-performance/lcos-estimates
- The price Italy pays for imported electricity (about $5.6 billion in 2024) divided by the imported amount of electrical energy (about 58.3 TWh on the same year), from https://wits.worldbank.org/trade/comtrade/en/country/ITA/year/2024/tradeflow/Imports/partner/ALL/product/271600

| Source | Assumed Cost [$/MWh] | Description |
|---|---|---|
| Net Import | 96.05 | Average price of imported electricity |
| Thermal | 58.47 | LCOE for large-scale thermoelectric plants (natural gas combined-cycle) |
| Nuclear | 87.81 | LCOE for nuclear plants |
| Photovoltaic | 40.38 | LCOE for large-scale photovoltaic plants |
| Wind | 58.33 | LCOE for wind turbines (a mix of offshore and onshore installations) |
| Storage | 35.30 | LCOS for a mix of hydro-pump systems and electrochemical batteries |
||||

<div align="center">
  <img src="Simulated_Scenario_Additional_Costs.png" alt="Immagine" width="500">

  Summary of simulated scenario differential costs.
</div>