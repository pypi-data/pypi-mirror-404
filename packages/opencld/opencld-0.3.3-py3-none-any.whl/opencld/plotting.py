from __future__ import annotations
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Union
import networkx as nx
import shutil, re, html
import seaborn as sns
import pydot

def _strip_units(value):
    """Helper to strip Pint units from a value, returning the magnitude."""
    if hasattr(value, 'magnitude'):
        return value.magnitude
    return value

def _strip_units_series(series):
    """Strip Pint units from a pandas Series or Index."""
    return series.map(_strip_units) if hasattr(series, 'map') else [_strip_units(v) for v in series]


class Plotting:
    """
    Visualization utilities for OpenCLD.

    All methods are @staticmethod so they can be used via the class or an instance.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Time-series plots

    @staticmethod
    def plot_timeseries(
        data: Union[pd.DataFrame, Mapping[str, Iterable[float]], Iterable[Iterable[float]]],
        columns: Optional[Sequence[str]] = None,
        time_column: Optional[str] = None,
        figsize: Sequence[float] = (12, 7),
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        legend: bool = True,
        grid: bool = True,
        styles: Optional[Mapping[str, Mapping[str, Any]]] = None,
        save_path: Optional[str] = None,
        show_plot: bool = True,
        ax: Optional[plt.Axes] = None,
        **plot_kwargs: Any,
    ) -> plt.Axes:
        """Plot one or multiple time series on a single set of axes."""
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame(data)

        if df.empty:
            raise ValueError("No data available to plot.")

        if time_column:
            if time_column not in df.columns:
                raise KeyError(f"time_column '{time_column}' not found in provided data.")
            df = df.set_index(time_column)

        if columns is None:
            columns = [c for c in df.columns if c != time_column]
        if not columns:
            raise ValueError("No columns selected for plotting.")

        owns_fig = False
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
            owns_fig = True
        else:
            fig = ax.figure

        styles = styles or {}
        
        # Strip Pint units from index for plotting compatibility
        plot_index = _strip_units_series(df.index)
        
        for col in columns:
            if col not in df.columns:
                raise KeyError(f"Column '{col}' not found in provided data.")
            line_kwargs: Dict[str, Any] = {**plot_kwargs, **styles.get(col, {})}
            # Strip Pint units from data values
            plot_values = _strip_units_series(df[col])
            ax.plot(plot_index, plot_values, label=col, **line_kwargs)

        ax.set_title(title or "Time Series")
        ax.set_xlabel(xlabel or "Time")
        ax.set_ylabel(ylabel or "Value")
        ax.grid(grid)
        if legend:
            ax.legend()

        fig.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=plot_kwargs.get("dpi", 300))
            print(f"[INFO] Plot saved to: {save_path}")

        if owns_fig:
            if show_plot:
                plt.show()
            else:
                plt.close(fig)

        return ax

    # ------------------------------------------------------------------
    # Monte Carlo visualizations

    @staticmethod
    def plot_alpha_density_lines(
        df: pd.DataFrame,
        variable_name: str,
        figsize: Sequence[float] = (12, 6),
        line_color: str = "green",
        alpha: float = 0.05,
        save_path: Optional[str] = None,
        show_plot: bool = True,
        title: Optional[str] = None,
    ) -> None:
        """Plot overlapping time series as transparent lines to show density."""
        subset = df[df["variable"] == variable_name]
        if subset.empty:
            print(f"[WARN] No data found for variable '{variable_name}'. Skipping plot.")
            return

        pivoted = subset.pivot(index="time", columns="run_id", values="value")

        plt.figure(figsize=figsize)
        for run_id in pivoted.columns:
            plt.plot(pivoted.index, pivoted[run_id], color=line_color, alpha=alpha)

        median = pivoted.median(axis=1)
        plt.plot(pivoted.index, median, color="red", linewidth=1.5, label="Median")

        plt.title(title if title else f"Density Line Plot for '{variable_name}'")
        plt.xlabel("Time")
        plt.ylabel(variable_name)
        plt.grid(True, linestyle="--", alpha=0.3)
        plt.legend()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300)
            print(f"[INFO] Plot saved to: {save_path}")

        if show_plot:
            plt.show()
        else:
            plt.close()

    @staticmethod
    def plot_variable_facets(
        df: pd.DataFrame,
        *,
        variable_column: str = "variable",
        value_column: str = "value",
        time_column: str = "time",
        type_column: str = "type",
        line_color: str = "blue",
        alpha: float = 0.1,
        median_color: str = "red",
        variables: Optional[Sequence[str]] = None,
        variable_types_to_plot: Optional[Sequence[str]] = ("stock", "flow", "auxiliary"),
        col_wrap: int = 3,
        height: float = 3.0,
        aspect: float = 1.5,
        save_path: Optional[str] = None,
        show_plot: bool = True,
    ):
        """Facet grid for Monte Carlo outputs grouped by variable."""
        if df.empty:
            print("[WARN] Provided DataFrame is empty. Skipping plot.")
            return

        for col in (variable_column, value_column, time_column):
            if col not in df.columns:
                raise KeyError(f"'{col}' column not found in DataFrame.")

        plot_df = df
        if type_column:
            if type_column not in df.columns:
                print(f"[WARN] '{type_column}' column not found; plotting all variables.")
                type_column = ""
            elif variable_types_to_plot:
                plot_df = plot_df[plot_df[type_column].isin(variable_types_to_plot)]

        if variables is None:
            variables = plot_df[variable_column].unique().tolist()
        else:
            unknown = [v for v in variables if v not in plot_df[variable_column].unique()]
            if unknown:
                print(f"[WARN] Variables not found and will be skipped: {unknown}")
            variables = [v for v in variables if v in plot_df[variable_column].unique()]

        if len(variables) == 0:
            print("No variables found to plot.")
            return

        plot_df = plot_df[plot_df[variable_column].isin(variables)]

        g = sns.FacetGrid(
            plot_df, col=variable_column, col_wrap=col_wrap,
            sharey=False, height=height, aspect=aspect,
        )

        g.map_dataframe(
            sns.lineplot, time_column, value_column, "run_id",
            estimator=None, lw=1, alpha=alpha, color=line_color,
        )

        def _median_overlay(data, **kwargs):
            med = data.groupby(time_column)[value_column].median()
            plt.plot(med.index, med.values, **kwargs)

        g.map_dataframe(_median_overlay, color=median_color, lw=2)

        g.fig.suptitle("Time Series per Variable", y=1.02, fontsize=16)
        g.set_titles("{col_name}")
        g.set_axis_labels("Time", "Value")

        legend_elements = [Line2D([0], [0], color=median_color, lw=2, label="Median")]
        g.fig.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(0.98, 0.98))

        g.fig.tight_layout(rect=[0, 0, 1, 0.98])

        if save_path:
            g.fig.savefig(save_path, dpi=300)
            print(f"[INFO] All variables plot saved to: {save_path}")

        if show_plot:
            plt.show()
        else:
            plt.close(g.fig)

        return g

    # ------------------------------------------------------------------
    # Backwards-compatible alias

    @staticmethod
    def plot_all_variables_from_csv(*args, **kwargs):
        return Plotting.plot_variable_facets(*args, **kwargs)

    # ------------------------------------------------------------------
    # Structure graph wrapper
    # This calls the module-level dispatcher named `plot_structure_graph`.
    # We reference it via globals() to avoid name shadowing.


    @staticmethod
    def plot_structure_graph_native(model, filename=None, figsize=(16, 12), layout_prog='spring', k=0.9, seed=42,
                                    **kwargs):
        """
        Generates and optionally saves a visual plot of the model structure graph.
        If filename is None, displays the plot inline.
        """
        import matplotlib.pyplot as plt
        import networkx as nx

        if filename:
            print(f"\nGenerating and saving full model structure graph to ('{filename}')...")
        else:
            print(f"\nGenerating and displaying full model structure graph...")

        all_polarities = model.get_link_polarities()
        if not all_polarities:
            print("  Cannot generate graph: Link polarities not available.")
            return None

        G_plot = nx.DiGraph()
        all_nodes_in_links = set(u for u, v in all_polarities.keys()) | set(v for u, v in all_polarities.keys())

        type_to_color_map = {
            'Stock': 'skyblue', 'Flow': 'lightcoral',
            'Auxiliary': 'lightgreen', 'Parameter': 'lightgrey'
        }

        node_types = {}
        for name in all_nodes_in_links:
            comp_type = type(model.stocks.get(name) or model.flows.get(name) or
                             model.auxiliaries.get(name) or model.parameters.get(name)).__name__
            node_type_str = {
                'Stock': 'Stock', 'Flow': 'Flow', 'Auxiliary': 'Auxiliary', 'Parameter': 'Parameter'
            }.get(comp_type, 'Unknown')
            node_types[name] = node_type_str
            G_plot.add_node(name, type=node_type_str)

        edge_labels = {(u, v): {1: '+', -1: '-', 0: '0'}.get(sign, '?')
                       for (u, v), sign in all_polarities.items() if G_plot.has_node(u) and G_plot.has_node(v)}
        G_plot.add_edges_from(edge_labels.keys())

        if G_plot.number_of_nodes() == 0:
            print("  Cannot generate graph: No nodes added.")
            return None

        fig, ax_graph = plt.subplots(figsize=figsize)

        try:
            layout_funcs = {'spring': nx.spring_layout, 'kamada_kawai': nx.kamada_kawai_layout}
            pos = layout_funcs.get(layout_prog, nx.spring_layout)(G_plot, k=k, seed=seed)
        except Exception as e:
            print(f"    Layout '{layout_prog}' failed ({e}), using 'spring' as fallback.")
            pos = nx.spring_layout(G_plot, k=k, seed=seed)

        node_colors = [type_to_color_map.get(node_types.get(name), 'grey') for name in G_plot.nodes()]

        # Define drawing kwargs for cleaner calls
        draw_kwargs = {
            'node_size': kwargs.get('node_size', 2500), 'font_size': kwargs.get('font_size', 9),
            'alpha': kwargs.get('alpha', 0.9), 'arrowstyle': kwargs.get('arrowstyle', '-|>'),
            'arrowsize': kwargs.get('arrowsize', 20), 'edge_color': kwargs.get('edge_color', 'gray'),
            'connectionstyle': 'arc3,rad=0.1'
        }

        nx.draw_networkx(G_plot, pos, ax=ax_graph, node_color=node_colors, **draw_kwargs)
        nx.draw_networkx_edge_labels(G_plot, pos, ax=ax_graph, edge_labels=edge_labels,
                                     font_color=kwargs.get('edge_font_color', 'black'),
                                     font_size=kwargs.get('edge_font_size', 8), rotate=False)

        ax_graph.set_title(kwargs.get('title', "Model Structure with Link Polarities (@ t=0)"))
        plt.axis('off')
        plt.tight_layout()

        if filename:
            try:
                plt.savefig(filename, dpi=kwargs.get('dpi', 300), bbox_inches='tight')
                print(f"  Saved structure graph: {filename}")
            except Exception as e:
                print(f"  Error saving graph plot: {e}")
            finally:
                plt.close(fig)
        else:
            plt.show()

        return fig

    @staticmethod
    def plot_structure_graph_pydot(
        model,
        filename="structure.svg",
        rankdir="LR",
        engine="dot",
        square_size_in=12,
        dpi=150,
        nodesep=0.6,
        ranksep=1.0,
        show_parameters=True,
        show_auxiliaries=True,
        show_polarity_on_aux_edges=False,
    ):
        """
        SD-style with minimal valve anchors (no extra gray dots).
          - Stocks = boxes (ports on sides so flows enter/exit correctly)
          - Auxiliaries = ellipses
          - Parameters = hexagons
          - Flows = pipes (edges) through a tiny diamond 'valve' anchor (no label)
          - Inputs (Params/Aux/Stocks/Flows) connect into the valve
          - Pure inflow: valve → stock
          - Pure outflow: stock → valve
        """

        if shutil.which("dot") is None:
            print("[ERROR] Graphviz 'dot' not found. Please install Graphviz and ensure 'dot' is in PATH.")
            return None

        if not getattr(model, "_dependency_graph", None):
            print("[WARN] Dependency graph not built.")
            return None

        # ---------- helpers ----------
        def _safe_id(s: str) -> str:
            return re.sub(r'[^0-9A-Za-z_]', '_', str(s))

        def _normalize_text(s: str) -> str:
            # Kill any stray HTML breaks and normalize curly apostrophes
            return re.sub(r'(?i)<\s*br\s*/?\s*>', ' ', str(s)).replace("\u2019", "'")

        # compass by rankdir + named ports we will use in edges
        if rankdir.upper() == "LR":
            IN_COMPASS, OUT_COMPASS = "w", "e"
        else:  # "TB"
            IN_COMPASS, OUT_COMPASS = "n", "s"

        # Helper to decide which extra port to use for influence edges
        def _influence_port_and_compass():
            if rankdir.upper() == "LR":
                return [("TOP", "n"), ("BOT", "s")]  # top and bottom for LR
            else:
                return [("OUT", "e"), ("IN", "w")]  # right and left for TB

        def valve_id(flow_name: str) -> str:
            return f"v__{_safe_id(flow_name)}"

        # ---------- theme ----------
        STOCK_COLOR = "#a7d0f5"
        AUX_COLOR = "#bfe7bf"
        PARAM_COLOR = "#e3e3e3"
        FLOW_COLOR = "#f5b7b1"
        EDGE_COLOR = "#888888"
        FONT = "DejaVu Sans"

        # ---------- base graph ----------
        g = pydot.Dot(graph_type="digraph", rankdir=rankdir)

        # graph defaults – add charset
        g_defaults = dict(
            splines="ortho",
            concentrate="false",
            fontname=FONT,
            fontsize="10",
            ratio="compress",
            dpi=str(dpi),
            nodesep=str(nodesep),
            ranksep=str(ranksep),
            charset="UTF-8",
        )
        if square_size_in:
            g_defaults["size"] = f"{square_size_in},{square_size_in}!"
        g.set_graph_defaults(**g_defaults)

        g.set_node_defaults(fontname=FONT, fontsize="10", style="filled", color="#444444")
        g.set_edge_defaults(fontname=FONT, fontsize="9", color=EDGE_COLOR, arrowsize="1.0", decorate="false")

        # ---------- node builders ----------
        def add_aux(name):
            nid = _safe_id(name)
            g.add_node(pydot.Node(
                nid, shape="ellipse", fillcolor=AUX_COLOR,
                label=_normalize_text(name),
                tooltip=_normalize_text(name)))
            return nid

        def add_param(name):
            nid = _safe_id(name)
            g.add_node(pydot.Node(
                nid, shape="hexagon", fillcolor=PARAM_COLOR,
                label=_normalize_text(name),
                tooltip=_normalize_text(name)))
            return nid

        def add_stock(name):
            nid = _safe_id(name)
            txt = html.escape(_normalize_text(name))
            label = (
                f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
                f'<TR><TD PORT="TOP" HEIGHT="4"></TD></TR>'
                f'<TR><TD>'
                f'  <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0"><TR>'
                f'    <TD PORT="IN"  WIDTH="6"></TD>'
                f'    <TD FIXEDSIZE="FALSE" BGCOLOR="{STOCK_COLOR}">{txt}</TD>'
                f'    <TD PORT="OUT" WIDTH="6"></TD>'
                f'  </TR></TABLE>'
                f'</TD></TR>'
                f'<TR><TD PORT="BOT" HEIGHT="4"></TD></TR>'
                f'</TABLE>>'
            )
            g.add_node(pydot.Node(nid, shape="plain", label=label, style="filled", fillcolor=STOCK_COLOR,
                                  tooltip=_normalize_text(name)))
            return nid

        def add_valve(v_id, title=None):
            g.add_node(pydot.Node(
                v_id, shape="diamond", width="0.22", height="0.22", fixedsize="true",
                label="", xlabel="", margin="0.0", fillcolor=FLOW_COLOR, color="#444444", penwidth="1.0",
                tooltip=(title or v_id)
            ))

        # ---------- add main nodes ----------
        id_map = {}
        for s in model.stocks:
            id_map[s] = add_stock(s)
        if show_auxiliaries:
            for a in model.auxiliaries:
                id_map[a] = add_aux(a)
        if show_parameters:
            for p in model.parameters:
                id_map[p] = add_param(p)

        def _minlen_for_text(txt: str, gain=0.06, floor=1, cap=10):
            return max(floor, min(cap, int(len(txt) * gain)))

        # ---------- flows via valves ----------
        flow_valves = {}
        for fname, F in model.flows.items():
            v_id = valve_id(fname)
            add_valve(v_id, title=str(fname))
            flow_valves[fname] = v_id

            src_stock = F.source_stock.name if getattr(F, "source_stock", None) else None
            tgt_stock = F.target_stock.name if getattr(F, "target_stock", None) else None

            flow_label = _normalize_text(fname)

            if src_stock and tgt_stock:
                g.add_edge(pydot.Edge(
                    f'{id_map[src_stock]}:OUT:{OUT_COMPASS}', v_id,
                    color=FLOW_COLOR, arrowhead="normal",
                    minlen=str(_minlen_for_text(flow_label))
                ))
                g.add_edge(pydot.Edge(
                    v_id, f'{id_map[tgt_stock]}:IN:{IN_COMPASS}',
                    color=FLOW_COLOR, arrowhead="normal",
                    xlabel=flow_label,
                    minlen=str(_minlen_for_text(flow_label)),
                    labeldistance="1.2", labelangle="0"
                ))
            elif tgt_stock and not src_stock:
                g.add_edge(pydot.Edge(
                    v_id, f'{id_map[tgt_stock]}:IN:{IN_COMPASS}',
                    color=FLOW_COLOR, arrowhead="normal",
                    xlabel=flow_label,
                    minlen=str(_minlen_for_text(flow_label)),
                    labeldistance="1.2", labelangle="0"
                ))
            elif src_stock and not tgt_stock:
                g.add_edge(pydot.Edge(
                    f'{id_map[src_stock]}:OUT:{OUT_COMPASS}', v_id,
                    color=FLOW_COLOR, arrowhead="normal",
                    xlabel=flow_label,
                    minlen=str(_minlen_for_text(flow_label)),
                    labeldistance="1.2", labelangle="0"
                ))

        ports = _influence_port_and_compass()  # decide available ports

        # ---------- connect inputs to valve ----------
        for fname, F in model.flows.items():
            v_id = flow_valves.get(fname)
            for inp in (getattr(F, "inputs", None) or []):
                src_id = None
                from_stock = False
                if (not show_parameters) and inp in model.parameters:
                    continue
                if (not show_auxiliaries) and inp in model.auxiliaries:
                    continue
                if inp in model.parameters or inp in model.auxiliaries or inp in model.stocks:
                    src_id = id_map.get(inp)
                    from_stock = inp in model.stocks
                elif inp in model.flows:
                    src_id = flow_valves.get(inp)

                if not src_id:
                    continue

                if from_stock:
                    port, compass = ports[hash((inp, fname)) % 2]
                    src_endpoint = f'{src_id}:{port}:{compass}'
                else:
                    src_endpoint = src_id

                lbl = ""
                if show_polarity_on_aux_edges:
                    sign = model._link_polarities.get((inp, fname))
                    if sign is not None:
                        lbl = {1: "+", -1: "-", 0: "0"}.get(sign, "?")

                g.add_edge(pydot.Edge(src_endpoint, v_id, color=EDGE_COLOR, label=lbl, arrowhead="none"))

        # ---------- remaining influences into auxiliaries ----------
        already = {(e.get_source(), e.get_destination()) for e in g.get_edges()}
        for (u, v), sign in model._link_polarities.items():
            if v not in model.auxiliaries or (not show_auxiliaries):
                continue
            if (not show_parameters) and u in model.parameters:
                continue
            u_id = id_map.get(u) or flow_valves.get(u)
            v_id = id_map.get(v)
            if not (u_id and v_id):
                continue
            if (u_id, v_id) in already:
                continue
            lbl = {1: "+", -1: "-", 0: "0"}.get(sign, "?") if show_polarity_on_aux_edges else ""
            g.add_edge(pydot.Edge(u_id, v_id, label=lbl, color=EDGE_COLOR))

        # ---------- export ----------
        try:
            ext = filename.split(".")[-1].lower()
            g.write(filename, prog=engine, format=ext)
            print(f"[OK] Structure graph saved to {filename}")
        except Exception as e:
            print("[ERROR] Graphviz render failed:", e)
            return None

        return filename


    @staticmethod
    def plot_structure_graph(model, engine="native", **kwargs):
        if engine == "native":
            return Plotting.plot_structure_graph_native(model, **kwargs)
        elif engine == "graphviz":
            return Plotting.plot_structure_graph_pydot(model, **kwargs)
        else:
            raise ValueError(f"Unknown engine: {engine}")



def plot_timeseries(*a, **k): return Plotting.plot_timeseries(*a, **k)
def plot_alpha_density_lines(*a, **k): return Plotting.plot_alpha_density_lines(*a, **k)
def plot_variable_facets(*a, **k): return Plotting.plot_variable_facets(*a, **k)
def plot_structure_graph(model, engine="native", **k): return Plotting.plot_structure_graph(model, engine, **k)
def plot_all_variables_from_csv(*a, **k): return Plotting.plot_all_variables_from_csv(*a, **k)
