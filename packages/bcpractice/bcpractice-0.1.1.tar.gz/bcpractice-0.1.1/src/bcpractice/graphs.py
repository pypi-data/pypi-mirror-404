"""TikZ graph templates for reliable graph generation."""

from __future__ import annotations

import math


def slope_field(
    equation: str,
    x_range: tuple[float, float] = (-3, 3),
    y_range: tuple[float, float] = (-3, 3),
    filled: bool = True,
) -> str:
    """Generate a slope field TikZ graph.

    Args:
        equation: The dy/dx equation (e.g., "x-y", "x/y", "x*y")
        x_range: (xmin, xmax)
        y_range: (ymin, ymax)
        filled: If True, draw actual slope segments. If False, empty grid for students.
    """
    if not filled:
        return slope_field_simple(equation, x_range, y_range)

    return slope_field_filled(equation, x_range, y_range)


def safe_eval_slope(equation: str, x: float, y: float) -> float | None:
    """Safely evaluate a slope equation at (x, y)."""
    try:
        # Create safe namespace with math functions
        safe_dict = {
            "x": x,
            "y": y,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "exp": math.exp,
            "log": math.log,
            "sqrt": math.sqrt,
            "abs": abs,
            "pi": math.pi,
            "e": math.e,
        }
        # Replace common math notation
        expr = equation.replace("^", "**")
        result = eval(expr, {"__builtins__": {}}, safe_dict)
        if math.isnan(result) or math.isinf(result):
            return None
        return result
    except (ZeroDivisionError, ValueError, TypeError, SyntaxError):
        return None


def slope_field_filled(
    equation: str,
    x_range: tuple[float, float] = (-3, 3),
    y_range: tuple[float, float] = (-3, 3),
) -> str:
    """Generate a slope field with actual slope segments drawn.

    Computes slopes in Python and generates simple TikZ line coordinates.
    """
    xmin, xmax = x_range
    ymin, ymax = y_range

    # Generate grid points
    x_points = list(range(int(xmin), int(xmax) + 1))
    y_points = list(range(int(ymin), int(ymax) + 1))

    # Length of slope segments
    seg_len = 0.3

    # Compute slope segments
    segments = []
    for x in x_points:
        for y in y_points:
            slope = safe_eval_slope(equation, x, y)
            if slope is not None:
                # Normalize direction vector
                length = math.sqrt(1 + slope * slope)
                dx = seg_len / length
                dy = seg_len * slope / length

                x1, y1 = x - dx / 2, y - dy / 2
                x2, y2 = x + dx / 2, y + dy / 2
                segments.append((x1, y1, x2, y2))

    # Build TikZ
    tikz = f"""\\begin{{tikzpicture}}[scale=0.7]
\\begin{{axis}}[
    axis lines=middle,
    xlabel={{$x$}},
    ylabel={{$y$}},
    xmin={xmin - 0.5}, xmax={xmax + 0.5},
    ymin={ymin - 0.5}, ymax={ymax + 0.5},
    xtick={{{int(xmin)},...,{int(xmax)}}},
    ytick={{{int(ymin)},...,{int(ymax)}}},
    grid=major,
    grid style={{gray!30}},
    width=10cm,
    height=8cm,
    title={{$\\dfrac{{dy}}{{dx}} = {equation}$}},
    title style={{at={{(0.5,1.02)}}, anchor=south}},
]
"""

    # Add each slope segment as a simple line plot
    for x1, y1, x2, y2 in segments:
        tikz += f"\\addplot[blue, thick] coordinates {{({x1:.3f},{y1:.3f}) ({x2:.3f},{y2:.3f})}};\n"

    tikz += """\\end{axis}
\\end{tikzpicture}"""

    return tikz


