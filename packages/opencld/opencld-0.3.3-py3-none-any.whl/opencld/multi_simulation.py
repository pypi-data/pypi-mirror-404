import pandas as pd
from time import time

def run_simulation_multiple(build_function, num_runs, duration, mode="full", filepath=None, show_progress=True, verbose=False):
    """
    Run multiple stochastic simulations using a user-defined model builder function.

    Parameters:
        build_function (callable): A function that takes no arguments and returns a fresh,
                                 compiled Simulation instance.
        num_runs (int): Number of runs to simulate.
        duration (float or Quantity): Duration of each simulation.
        mode (str): 'full' for full time series, 'start_end' for only first/last timestep.
        filepath (str or None): If provided, saves the result to a CSV at this path.
        show_progress (bool): If True, displays a progress bar for the runs.
        verbose (bool): If False (default), suppresses per-model validation messages.

    Returns:
        pd.DataFrame: Results from all runs in a tidy, long format.
    """
    # Import here to avoid circular imports
    from .model import Model
    
    # Suppress verbose model validation messages during multi-run
    original_verbose = Model._verbose
    Model._verbose = verbose
    
    all_records = []

    if verbose:
        print(f"[INFO] Running {num_runs} simulations...")
    start_time = time()

    # Create a simple iterator or a tqdm progress bar
    iterator = range(1, num_runs + 1)
    if show_progress:
        try:
            from tqdm import trange
            iterator = trange(1, num_runs + 1, desc="Running simulations")
        except ImportError:
            print("[INFO] Tqdm not found, progress bar will not be shown. Install with 'pip install tqdm'.")

    for run_id in iterator:
        # Get a new, fresh simulation instance for each run
        sim = build_function()
        
        # Run the simulation without its own internal progress bar
        sim.run(duration, show_progress=False)

        # Use the 'to_df' method to get results in the correct format
        # Use the 'numeric' mode which is equivalent to get_results_for_plot()
        df_long = sim.to_df(mode="numeric", run_id=run_id)

        if mode == 'full':
            all_records.append(df_long)

        elif mode == 'start_end':
            # Filter the long df to get start and end values
            t_min = df_long['time'].min()
            t_max = df_long['time'].max()
            
            start_df = df_long[df_long['time'] == t_min].copy()
            start_df.rename(columns={'value': 'start_value'}, inplace=True)
            
            end_df = df_long[df_long['time'] == t_max].copy()
            end_df.rename(columns={'value': 'end_value'}, inplace=True)
            
            # Merge start and end dataframes
            summary = pd.merge(
                start_df[['run_id', 'variable', 'type', 'start_value']],
                end_df[['run_id', 'variable', 'end_value']],
                on=['run_id', 'variable']
            )
            all_records.append(summary)
            
        else:
            raise ValueError(f"[run_simulation_multiple] Unsupported mode: {mode!r}. Use 'full' or 'start_end'.")

    elapsed = time() - start_time
    
    # Restore original verbosity setting
    Model._verbose = original_verbose
    
    if verbose:
        print(f"[INFO] All {num_runs} simulations completed in {elapsed:.2f} seconds.")

    if not all_records:
        return pd.DataFrame()

    result_df = pd.concat(all_records, ignore_index=True)

    if filepath:
        result_df.to_csv(filepath, index=False)
        print(f"[INFO] Exported {num_runs} runs to CSV: {filepath}")

    return result_df
