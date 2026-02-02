# OpenCLD: A Hybrid System Dynamics & AI Library in Python

[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)  

**OpenCLD** is a lightweight and intuitive Python library for building and simulating system dynamics models.
It provides core components for representing stocks, flows, and auxiliaries, making it easy to create and explore dynamic systems.
The library includes unit-aware modeling, dependency and consistency checks, structure graph visualization, tidy results export, and utilities for multi-run experiments.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Units Management](#unit-management)
- [Core Components](#core-components)
  - [Model](#model)
  - [Stock](#stock)
  - [Flow](#flow)
  - [Auxiliary](#auxiliary)
  - [Parameter](#parameter)
- [Advanced Features](#advanced-features)
  - [Monte Carlo Analysis](#monte-carlo-analysis)
  - [Table - Linear interpolation](#table)
  - [Loop and Polarity Analysis](#loop-and-polarity-analysis)
- [Plotting and Visualization](#plotting-and-visualization)
  - [Plotting Class](#plotting-class)

  <!--
  - [Delays](#delays)
  - [Behavior Modes](#behavior-modes)
  - [Feedback Loops](#feedback-loops)
  -->
- [Examples](#examples)
- [License](#license)

## Overview

OpenCLD is a small Python library for building and simulating system dynamics models. It uses a clear model grammar, Stock, Flow, Auxiliary, Parameter, with unit-aware values to keep models consistent and readable. With OpenCLD you can define variables with physical units, validate dependencies and dimensional consistency, run simulations and collect tidy results in pandas DataFrames, visualize the model structure, and run multi-experiment batches.

## Installation

You can install OpenCLD using pip:

```bash
pip install opencld
```

Or clone the repository and install from source:

```bash
git clone https://github.com/log-lab-polito/OpenCLD.git
cd OpenCLD
pip install -e .

```

## Unit Management

A core feature of OpenCLD is its robust handling of physical units, which prevents common errors in scientific modeling. This is managed by the UnitManager class, which wraps the powerful pint library.

*Key Features:*
- *Automatic Unit Registration:* If you use a unit that hasn't been defined (like "widget"), OpenCLD automatically registers it as a new base unit for counting. No need to define everything in advance.
- *Automatic SI Prefix Handling:* The library automatically understands standard SI prefixes. If you've defined "meter", you can immediately use "kilometer", "km", "cm", or "millimeter" without any extra definitions.
- *Dimensional Consistency:* All calculations within Stock updates, Flow rates, and Auxiliary functions are checked for dimensional consistency. For example, you cannot add meters to seconds. This catches logical errors in your model equations before you even run the simulation.
- *Extensible Registry:* While many units work out-of-the-box, you can provide your own custom unit definitions by creating a units.txt file in your project's root directory. This file will be automatically detected and loaded.

All unit functionality is accessed through the library's global ureg (unit registry) and Q_ (quantity factory) objects.

```python
from opencld import ureg, Q_

# 'person' will be auto-registered as a new base unit if it's the first time it's seen
population_qty = Q_(1000, "person") 

# 'km' is understood automatically because 'meter' is a base SI unit
distance_qty = Q_(5, "km") 

print(distance_qty.to("meter")) # Output: 5000.0 meter
```




## Core Components

### Model

The `Model` class is the main engine for building, running, and analyzing system dynamics models. It manages all components and handles simulation logic.

**Key Attributes:**
- `stocks`: Dictionary of Stock objects
- `flows`: Dictionary of Flow objects  
- `auxiliaries`: Dictionary of Auxiliary objects
- `parameters`: Dictionary of Parameter objects
- `timestep`: The simulation time step
- `time`: Current simulation time
- `history`: Record of all simulation states

**Key Methods:**
- `run(duration)`: Runs the simulation for a specified duration
- `step()`: Executes a single time step
- `get_results()`: Returns simulation results as a DataFrame
- `get_results_for_plot()`: Returns results with units stripped for plotting
- `to_df()`: Converts results to long-format DataFrame


**Example:**
```python
from opencld import Model, Stock, Flow, Parameter

# Create model components
population = Stock("Population", initial_value=1000, unit="people")
birth_rate = Parameter("birth_rate", value=0.05, unit="1/year")

def births_eq(state):
    return state["parameters"]["birth_rate"].value * state["stocks"]["Population"].value

births = Flow("Births", source_stock=None, target_stock=population, 
              rate_function=births_eq, unit="people/year")

# Create and run model
model = Model(
    stocks=[population],
    flows=[births], 
    parameters=[birth_rate],
    timestep=1.0,
    timestep_unit="year"
)

model.run(duration=50)
results = model.get_results_for_plot()
```

### Stock

A Stock represents an accumulation or level in your system. Stocks change over time through inflows and outflows.

**Key Attributes:**
- `name`: The name of the stock
- `value`: The current value of the stock
- `initial_value`: The starting value of the stock
- `unit`: Units of measurement
- `dimensions`: Optional array dimensions 

**Key Methods:**
- `get_value()`: Returns the current value of the stock

**Example:**
```python
from opencld import Stock

# Create a stock representing a population of 1000 people
population = Stock("Population", initial_value=1000, unit="people")

```


### Flow

A Flow represents a rate of change that affects stocks. Flows can be inflows (increasing a stock) or outflows (decreasing a stock).

**Key Attributes:**
- `name`: The name of the flow
- `source_stock`: The stock that the flow originates from (can be None for sources)
- `target_stock`: The stock that the flow goes to (can be None for sinks)
- `rate_function`: A function that calculates the flow rate
- `unit`: Units of measurement for the flow rate
- `dimensions`: Optional array dimensions 


**Key Methods:**
- `calculate_rate(system_state)`: Calculates the flow rate using the provided rate function
- `get_rate()`: Returns the current flow rate

**Example:**
```python
from opencld import Stock, Flow

# Stock used by the flow
population = Stock("Population", initial_value=1000, unit="people")

# Create a birth flow that increases the population
def births_eq(state):
    return state["stocks"]["Population"].value * 0.05  # 5% birth rate

births = Flow(
    name="Births",
    source_stock=None,   # external source
    target_stock=population,
    rate_function=births_eq,
    unit="people/year"
)

```

### Auxiliary

An Auxiliary variable represents intermediate calculations that help define relationships between stocks and flows. These variables vary over time and are recalculated at each simulation step.

**Key Attributes:**
- `name`: The name of the auxiliary variable
- `calculation_function`: A function that calculates the auxiliary variable's value
- `inputs`: A list of input variables that this auxiliary variable depends on
- `unit`: Units of measurement
- `dimensions`: Optional array dimensions


**Key Methods:**
- `calculate_value(system_state)`: Calculates the value using the provided calculation function
- `get_value()`: Returns the current value

**Example:**
```python
from opencld import Auxiliary
# Create an auxiliary variable for population density
def density_eq(state):
    return state["stocks"]["Population"].value / 100  # people per square km

population_density = Auxiliary(
    name="Population Density",
    calculation_function=density_eq,
    unit="people/km**2",
    inputs=["Population"]
)
```

### Parameter

A Parameter represents a constant value that does not change during a simulation. Parameters are used in calculations within flows and auxiliary variables.

**Key Attributes:**
- `name`: The name of the parameter
- `value`: The numerical value of the parameter
- `unit`: Units of measurement for the parameter

**Key Methods:**
- `get_value()`: Returns the value of the parameter

**Example:**
```python
from opencld import Parameter

# Create a parameter for the land area
land_area = Parameter("Land Area", value=100, unit="km**2")
```

## Advanced Features

### Monte Carlo Analysis

OpenCLD supports multiple-run simulations with stochastic parameters to assess uncertainty.

**Key Functions:**
- `Model.run_multiple()`: Run multiple simulations using a builder that returns a fresh `Model`

**Key Features:**

- Stochastic parameters via your `build_model()` fucntion
- Output modes: `full` or `start_end`
- Optional progress bar with `tqdm` (`show_progress = True`)
- Optional CSV export via `filepath`
- `duration` accepts float
- Fresh model per run to avoid side effects

**Returned DataFrame**
- `mode="full"`: tidy long DataFrame with columns:`time, run_id, variable, value, type `
- `mode="start_end"`: tidy summary with columns:`run_id, variable, type, start_value, end_value`

**Example:**
```python
import numpy as np  #to use the random function
from opencld import Model, Stock, Flow, Parameter, Auxiliary

def build_model():
    population = Stock("Population", initial_value=1000, unit="people")
    birth_rate = Parameter("birth_rate", value=np.random.normal(0.05, 0.01), unit="1/year")

    def births_eq(state):
        return state["parameters"]["birth_rate"].value * state["stocks"]["Population"].value

    births = Flow(
        name="Births",
        source_stock=None,
        target_stock=population,
        rate_function=births_eq,
        unit="people/year",
        inputs=["Population", "birth_rate"],
    )

    return Model(
        stocks=[population],
        flows=[births],
        parameters=[birth_rate],
        timestep=1.0,
        timestep_unit="year",
    )

# 100 runs, full time series in tidy long format
mc_results = Model.run_multiple(
    build_function=build_model,
    num_runs=100,
    duration=50,
    mode="full",          # or "start_end"
    filepath=None,
    show_progress=True,
)
```

### Table

**Purpose:**
Piecewise-linear lookup for nonlinear relationships in system-dynamics models. Linear interpolation. Flat extrapolation at bounds. Vectorized via NumPy

**Use:**
```python
# Example: flow rate as a function of a stock via a lookup
from opencld.table import Table

decay_table = Table([0, 100, 200, 400], [0, 5, 12, 25], name="DecayRate")

def outflow_rate():
    return decay_table()     # piecewise rate used by your Flow
```

### Loop and Polarity Analysis

OpenCLD can automatically build a dependency graph from your model structure and estimate **link polarity** (+/-/0)
via numerical perturbation at \(t=0\). It also detects **feedback loops** and labels them as Reinforcing (R) or
Balancing (B).

**Key methods (scalar):**
- `model.print_relationships()`
- `model.print_loops()`

**Vector models (v0.3.2):**
If your Stocks/Flows/Auxiliaries are vectors (NumPy arrays), link polarity can differ **element-by-element**.
OpenCLD exposes per-element signs and per-element loop polarity:

- `model.print_relationships_vector()`
- `model.print_loops_vector()`
- `model.get_link_polarities_vector()`
- `model.get_loops_vector()`

See `examples/04_vector_polarity.py`.


## Plotting and Visualization

### Plotting Class

The `Plotting` class provides comprehensive visualization tools for system dynamics models, including time series plots, Monte Carlo analysis, multi-variable faceting and structure graphs. All methods are `@staticmethod`. Module-level aliases mirror the class API. 

**Key Methods:**
- `plot_timeseries(data, columns=None, save_path=None)`: Create single or multi-variable time series plots
- `plot_alpha_density_lines(df, variable_name, save_path=None)`: Density-style overlay plots for Monte Carlo runs
- `plot_variable_facets(df, variable_column="variable", value_column="value", time_column="time")`: Facet grid plots for multiple variables across runs
- `plot_structure_graph(engine="native", filename=None)`: Model structure with the built-in renderer. Use `engine="graphviz"` to render via Graphviz + pydot
- `plot_results(columns=None, filename=None)`: Quick plot from `model.get_results_for_plot()`

**Notes**
- `engine="graphviz"` requires `pydot` and Graphviz (`dot` on PATH)
- Monte Carlo plotting expects a long DataFrame with columns:`time`, `variable`, `value`, `run_id` (optional `type`)

**Example 1:**
```python
from opencld import Plotting

# assume `model` is a built Model

Plotting.plot_structure_graph(
    model,
    engine="graphviz",          # or "native"
    filename="structure.svg",   # e.g., "structure.png" for native
    rankdir="LR"                # graphviz only
)

```

**Example 2:**
```python
from opencld import Model
from opencld import Plotting

# assume `build_model` returns a new randomized Model each call
mc_df = Model.run_multiple(build_model, num_runs=100, duration=50, mode="full")
Plotting.plot_alpha_density_lines(mc_df, variable_name="Prey", save_path="prey_density.png")

```


<!-- This is a hidden comment

 
### Delays

Delays represent time lags in a system. OpenCLD provides three types of delays:

#### MaterialDelay

Material delays occur when physical entities take time to move through a process. They conserve the quantity being delayed.

**Key Attributes:**
- `name`: The name of the delay
- `delay_time`: The average time it takes for material to flow through the delay
- `order`: The order of the delay (number of stages)
- `outflow`: The current outflow rate

**Key Methods:**
- `update(inflow, timestep)`: Updates the delay based on the current inflow
- `get_outflow()`: Returns the current outflow rate

#### InformationDelay

Information delays occur when information takes time to be perceived, processed, or transmitted. They smooth out fluctuations in the input signal.

**Key Attributes:**
- `name`: The name of the delay
- `delay_time`: The average time it takes for information to be processed
- `order`: The order of the delay (number of stages)
- `output`: The current output value

**Key Methods:**
- `update(input_value, timestep)`: Updates the delay based on the current input
- `get_output()`: Returns the current output value

#### FixedDelay

Fixed delays represent a precise time lag where the output exactly matches the input after a fixed time period.

**Key Attributes:**
- `name`: The name of the delay
- `delay_time`: The exact time it takes for the input to appear at the output
- `history`: A queue of past input values

**Key Methods:**
- `update(input_value, timestep)`: Updates the delay based on the current input
- `get_output()`: Returns the current output value

**Example:**
```python
# Create a material delay for a manufacturing process
production_delay = opencld.MaterialDelay(
    name="Production Delay", 
    delay_time=5.0,  # 5 time units to complete production
    initial_value=0.0, 
    order=3  # Third-order delay for more realistic behavior
)

# Update the delay with the current production rate
output_rate = production_delay.update(input_rate, timestep)
```

### Behavior Modes

Behavior modes represent common patterns of system behavior over time. OpenCLD provides implementations of these patterns:

#### ExponentialGrowth

Represents exponential growth behavior where a quantity increases at a rate proportional to its current value.

#### ExponentialDecay

Represents exponential decay behavior where a quantity decreases at a rate proportional to its current value.

#### GoalSeeking

Represents goal-seeking behavior where a quantity adjusts toward a target value over time.

#### Oscillation

Represents oscillatory behavior where a quantity fluctuates around a goal value due to delays in the system.

#### SShapedGrowth

Represents S-shaped or logistic growth where growth is initially exponential but slows as it approaches a carrying capacity.

#### OvershootAndCollapse

Represents overshoot and collapse behavior where a system exceeds its carrying capacity and then collapses.

**Example:**
```python
# Create an exponential growth model for a population
population_growth = opencld.ExponentialGrowth(
    name="Population Growth", 
    initial_value=100.0, 
    growth_rate=0.05  # 5% growth rate per time unit
)

# Update the population for one time unit
new_population = population_growth.update(1.0)
```

### Feedback Loops

Feedback loops are circular causal relationships in a system. OpenCLD provides classes to document and analyze these loops:

#### ReinforcingLoop

Reinforcing loops amplify changes in a system, creating exponential growth or collapse.

**Key Attributes:**
- `name`: The name of the feedback loop
- `components`: A list of components that form the loop
- `description`: A description of the feedback mechanism
- `polarity`: The polarity of the loop (positive for reinforcing loops)

**Key Methods:**
- `get_components()`: Returns the components that form the feedback loop

#### BalancingLoop

Balancing loops counteract changes in a system, creating goal-seeking or oscillatory behavior.

**Key Attributes:**
- `name`: The name of the feedback loop
- `components`: A list of components that form the loop
- `description`: A description of the feedback mechanism
- `polarity`: The polarity of the loop (negative for balancing loops)

**Key Methods:**
- `get_components()`: Returns the components that form the feedback loop

#### FeedbackStructure

Represents a collection of feedback loops in a system dynamics model, helping to analyze the overall feedback structure.

**Key Attributes:**
- `name`: The name of the feedback structure
- `loops`: A list of feedback loops in the structure

**Key Methods:**
- `add_loop(loop)`: Adds a feedback loop to the structure
- `get_loops()`: Returns all loops in the structure
- `get_reinforcing_loops()`: Returns only reinforcing loops
- `get_balancing_loops()`: Returns only balancing loops

**Example:**
```python
# Document a reinforcing feedback loop in a population model
population_loop = opencld.ReinforcingLoop(
    name="Population Growth Loop",
    components=[population, births],
    description="More people lead to more births, which further increases the population."
)
```

-->


## Examples

The OpenCLD package includes several example models in the `examples` directory on GITHUB:

- **Monte Carlo Analysis**: Examples of uncertainty analysis and parameter variation
- **Predator-Prey Models**: Classic ecological models with stochastic parameters
- **Inventory Models**: Business system dynamics examples
- **DHL Emission**: Computing GHG by DHL in the next years

### Complete Example: Predator-Prey Model with Plotting

```python
import numpy as np

from opencld import Model, ureg, Q_
from opencld import Stock
from opencld import Flow
from opencld import Parameter
from opencld import Auxiliary
from opencld import UnitManager
from opencld import Plotting



# --- Build a single randomized model instance (factory for Monte Carlo) ---
def build_simulation():
    simulation_timestep = 1
    simulation_unit = "day"

    # Stocks
    prey = Stock("Prey", initial_value=500, unit="animal")
    predator = Stock("Predator", initial_value=30, unit="animal")

    # Parameters (randomized each call for Monte Carlo)
    birth_rate = Parameter("birth_rate", value=np.random.normal(0.1, 0.01), unit="1/day")
    predation_rate = Parameter("predation_rate", value=np.random.normal(0.01, 0.002), unit="1/(animal*day)")
    conversion_rate = Parameter("conversion_rate", value=np.random.uniform(0.05, 0.15), unit="dimensionless")
    death_rate = Parameter("death_rate", value=0.5, unit="1/day")

    # Auxiliary: prey eaten today = predation_rate * prey * predator
    def prey_eaten_eq(state):
        prey_val = state["stocks"]["Prey"].value
        predator_val = state["stocks"]["Predator"].value
        pred_rate = state["parameters"]["predation_rate"].value
        return pred_rate * prey_val * predator_val

    prey_eaten = Auxiliary(
        "Prey Eaten Today",
        prey_eaten_eq,
        unit="animal/day",
        inputs=["Prey", "Predator", "predation_rate"]
    )

    # Flow rate functions
    def prey_births_eq(state):
        return state["parameters"]["birth_rate"].value * state["stocks"]["Prey"].value

    def prey_death_eq(state):
        return state["auxiliaries"]["Prey Eaten Today"].value

    def predator_birth_eq(state):
        return state["auxiliaries"]["Prey Eaten Today"].value * state["parameters"]["conversion_rate"].value

    def predator_death_eq(state):
        return state["parameters"]["death_rate"].value * state["stocks"]["Predator"].value

    # Flows
    prey_birth = Flow("Prey Birth", source_stock=None, target_stock=prey,
                      rate_function=prey_births_eq, unit="animal/day",
                      inputs=["Prey", "birth_rate"])
    prey_death = Flow("Prey Death", source_stock=prey, target_stock=None,
                      rate_function=prey_death_eq, unit="animal/day",
                      inputs=["Prey Eaten Today"])
    predator_birth = Flow("Predator Birth", source_stock=None, target_stock=predator,
                          rate_function=predator_birth_eq, unit="animal/day",
                          inputs=["Prey Eaten Today", "conversion_rate"])
    predator_death = Flow("Predator Death", source_stock=predator, target_stock=None,
                          rate_function=predator_death_eq, unit="animal/day",
                          inputs=["Predator", "death_rate"])

    # Assemble and return the Model
    return Model(
        stocks=[prey, predator],
        flows=[prey_birth, prey_death, predator_birth, predator_death],
        auxiliaries=[prey_eaten],
        parameters=[birth_rate, predation_rate, conversion_rate, death_rate],
        timestep=simulation_timestep,
        timestep_unit=simulation_unit
    )


# --- Monte Carlo run and export ---
# Runs 3 stochastic realizations for 10 time units, returns long-form DataFrame, and writes CSV.
df = Model.run_multiple(
    build_simulation,
    num_runs=3,
    duration=10,
    mode="full",
    filepath="predator_multi_run_output.csv"
)

# Density-style overlay for the "Prey" variable across runs. Saves a PNG.
Plotting.plot_alpha_density_lines(df, variable_name="Prey", save_path="prey_density_plot.png")

# --- Structure graph plotting ---
# Build a single concrete model instance and render its structure using Graphviz+pydot.
m = build_simulation()
Plotting.plot_structure_graph(
    m,
    engine="graphviz",                      # use "native" to draw with networkx/matplotlib
    filename="predator_non_determinist_diagram.png"
)

```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