def slope_field_simple(
    equation: str,
    x_range: tuple[float, float] = (-3, 3),
    y_range: tuple[float, float] = (-3, 3),
) -> str:
    """Generate a slope field grid with equation shown.

    Provides a clean grid where students can visualize/sketch the slopes.
    The equation is displayed for reference.
    """
    xmin, xmax = x_range
    ymin, ymax = y_range

    # Generate grid points
    points = []
    for x in range(int(xmin), int(xmax) + 1):
        for y in range(int(ymin), int(ymax) + 1):
            points.append(f"({x},{y})")

    return f"""\\begin{{tikzpicture}}[scale=0.7]
\\begin{{axis}}[
    axis lines=middle,
    xlabel={{$x$}},
    ylabel={{$y$}},
    xmin={xmin - 0.5}, xmax={xmax + 0.5},
    ymin={ymin - 0.5}, ymax={ymax + 0.5},
    xtick={{{int(xmin)},...,{int(xmax)}}},
    ytick={{{int(ymin)},...,{int(ymax)}}},
    grid=major,
    grid style={{gray!30}},
    width=10cm,
    height=8cm,
    title={{$\\dfrac{{dy}}{{dx}} = {equation}$}},
    title style={{at={{(0.5,1.02)}}, anchor=south}},
]
% Grid points for slope field
\\addplot[only marks, mark=o, mark size=1.5pt, black!50] coordinates {{
{" ".join(points)}
}};
\\end{{axis}}
\\end{{tikzpicture}}"""


def piecewise_linear(
    points: list[tuple[float, float]],
    x_range: tuple[float, float] | None = None,
    y_range: tuple[float, float] | None = None,
    xlabel: str = "x",
    ylabel: str = "y",
    show_points: bool = True,
) -> str:
    """Generate a piecewise linear function graph.

    Args:
        points: List of (x, y) coordinates defining the piecewise function
        x_range: Optional (xmin, xmax), auto-calculated if None
        y_range: Optional (ymin, ymax), auto-calculated if None
        xlabel: Label for x-axis
        ylabel: Label for y-axis
        show_points: Whether to show dots at the vertices
    """
    if not points:
        return ""

    # Auto-calculate ranges if not provided
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    if x_range is None:
        xmin, xmax = min(xs) - 1, max(xs) + 1
    else:
        xmin, xmax = x_range

    if y_range is None:
        ymin, ymax = min(ys) - 1, max(ys) + 1
    else:
        ymin, ymax = y_range

    # Build coordinate string
    coords = " ".join([f"({p[0]},{p[1]})" for p in points])

    tikz = f"""\\begin{{tikzpicture}}[scale=0.75]
\\begin{{axis}}[
    axis lines=middle,
    xlabel={{${xlabel}$}},
    ylabel={{${ylabel}$}},
    xmin={xmin}, xmax={xmax},
    ymin={ymin}, ymax={ymax},
    grid=major,
    grid style={{gray!30}},
    width=10cm,
    height=6cm,
]
\\addplot[thick, blue, mark=none] coordinates {{ {coords} }};
"""

    if show_points:
        tikz += f"\\addplot[only marks, mark=*, blue, mark size=2pt] coordinates {{ {coords} }};\n"

    tikz += """\\end{axis}
\\end{tikzpicture}"""

    return tikz


def function_plot(
    functions: list[dict],
    x_range: tuple[float, float] = (-5, 5),
    y_range: tuple[float, float] = (-5, 5),
    xlabel: str = "x",
    ylabel: str = "y",
) -> str:
    """Generate a function plot with one or more functions.

    Args:
        functions: List of dicts with keys:
            - "expr": pgfmath expression (e.g., "x^2", "sin(deg(x))")
            - "domain": (xmin, xmax) for this function
            - "color": optional color (default "blue")
            - "label": optional label for legend
        x_range: (xmin, xmax) for axis
        y_range: (ymin, ymax) for axis
    """
    xmin, xmax = x_range
    ymin, ymax = y_range

    tikz = f"""\\begin{{tikzpicture}}[scale=0.75]
\\begin{{axis}}[
    axis lines=middle,
    xlabel={{${xlabel}$}},
    ylabel={{${ylabel}$}},
    xmin={xmin}, xmax={xmax},
    ymin={ymin}, ymax={ymax},
    grid=major,
    grid style={{gray!30}},
    width=10cm,
    height=6cm,
    samples=100,
]
"""

    for func in functions:
        expr = func.get("expr", "x")
        domain = func.get("domain", (xmin, xmax))
        color = func.get("color", "blue")

        tikz += f"\\addplot[thick, {color}, domain={domain[0]}:{domain[1]}] {{{expr}}};\n"

    tikz += """\\end{axis}
\\end{tikzpicture}"""

    return tikz


