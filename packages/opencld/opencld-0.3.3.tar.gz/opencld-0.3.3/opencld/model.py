import pandas as pd
import networkx as nx
import copy
from tqdm import trange
from .units import ureg, Q_, get_quantity
from time import time
import numpy as np

# Module-level pint helpers for convenience
Q_ = ureg.Quantity

# A small, fixed constant for numerical perturbation
DEFAULT_EPSILON = 0 #1e-9

from .multi_simulation import run_simulation_multiple as _run_multiple

class Model:
    """
    The main engine for building, running, and analyzing a system dynamics model.
    """
    # Class-level verbosity control (set to False to suppress validation messages)
    _verbose = True
    
    # Supported integration methods
    INTEGRATION_METHODS = ('euler', 'rk4')
    
    def __init__(self, stocks, flows, auxiliaries=None, parameters=None, timestep=1.0, timestep_unit='day', integration_method='euler'):
        """
        Initializes a new simulation.

        :param stocks: A list of Stock objects.
        :param flows: A list of Flow objects.
        :param auxiliaries: An optional list of Auxiliary objects.
        :param parameters: An optional list of Parameter objects.
        :param timestep: The numerical value for the simulation time step (dt).
        :param timestep_unit: The unit of time for the simulation (e.g., 'day', 'year').
        :param integration_method: Integration method to use ('euler' or 'rk4'). Default is 'euler'.
        """
        # --- 0. Validate and Store Integration Method ---
        if integration_method not in self.INTEGRATION_METHODS:
            raise ValueError(f"Unknown integration method '{integration_method}'. Supported: {self.INTEGRATION_METHODS}")
        self.integration_method = integration_method
        # --- 1. Store Model Components ---
        # Components are stored in dictionaries for quick, by-name lookup.
        self.stocks = {s.name: s for s in stocks}
        self.flows = {f.name: f for f in flows}
        self.auxiliaries = {a.name: a for a in auxiliaries} if auxiliaries else {}
        self.parameters = {p.name: p for p in parameters} if parameters else {}

        # --- 2. Simulation State Initialization ---
        self.timestep = get_quantity(timestep, timestep_unit)
        self.time = 0.0 * self.timestep.units # Start time at 0 with correct units
        self.history = [] # Will store a record for each timestep

        # --- 3. Analysis and Configuration Attributes ---
        self.loops = []
        # Vector-aware polarity data (optional, populated when outputs are vector-valued)
        self.loops_vector = None  # Dict[index_tuple, list[(label, loop_str)]]
        self._dependency_graph = None
        self._link_polarities = {}
        self._link_polarities_vector = {}  # Dict[(u,v), np.ndarray[int]] for per-element link signs
        self.ureg = ureg # Expose the unit registry instance for potential external use
        self.epsilon_for_perturbation = DEFAULT_EPSILON
        self.numeric_threshold = 1e-12 # A small number to treat changes smaller than this as zero

        # --- 4. Model Setup and Validation ---
        # Determine the correct calculation order for auxiliaries to respect dependencies.
        self._sorted_auxiliary_names = self._get_auxiliary_calculation_order()
        # Perform initial checks to ensure the model is runnable and units are consistent.
        self.validate_model()

        # --- 5. Initial State Calculation (for t=0) ---
        # This block calculates the state at t=0 and records it as the first
        # entry in the history. It's also used as the baseline for polarity analysis.
        self.initial_state_values = {}
        initial_system_state_for_polarity = None
        try:
            temp_state = self._get_system_state(get_objects=True)
            # Calculate initial values for all dynamic components
            for aux_name in self._sorted_auxiliary_names:
                aux = self.auxiliaries[aux_name]
                self.initial_state_values[aux.name] = aux.calculate_value(temp_state)
            for flow in self.flows.values():
                self.initial_state_values[flow.name] = flow.calculate_rate(temp_state)
            for stock in self.stocks.values():
                self.initial_state_values[stock.name] = stock.value

            # Capture the full state with object references for polarity analysis
            initial_system_state_for_polarity = self._get_system_state(get_objects=True)
            
            # Record this pristine t=0 state as the first data point.
            self._record_state(record_time=self.time) # Pass time explicitly for clarity

        except Exception as e:
            print(f"[WARN] Initial state calculation failed: {e}")
            self.initial_state_values = None # Flag that initial state is unknown

        # --- 6. Structural Analysis (Loops and Polarities) ---
        try:
            if self.initial_state_values and initial_system_state_for_polarity and nx:
                self._dependency_graph = self._find_loops_and_polarity(initial_system_state_for_polarity)
            elif nx is None:
                self.loops.append(("?", "Loop detection skipped: networkx library not found."))
            else:
                self.loops.append(("?", "Polarity detection skipped: initial state calculation failed."))
        except Exception as e:
            print(f"\n[WARN] Failed during automatic loop/polarity detection: {e}")
            self.loops.append(("Error", f"Error during loop detection: {e}"))

    # ------------------------------------------------------------------------------------
    # --- Core Simulation Logic ---
    # ------------------------------------------------------------------------------------

    def _get_system_state(self, get_objects=False):
        """
        Gathers the current state of the simulation into a dictionary.

        :param get_objects: If True, returns a dictionary of the actual component objects.
                            If False, returns a dictionary of their scalar values.
        :return: A dictionary representing the system's current state.
        """
        if get_objects:
            # This version is passed to calculation functions, giving them access to component objects.
            return {
                'stocks': self.stocks,
                'flows': self.flows,
                'auxiliaries': self.auxiliaries,
                'parameters': self.parameters,
                'time': self.time,
                'timestep': self.timestep 
            }
        else:
            # This version is for history recording, capturing the values at a moment in time.
            return {
                'stocks': {s.name: s.value for s in self.stocks.values()},
                'flows': {f.name: f.rate for f in self.flows.values()},
                'auxiliaries': {a.name: a.value for a in self.auxiliaries.values()},
                'parameters': {p.name: p.value for p in self.parameters.values()},
                'time': self.time
            }

    def _record_state(self, record_time):
        """Appends the current state of all components to the history log."""
        self.history.append({
            'time': record_time,
            'stocks': {s.name: s.value for s in self.stocks.values()},
            'flows': {f.name: f.rate for f in self.flows.values()},
            'auxiliaries': {a.name: a.value for a in self.auxiliaries.values()},
            'parameters': {p.name: p.value for p in self.parameters.values()}
        })

    def _update_auxiliaries_and_flows(self, state_to_update, perturbed_input_name=None):
        """
        Helper for polarity analysis. Recalculates all auxiliaries and flows for a given state,
        optionally skipping the recalculation of the variable that was directly perturbed.
        """
        for aux_name in self._sorted_auxiliary_names:
            if aux_name == perturbed_input_name:
                continue # Skip recalculation for the perturbed input itself
            if aux_name in state_to_update['auxiliaries']:
                state_to_update['auxiliaries'][aux_name].calculate_value(state_to_update)

        for flow_name in self.flows.keys():
            if flow_name == perturbed_input_name:
                continue # Skip recalculation for the perturbed input itself
            if flow_name in state_to_update['flows']:
                state_to_update['flows'][flow_name].calculate_rate(state_to_update)

    def step(self):
        """Executes a single time step of the simulation using the configured integration method."""
        if self.integration_method == 'euler':
            self._step_euler()
        elif self.integration_method == 'rk4':
            self._step_rk4()
        
        # Increment simulation time to the end of the interval.
        self.time += self.timestep
        
        # Record the new state at the new time (t + dt).
        self._record_state(record_time=self.time)

    def _step_euler(self):
        """Executes a single Euler integration step."""
        # Get the state at the beginning of the interval (time t)
        state = self._get_system_state(get_objects=True)
        
        # Calculate all auxiliary and flow values based on the state at time t.
        for aux_name in self._sorted_auxiliary_names:
            self.auxiliaries[aux_name].calculate_value(state)
        for flow in self.flows.values():
            flow.calculate_rate(state)
            
        # Update all stocks using the flow rates calculated at time t.
        for stock in self.stocks.values():
            stock.update(self.timestep)

    def _step_rk4(self):
        """
        Executes a single RK4 (Runge-Kutta 4th order) integration step.
        
        RK4 formula:
        y(t+dt) = y(t) + (k1 + 2*k2 + 2*k3 + k4) * dt / 6
        
        where:
        k1 = f(t, y)
        k2 = f(t + dt/2, y + k1*dt/2)
        k3 = f(t + dt/2, y + k2*dt/2)
        k4 = f(t + dt, y + k3*dt)
        """
        dt = self.timestep
        half_dt = dt / 2
        
        # Save the original stock values
        original_values = {name: stock.value.copy() for name, stock in self.stocks.items()}
        original_time = self.time
        
        # --- k1: Evaluate at current state (t, y) ---
        state = self._get_system_state(get_objects=True)
        for aux_name in self._sorted_auxiliary_names:
            self.auxiliaries[aux_name].calculate_value(state)
        for flow in self.flows.values():
            flow.calculate_rate(state)
        
        # Store k1 (net flow rates at t)
        k1 = self._get_net_flows()
        
        # --- k2: Evaluate at (t + dt/2, y + k1*dt/2) ---
        self.time = original_time + half_dt
        for name, stock in self.stocks.items():
            stock.value = original_values[name] + k1[name] * half_dt
        
        state = self._get_system_state(get_objects=True)
        for aux_name in self._sorted_auxiliary_names:
            self.auxiliaries[aux_name].calculate_value(state)
        for flow in self.flows.values():
            flow.calculate_rate(state)
        
        k2 = self._get_net_flows()
        
        # --- k3: Evaluate at (t + dt/2, y + k2*dt/2) ---
        for name, stock in self.stocks.items():
            stock.value = original_values[name] + k2[name] * half_dt
        
        state = self._get_system_state(get_objects=True)
        for aux_name in self._sorted_auxiliary_names:
            self.auxiliaries[aux_name].calculate_value(state)
        for flow in self.flows.values():
            flow.calculate_rate(state)
        
        k3 = self._get_net_flows()
        
        # --- k4: Evaluate at (t + dt, y + k3*dt) ---
        self.time = original_time + dt
        for name, stock in self.stocks.items():
            stock.value = original_values[name] + k3[name] * dt
        
        state = self._get_system_state(get_objects=True)
        for aux_name in self._sorted_auxiliary_names:
            self.auxiliaries[aux_name].calculate_value(state)
        for flow in self.flows.values():
            flow.calculate_rate(state)
        
        k4 = self._get_net_flows()
        
        # --- Final update: y(t+dt) = y(t) + (k1 + 2*k2 + 2*k3 + k4) * dt / 6 ---
        self.time = original_time  # Will be incremented by step()
        for name, stock in self.stocks.items():
            weighted_slope = (k1[name] + 2*k2[name] + 2*k3[name] + k4[name]) / 6
            stock.value = original_values[name] + weighted_slope * dt

    def _get_net_flows(self):
        """
        Calculates the net flow (derivative) for each stock based on current flow rates.
        Returns a dictionary of {stock_name: net_flow_rate}.
        """
        net_flows = {}
        for name, stock in self.stocks.items():
            # Initialize net_flow with correct shape and units
            net_flow_unit = stock.unit / self.timestep.units
            net_flow = Q_(np.zeros(stock.value.shape), net_flow_unit)
            
            for inflow in stock.inflows:
                net_flow = net_flow + inflow.rate
            for outflow in stock.outflows:
                net_flow = net_flow - outflow.rate
            
            net_flows[name] = net_flow
        return net_flows

    def run(self, duration, show_progress=True):
        """
        Runs the simulation for a specified duration, ensuring the t=0 state is recorded
        and the simulation progresses correctly.
        """
        # --- 1. SETUP ---
        duration_qty = duration if hasattr(duration, 'units') else Q_(duration, str(self.timestep.units))
        if duration_qty.dimensionality != self.timestep.dimensionality:
            raise ValueError(f"Duration unit {duration_qty.units} is incompatible with {self.timestep.units}.")
        
        steps = int((duration_qty / self.timestep).to_base_units().magnitude)

        # --- 2. RESET STATE ---
        for stock in self.stocks.values():
            stock.value = stock.initial_value.copy() # Use a copy to avoid mutation
        self.time = 0.0 * self.timestep.units
        self.history = []
        
        # --- 3. CALCULATE & RECORD INITIAL STATE (t=0) ---
        # This is crucial: calculate the initial flows and aux values before the first step
        initial_state = self._get_system_state(get_objects=True)
        for aux_name in self._sorted_auxiliary_names:
            self.auxiliaries[aux_name].calculate_value(initial_state)
        for flow in self.flows.values():
            flow.calculate_rate(initial_state)
        self._record_state(record_time=self.time)

        # --- 4. RUN SIMULATION LOOP ---
        iterator = trange(steps, desc="Running simulation") if show_progress else range(steps)
        for _ in iterator:
            self.step() # This will now correctly calculate from t=1 onwards

        self.results = self.get_results()
        return self.results


    # ------------------------------------------------------------------------------------
    # --- Data Retrieval and Formatting ---
    # ------------------------------------------------------------------------------------

    def get_results(self, strip_units=False):
        """
        Processes the simulation history into a wide-format pandas DataFrame.

        :param strip_units: If True, converts all pint.Quantity values to their
                            scalar magnitudes for easier plotting. Defaults to False.
        :return: pandas.DataFrame
        """
        if not self.history:
            return pd.DataFrame()

        flat_history = []
        for record in self.history:
            flat_record = {'time': record['time']}
            for category in ['stocks', 'flows', 'auxiliaries', 'parameters']:
                if category in record:
                    flat_record.update(record[category])
            flat_history.append(flat_record)
        
        df = pd.DataFrame(flat_history) # DO NOT set index yet

        if not strip_units:
            return df.set_index('time') # Set index at the end
        else:
            # --- UNIT STRIPPING ---
            # Create a new DataFrame to hold scalar values
            df_numeric = pd.DataFrame()
            for col in df.columns:
                # Check the first valid element to see if it's a Quantity
                first_valid_idx = df[col].first_valid_index()
                if first_valid_idx is not None and hasattr(df.loc[first_valid_idx, col], 'magnitude'):
                    # If it is, apply .magnitude to the whole series
                    df_numeric[col] = df[col].apply(lambda x: x.magnitude if hasattr(x, 'magnitude') else x)
                else:
                    # Otherwise, the column is already numeric/scalar, so just copy it
                    df_numeric[col] = df[col]
            
            return df_numeric.set_index('time')

    def get_results_for_plot(self):
        """Convenience method to get simulation results with units stripped."""
        return self.get_results(strip_units=True)

    def to_df(self, filepath: str = None, mode: str = "numeric", run_id: int = 1):
        """
        Converts simulation results into a tidy, long-format DataFrame, and optionally saves to CSV.

        :param filepath: If provided, writes the DataFrame to this CSV file path.
        :param mode: "with_unit" to keep pint.Quantity objects, "numeric" to use scalar magnitudes.
        :param run_id: An identifier for this simulation run, added as a column.
        :return: pandas.DataFrame in long format (time, run_id, variable, value, type).
        """
        # 1. Grab the wide-format results in the desired mode
        strip = (mode != "with_unit")
        wide_df = self.get_results(strip_units=strip)

        # 2. Melt into long format
        long_df = wide_df.reset_index().melt(
            id_vars="time",
            var_name="variable",
            value_name="value"
        )
        long_df["run_id"] = run_id

        # 3. Infer component type for each variable
        type_map = {
            **{n: "stock" for n in self.stocks},
            **{n: "flow" for n in self.flows},
            **{n: "auxiliary" for n in self.auxiliaries},
            **{n: "parameter" for n in self.parameters}
        }
        long_df["type"] = long_df["variable"].map(type_map)

        # 4. Reorder columns and optionally save
        long_df = long_df[["time", "run_id", "variable", "value", "type"]]
        if filepath:
            if mode == "with_unit":
                print("[WARN] Saving DataFrame with pint.Quantity objects to CSV. "
                      "Values will be converted to strings. Use mode='numeric' for a standard CSV.")
            long_df.to_csv(filepath, index=False)
        return long_df
    
    # ------------------------------------------------------------------------------------
    # --- Model Validation ---
    # ------------------------------------------------------------------------------------

    def validate_model(self):
        """Performs pre-run checks for unit consistency and calculability."""
        if Model._verbose:
            print("[INFO] Validating model...")
        try:
            self.check_units()
            self.validate_influences()
            if Model._verbose:
                print("[INFO] Model validation passed.")
        except Exception as e:
            print(f"[ERROR] Model validation failed: {e}")
            raise # Re-raise to prevent simulation of an invalid model

    def check_units(self):
        """Checks for missing units and dimensional consistency between flows and stocks."""
        errors = []
        # Check for missing units
        for category, components in [("Stock", self.stocks), ("Flow", self.flows), 
                                     ("Auxiliary", self.auxiliaries), ("Parameter", self.parameters)]:
            for name, comp in components.items():
                if getattr(comp, 'unit', None) is None:
                    errors.append(f"{category} '{name}' is missing a unit.")
        
        # Check for flow-stock consistency
        sim_time_unit = self.timestep.units
        for flow in self.flows.values():
            stock_to_check = flow.source_stock or flow.target_stock
            if stock_to_check and stock_to_check.unit and flow.unit:
                expected_dim = stock_to_check.unit.dimensionality / sim_time_unit.dimensionality
                if flow.unit.dimensionality != expected_dim:
                    errors.append(
                        f"Flow '{flow.name}' unit '{flow.unit}' is inconsistent with stock '{stock_to_check.name}' "
                        f"({stock_to_check.unit}) over time [{sim_time_unit}]."
                    )
        if errors:
            raise ValueError("Unit check failed:\n- " + "\n- ".join(errors))

    def validate_influences(self):
        """Ensures all components can be calculated once with initial values."""
        state = self._get_system_state(get_objects=True)
        for aux_name in self._sorted_auxiliary_names:
            self.auxiliaries[aux_name].calculate_value(state)
        for flow in self.flows.values():
            flow.calculate_rate(state)

    # ------------------------------------------------------------------------------------
    # --- Structural Analysis (Loops & Polarities) ---
    # ------------------------------------------------------------------------------------

    def _get_auxiliary_calculation_order(self):
        """Determines the correct calculation order for auxiliaries using topological sort."""
        if not self.auxiliaries:
            return []

        aux_graph = nx.DiGraph(
            (inp, aux.name)
            for aux in self.auxiliaries.values()
            for inp in aux.inputs
            if inp in self.auxiliaries
        )
        aux_graph.add_nodes_from(self.auxiliaries.keys()) # Ensure all aux are nodes

        try:
            return list(nx.topological_sort(aux_graph))
        except nx.NetworkXUnfeasible as e:
            cycles = list(nx.simple_cycles(aux_graph))
            cycle_str = "; ".join([" -> ".join(c + [c[0]]) for c in cycles])
            raise ValueError(f"Cyclic dependency detected among auxiliaries: {cycle_str}") from e

    def _find_loops_and_polarity(self, base_state_for_estimation):
        """Builds the model's dependency graph, finds loops, and determines their polarity."""
        # 1. Build the dependency graph from component 'inputs' lists
        G = nx.DiGraph()
        all_calculable = {**self.flows, **self.auxiliaries}
        for comp in all_calculable.values():
            for inp in comp.inputs:
                G.add_edge(inp, comp.name)
        for flow in self.flows.values():
            if flow.target_stock:
                G.add_edge(flow.name, flow.target_stock.name)
            if flow.source_stock:
                G.add_edge(flow.name, flow.source_stock.name)
        
        # 2. Estimate the polarity of each link in the graph
        self._link_polarities = {}
        self._link_polarities_vector = {}
        for u, v in G.edges():
            scalar_sign, vector_sign = self._estimate_link_signs(u, v, base_state_for_estimation)
            self._link_polarities[(u, v)] = scalar_sign
            G.edges[u, v]['sign'] = scalar_sign
            if vector_sign is not None:
                self._link_polarities_vector[(u, v)] = vector_sign

        # 3. Find all simple cycles (loops) in the graph
        cycles = list(nx.simple_cycles(G))
        self.loops = []
        for cycle in cycles:
            # 4. Determine loop polarity by multiplying the signs of its links
            polarity = 1
            is_valid_loop = True
            for i in range(len(cycle)):
                u, v = cycle[i], cycle[(i + 1) % len(cycle)]
                sign = G.edges[u, v].get('sign', 0)
                if sign in [None, '?']:
                    is_valid_loop = False
                    break
                polarity *= sign
            
            # 5. Label the loop as Reinforcing (R), Balancing (B), or Neutral (N)
            label = 'R (+)' if polarity > 0 else 'B (-)' if polarity < 0 else 'N (0)'
            self.loops.append(
                (label if is_valid_loop else '?', ' -> '.join(cycle + [cycle[0]]))
            )

        # 6. Optional: vector-aware loop polarity (one polarity per element index)
        self.loops_vector = self._calculate_vector_loops(cycles, G)
        return G

    def get_loops(self):
        """Returns the list of detected feedback loops."""
        return self.loops

    def get_link_polarities(self):
        """Returns the dictionary of calculated link polarities."""
        return self._link_polarities

    def get_link_polarities_vector(self):
        """
        Returns per-element link polarities for vector-valued influences.

        The returned dict maps (u, v) -> numpy.ndarray of ints in {-1, 0, +1}.
        Edges that are purely scalar (or where vector polarity cannot be inferred)
        will not appear in this dictionary.
        """
        return self._link_polarities_vector

    def get_loops_vector(self):
        """
        Returns detected feedback loops grouped by element index for vector models.

        Returns
        -------
        dict[tuple, list[tuple[str, str]]] | None
            Mapping from an element index (e.g. (0,), (1,)) to a list of
            (label, loop_string). None if vector loop polarity is not available.
        """
        return self.loops_vector
    
    # ------------------------------------------------------------------------------------
    # --- Polarity Perturbation Engine (Internal Helpers) ---
    # ------------------------------------------------------------------------------------

    def _get_var_value_from_state(self, state, var_name):
        """Retrieves a variable's value/rate from a state dictionary."""
        if var_name == 'time': return state.get('time') # FIX: Handle time variable
        if var_name in state['stocks']: return state['stocks'][var_name].value
        if var_name in state['auxiliaries']: return state['auxiliaries'][var_name].value
        if var_name in state['parameters']: return state['parameters'][var_name].value
        if var_name in state['flows']: return state['flows'][var_name].rate
        print(f"[WARN] Variable '{var_name}' not found in state.")
        return None

    def _set_var_value_in_state(self, state, var_name, new_value):
        """Sets a variable's value/rate in a state dictionary (for perturbation)."""
        if var_name in state['stocks']: state['stocks'][var_name].value = new_value
        elif var_name in state['auxiliaries']: state['auxiliaries'][var_name].value = new_value
        elif var_name in state['parameters']: state['parameters'][var_name].value = new_value
        elif var_name in state['flows']: state['flows'][var_name].rate = new_value
        else: print(f"[WARN] Variable '{var_name}' not found in state to set value.")

    def _estimate_link_signs(self, input_var_name, output_var_name, base_state):
        """
        Estimates a link's polarity via relative numerical perturbation.

        Returns
        -------
        (scalar_sign, vector_sign)
            - scalar_sign: int in {-1, 0, +1} (backwards-compatible aggregation)
            - vector_sign: np.ndarray[int] or None (per-element signs when output is vector-valued)
        """
        # 1. Definitional polarity for Flow -> Stock
        if input_var_name in self.flows and output_var_name in self.stocks:
            flow_obj = self.flows[input_var_name]
            if flow_obj.target_stock and flow_obj.target_stock.name == output_var_name:
                scalar = 1
            elif flow_obj.source_stock and flow_obj.source_stock.name == output_var_name:
                scalar = -1
            else:
                scalar = 0

            # If the stock is vector-valued, replicate the definitional sign per element.
            out_val = self._get_var_value_from_state(base_state, output_var_name)
            try:
                out_mag = np.asarray(out_val.magnitude) if out_val is not None else None
                if out_mag is not None and out_mag.shape != ():
                    return scalar, np.full(out_mag.shape, scalar, dtype=int)
            except Exception:
                pass
            return scalar, None

        # 2. Perturbation setup
        original_input_value = self._get_var_value_from_state(base_state, input_var_name)
        if original_input_value is None or not hasattr(original_input_value, 'magnitude'):
            return 0, None

        # Use a relative perturbation
        if np.all(original_input_value.magnitude == 0):
            perturbation_delta = Q_(self.epsilon_for_perturbation, original_input_value.units)
        else:
            perturbation_delta = original_input_value * 0.001 # 0.1% relative change
        
        if np.all(np.abs(perturbation_delta.magnitude) < self.numeric_threshold):
             perturbation_delta = Q_(self.epsilon_for_perturbation, original_input_value.units)

        # 3. Positive Perturbation
        state_plus = copy.deepcopy(base_state)
        self._set_var_value_in_state(state_plus, input_var_name, original_input_value + perturbation_delta)
        self._update_auxiliaries_and_flows(state_plus, perturbed_input_name=input_var_name)
        output_plus = self._get_var_value_from_state(state_plus, output_var_name)

        # 4. Negative Perturbation
        state_minus = copy.deepcopy(base_state)
        self._set_var_value_in_state(state_minus, input_var_name, original_input_value - perturbation_delta)
        self._update_auxiliaries_and_flows(state_minus, perturbed_input_name=input_var_name)
        output_minus = self._get_var_value_from_state(state_minus, output_var_name)
        
        # 5. Determine sign
        if output_plus is None or output_minus is None:
            return 0, None

        delta_output = np.asarray(output_plus.magnitude) - np.asarray(output_minus.magnitude)

        # Vector sign (per-element), only when the output is vector-valued
        vector_sign = None
        if delta_output.shape != ():
            vector_sign = np.where(
                np.abs(delta_output) < self.numeric_threshold,
                0,
                np.sign(delta_output),
            ).astype(int)

        # Backwards-compatible scalar sign: aggregate vector change into one number
        total_change = float(np.sum(delta_output))
        if abs(total_change) < self.numeric_threshold:
            return 0, vector_sign
        return (1 if total_change > 0 else -1), vector_sign

    def _calculate_vector_loops(self, cycles, G):
        """
        Calculates loop polarities per element index when vector link polarities are available.

        Returns
        -------
        dict[tuple, list[tuple[str, str]]] | None
        """
        if not cycles:
            return None

        if not self._link_polarities_vector:
            return None

        # Determine the reference shape from the first vector edge we have.
        try:
            first_vec = next(iter(self._link_polarities_vector.values()))
            ref_shape = np.asarray(first_vec).shape
            if ref_shape == ():
                return None
        except Exception:
            return None

        loops_by_index = {idx: [] for idx in np.ndindex(ref_shape)}

        for cycle in cycles:
            loop_str = ' -> '.join(cycle + [cycle[0]])

            # Start with +1 for all indices
            vec_polarity = np.ones(ref_shape, dtype=int)
            is_valid = True

            for i in range(len(cycle)):
                u, v = cycle[i], cycle[(i + 1) % len(cycle)]
                sign_vec = self._link_polarities_vector.get((u, v))

                if sign_vec is None:
                    # Fall back to scalar sign and broadcast it
                    scalar = G.edges[u, v].get('sign', 0)
                    if scalar in [None, '?']:
                        is_valid = False
                        break
                    sign_vec = scalar

                # Multiply (broadcasting scalars over arrays)
                try:
                    vec_polarity = vec_polarity * sign_vec
                except Exception:
                    is_valid = False
                    break

            if not is_valid:
                for idx in loops_by_index:
                    loops_by_index[idx].append(('?', loop_str))
                continue

            # Assign per-index labels
            for idx in loops_by_index:
                p = int(vec_polarity[idx])
                label = 'R (+)' if p > 0 else 'B (-)' if p < 0 else 'N (0)'
                loops_by_index[idx].append((label, loop_str))

        return loops_by_index

    # ------------------------------------------------------------------------------------
    # --- Data Access Methods (plotting moved to PlottingToolkit) ---
    # ------------------------------------------------------------------------------------

    def print_loops(self):
        """Formats and prints the detected feedback loops grouped by polarity."""
        print("\n--- Detected Feedback Loops (Polarity @ t=0) ---")
        detected_loops = self.get_loops()
        if not detected_loops:
            print("  No feedback loops were detected.")
            return

        # Group loops by polarity
        grouped_loops = {'R (+)': [], 'B (-)': [], 'N (0)': [], '?': []}
        for polarity, loop_str in detected_loops:
            grouped_loops.get(polarity, grouped_loops['?']).append(loop_str)

        def print_loop_group(title, loops_list):
            print(f"\n  {title}:")
            if not loops_list:
                print("    None found.")
            else:
                for i, loop_str in enumerate(sorted(loops_list)):
                    print(f"    {i+1}. {loop_str}")

        print_loop_group("Reinforcing Loops (+)", grouped_loops['R (+)'])
        print_loop_group("Balancing Loops (-)", grouped_loops['B (-)'])
        print_loop_group("Neutral Loops (0 @ t=0)", grouped_loops['N (0)'])
        print_loop_group("Ambiguous Loops (?)", grouped_loops['?'])
        print("----------------------------------------------------")

    def print_relationships(self):
        """Formats and prints all model relationships and their calculated polarities."""
        print("\n--- Model Relationships and Link Polarities (@ t=0) ---")
        all_polarities = self.get_link_polarities()
        if not all_polarities:
            print("  Could not retrieve link polarities.")
            return

        link_outputs = []
        for (u, v), sign in all_polarities.items():
            symbol = {1: '+', -1: '-', 0: '0'}.get(sign, '?')
            source_type = "(P)" if u in self.parameters else ""
            link_outputs.append(f"  {u:<30s} {source_type:>3s} -> {v:<30s} : ({symbol})")
        
        if not link_outputs:
            print("  No relationships found.")
        else:
            print("\n".join(sorted(link_outputs)))
        print("\n  Note: Polarity (+,-,0,?) calculated via numerical perturbation at t=0.")
        print("----------------------------------------------------")

    def print_relationships_vector(self, diff_only: bool = False, include_scalar: bool = False):
        """
        Prints per-element link polarities for vector-valued influences (@ t=0).

        Parameters
        ----------
        diff_only : bool
            If True, only prints edges where the vector sign is not uniform across elements
            or disagrees with the scalar (aggregated) sign.
        include_scalar : bool
            If True, also prints the scalar (aggregated) sign for comparison.
        """
        print("\n--- Model Relationships and Link Polarities (Vector @ t=0) ---")
        vec = self.get_link_polarities_vector()
        if not vec:
            print("  No vector link polarities available (model may be fully scalar).")
            return

        symbols = {1: '+', -1: '-', 0: '0'}

        def fmt(arr) -> str:
            a = np.asarray(arr).astype(int)
            return np.array2string(
                a,
                separator=", ",
                formatter={"all": lambda x: symbols.get(int(x), "?")},
            )

        lines = []
        for (u, v), sign_arr in vec.items():
            a = np.asarray(sign_arr).astype(int)
            scalar = self._link_polarities.get((u, v))

            is_uniform = (a.size > 0) and bool(np.all(a == a.flat[0]))
            uniform_val = int(a.flat[0]) if is_uniform else None
            scalar_agrees = (scalar is not None) and is_uniform and (int(scalar) == uniform_val)

            if diff_only and scalar_agrees:
                continue

            source_type = "(P)" if u in self.parameters else ""
            vec_str = fmt(a)
            if include_scalar:
                scalar_symbol = symbols.get(int(scalar), "?") if scalar is not None else "?"
                lines.append(
                    f"  {u:<30s} {source_type:>3s} -> {v:<30s} : scalar=({scalar_symbol}) vector={vec_str}"
                )
            else:
                lines.append(f"  {u:<30s} {source_type:>3s} -> {v:<30s} : {vec_str}")

        if not lines:
            print("  (All vector edge signs are uniform and match the scalar sign.)")
        else:
            print("\n".join(sorted(lines)))
        print("\n  Note: Vector sign is computed per element (numerical perturbation at t=0).")
        print("----------------------------------------------------")

    def print_loops_vector(self, compact: bool = False):
        """
        Prints detected feedback loops for vector models (@ t=0).

        Parameters
        ----------
        compact : bool
            If True, prints each loop once and lists which element indices are R/B/N.
            If False (default), prints loops grouped under each element index.
        """
        print("\n--- Detected Feedback Loops (Vector Polarity @ t=0) ---")
        loops_by_idx = self.get_loops_vector()
        if not loops_by_idx:
            print("  No vector loop polarity available (model may be fully scalar).")
            return

        if compact:
            # loop_str -> label -> set(indices)
            loop_map = {}
            for idx, entries in loops_by_idx.items():
                for label, loop_str in entries:
                    loop_map.setdefault(loop_str, {}).setdefault(label, set()).add(idx)

            for loop_str in sorted(loop_map.keys()):
                print(f"\n  {loop_str}:")
                for label in ("R (+)", "B (-)", "N (0)", "?"):
                    idxs = sorted(loop_map[loop_str].get(label, set()))
                    if idxs:
                        idxs_str = ", ".join(str(i) for i in idxs)
                        print(f"    {label}: {idxs_str}")
            print("----------------------------------------------------")
            return

        # Verbose (per-element) view
        for idx in sorted(loops_by_idx.keys()):
            print(f"\n  Element {idx}:")
            grouped = {'R (+)': [], 'B (-)': [], 'N (0)': [], '?': []}
            for label, loop_str in loops_by_idx[idx]:
                grouped.get(label, grouped['?']).append(loop_str)

            def print_group(title, items):
                print(f"    {title}:")
                if not items:
                    print("      None found.")
                else:
                    for i, s in enumerate(sorted(set(items))):
                        print(f"      {i+1}. {s}")

            print_group("Reinforcing Loops (+)", grouped['R (+)'])
            print_group("Balancing Loops (-)", grouped['B (-)'])
            print_group("Neutral Loops (0 @ t=0)", grouped['N (0)'])
            print_group("Ambiguous Loops (?)", grouped['?'])
        print("----------------------------------------------------")



    @staticmethod
    def run_multiple(build_function, num_runs, duration, mode="full", filepath=None, show_progress=True, verbose=False):
        return _run_multiple(build_function, num_runs, duration, mode=mode, filepath=filepath, show_progress=show_progress, verbose=verbose)