def accumulation_graph(
    f_points: list[tuple[float, float]],
    shade_regions: list[dict] | None = None,
    x_range: tuple[float, float] | None = None,
    y_range: tuple[float, float] | None = None,
) -> str:
    """Generate a graph for accumulation function problems.

    Args:
        f_points: Points defining f(t) as piecewise linear
        shade_regions: Optional list of regions to shade, each with:
            - "x_start", "x_end": x bounds
            - "color": fill color (default "blue!20")
            - "above": True if shading above x-axis region
        x_range, y_range: Axis bounds
    """
    if not f_points:
        return ""

    xs = [p[0] for p in f_points]
    ys = [p[1] for p in f_points]

    if x_range is None:
        xmin, xmax = min(xs) - 0.5, max(xs) + 0.5
    else:
        xmin, xmax = x_range

    if y_range is None:
        ymin, ymax = min(min(ys), 0) - 1, max(max(ys), 0) + 1
    else:
        ymin, ymax = y_range

    coords = " ".join([f"({p[0]},{p[1]})" for p in f_points])

    tikz = f"""\\begin{{tikzpicture}}[scale=0.75]
\\begin{{axis}}[
    axis lines=middle,
    xlabel={{$t$}},
    ylabel={{$y = f(t)$}},
    xmin={xmin}, xmax={xmax},
    ymin={ymin}, ymax={ymax},
    grid=major,
    grid style={{gray!30}},
    width=10cm,
    height=6cm,
]
"""

    # Add shaded regions if specified
    if shade_regions:
        for region in shade_regions:
            x_start = region.get("x_start", xmin)
            x_end = region.get("x_end", xmax)
            color = region.get("color", "blue!20")
            # Find the relevant points for this region
            tikz += f"\\addplot[fill={color}, draw=none, domain={x_start}:{x_end}] {{0}} \\closedcycle;\n"

    # Add the function
    tikz += f"\\addplot[thick, blue, mark=none] coordinates {{ {coords} }};\n"
    tikz += f"\\addplot[only marks, mark=*, blue, mark size=2pt] coordinates {{ {coords} }};\n"

    tikz += """\\end{axis}
\\end{tikzpicture}"""

    return tikz


def velocity_graph(
    v_points: list[tuple[float, float]],
    x_range: tuple[float, float] | None = None,
    y_range: tuple[float, float] | None = None,
) -> str:
    """Generate a velocity-time graph for particle motion problems."""
    return piecewise_linear(
        points=v_points,
        x_range=x_range,
        y_range=y_range,
        xlabel="t",
        ylabel="v(t)",
        show_points=True,
    )


# Graph type registry for easy lookup
GRAPH_TEMPLATES = {
    "slope_field": slope_field,  # Main function that handles filled/empty
    "piecewise": piecewise_linear,
    "function": function_plot,
    "accumulation": accumulation_graph,
    "velocity": velocity_graph,
}


def generate_graph(graph_type: str, **kwargs) -> str:
    """Generate a graph from a template.

    Args:
        graph_type: One of the registered graph types
        **kwargs: Arguments to pass to the template function

    Returns:
        TikZ code string
    """
    if graph_type not in GRAPH_TEMPLATES:
        return ""

    try:
        return GRAPH_TEMPLATES[graph_type](**kwargs)
    except Exception as e:
        # Return empty on error - don't break compilation
        return f"% Graph generation error: {e}"
