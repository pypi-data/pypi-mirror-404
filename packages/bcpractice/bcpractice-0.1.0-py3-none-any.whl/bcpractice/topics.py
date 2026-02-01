"""AP BC Calculus curriculum topics organized by unit."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Topic:
    id: str
    name: str
    bc_only: bool = False


@dataclass
class Unit:
    number: int
    name: str
    topics: list[Topic]
    bc_only: bool = False


# Complete AP BC Calculus Curriculum
# Source: College Board CED & FlippedMath

UNITS: list[Unit] = [
    Unit(
        number=1,
        name="Limits and Continuity",
        topics=[
            Topic("1.1", "Can Change Occur at an Instant?"),
            Topic("1.2", "Defining Limits and Using Limit Notation"),
            Topic("1.3", "Estimating Limit Values from Graphs"),
            Topic("1.4", "Estimating Limit Values from Tables"),
            Topic("1.5", "Determining Limits Using Algebraic Properties"),
            Topic("1.6", "Determining Limits Using Algebraic Manipulation"),
            Topic("1.7", "Selecting Procedures for Determining Limits"),
            Topic("1.8", "Determining Limits Using the Squeeze Theorem"),
            Topic("1.9", "Connecting Multiple Representations of Limits"),
            Topic("1.10", "Exploring Types of Discontinuities"),
            Topic("1.11", "Defining Continuity at a Point"),
            Topic("1.12", "Confirming Continuity Over an Interval"),
            Topic("1.13", "Removing Discontinuities"),
            Topic("1.14", "Infinite Limits and Vertical Asymptotes"),
            Topic("1.15", "Limits at Infinity and Horizontal Asymptotes"),
            Topic("1.16", "Intermediate Value Theorem"),
        ],
    ),
    Unit(
        number=2,
        name="Differentiation: Definition and Fundamental Properties",
        topics=[
            Topic("2.1", "Defining Average and Instantaneous Rate of Change"),
            Topic("2.2", "Defining the Derivative and Using Derivative Notation"),
            Topic("2.3", "Estimating Derivatives at a Point"),
            Topic("2.4", "Connecting Differentiability and Continuity"),
            Topic("2.5", "Applying the Power Rule"),
            Topic("2.6", "Derivative Rules: Constant, Sum, Difference, Constant Multiple"),
            Topic("2.7", "Derivatives of cos(x), sin(x), e^x, ln(x)"),
            Topic("2.8", "The Product Rule"),
            Topic("2.9", "The Quotient Rule"),
            Topic("2.10", "Derivatives of tan(x), cot(x), sec(x), csc(x)"),
        ],
    ),
    Unit(
        number=3,
        name="Differentiation: Composite, Implicit, and Inverse Functions",
        topics=[
            Topic("3.1", "The Chain Rule"),
            Topic("3.2", "Implicit Differentiation"),
            Topic("3.3", "Differentiating Inverse Functions"),
            Topic("3.4", "Differentiating Inverse Trigonometric Functions"),
            Topic("3.5", "Selecting Procedures for Calculating Derivatives"),
            Topic("3.6", "Calculating Higher-Order Derivatives"),
        ],
    ),
    Unit(
        number=4,
        name="Contextual Applications of Differentiation",
        topics=[
            Topic("4.1", "Interpreting the Meaning of the Derivative in Context"),
            Topic("4.2", "Straight-Line Motion: Position, Velocity, Acceleration"),
            Topic("4.3", "Rates of Change in Applied Contexts Beyond Motion"),
            Topic("4.4", "Introduction to Related Rates"),
            Topic("4.5", "Solving Related Rates Problems"),
            Topic("4.6", "Approximating Values Using Local Linearity and Linearization"),
            Topic("4.7", "Using L'Hopital's Rule for Indeterminate Forms"),
        ],
    ),
    Unit(
        number=5,
        name="Analytical Applications of Differentiation",
        topics=[
            Topic("5.1", "Using the Mean Value Theorem"),
            Topic("5.2", "Extreme Value Theorem, Global vs. Local Extrema, Critical Points"),
            Topic("5.3", "Determining Intervals Where Functions Increase or Decrease"),
            Topic("5.4", "Using the First Derivative Test for Relative Extrema"),
            Topic("5.5", "Using the Candidates Test for Absolute Extrema"),
            Topic("5.6", "Determining Concavity of Functions"),
            Topic("5.7", "Using the Second Derivative Test for Extrema"),
            Topic("5.8", "Sketching Graphs of Functions and Their Derivatives"),
            Topic("5.9", "Connecting a Function, Its First and Second Derivatives"),
            Topic("5.10", "Introduction to Optimization Problems"),
            Topic("5.11", "Solving Optimization Problems"),
            Topic("5.12", "Exploring Behaviors of Implicit Relations"),
        ],
    ),
    Unit(
        number=6,
        name="Integration and Accumulation of Change",
        topics=[
            Topic("6.1", "Exploring Accumulation of Change"),
            Topic("6.2", "Approximating Areas with Riemann Sums"),
            Topic("6.3", "Riemann Sums, Summation Notation, and Definite Integral Notation"),
            Topic("6.4", "The Fundamental Theorem of Calculus and Accumulation Functions"),
            Topic("6.5", "Interpreting the Behavior of Accumulation Functions"),
            Topic("6.6", "Applying Properties of Definite Integrals"),
            Topic("6.7", "The Fundamental Theorem of Calculus and Definite Integrals"),
            Topic("6.8", "Finding Antiderivatives and Indefinite Integrals"),
            Topic("6.9", "Integrating Using Substitution"),
            Topic("6.10", "Integrating Using Long Division and Completing the Square"),
            Topic("6.11", "Integrating Using Integration by Parts", bc_only=True),
            Topic("6.12", "Integrating Using Linear Partial Fractions", bc_only=True),
            Topic("6.13", "Evaluating Improper Integrals", bc_only=True),
            Topic("6.14", "Selecting Techniques for Antidifferentiation"),
        ],
    ),
    Unit(
        number=7,
        name="Differential Equations",
        topics=[
            Topic("7.1", "Modeling Situations with Differential Equations"),
            Topic("7.2", "Verifying Solutions for Differential Equations"),
            Topic("7.3", "Sketching Slope Fields"),
            Topic("7.4", "Reasoning Using Slope Fields"),
            Topic("7.5", "Approximating Solutions Using Euler's Method", bc_only=True),
            Topic("7.6", "General Solutions Using Separation of Variables"),
            Topic("7.7", "Particular Solutions Using Initial Conditions and Separation of Variables"),
            Topic("7.8", "Exponential Models with Differential Equations"),
            Topic("7.9", "Logistic Models with Differential Equations", bc_only=True),
        ],
    ),
    Unit(
        number=8,
        name="Applications of Integration",
        topics=[
            Topic("8.1", "Average Value of a Function on an Interval"),
            Topic("8.2", "Position, Velocity, and Acceleration Using Integrals"),
            Topic("8.3", "Using Accumulation Functions and Definite Integrals in Applied Contexts"),
            Topic("8.4", "Area Between Curves (with respect to x)"),
            Topic("8.5", "Area Between Curves (with respect to y)"),
            Topic("8.6", "Area Between Curves with More Than Two Intersections"),
            Topic("8.7", "Volumes with Cross Sections: Squares and Rectangles"),
            Topic("8.8", "Volumes with Cross Sections: Triangles and Semicircles"),
            Topic("8.9", "Volume with Disc Method: Revolving Around x- or y-Axis"),
            Topic("8.10", "Volume with Disc Method: Revolving Around Other Axes"),
            Topic("8.11", "Volume with Washer Method: Revolving Around x- or y-Axis"),
            Topic("8.12", "Volume with Washer Method: Revolving Around Other Axes"),
            Topic("8.13", "Arc Length of a Smooth, Planar Curve", bc_only=True),
        ],
    ),
    Unit(
        number=9,
        name="Parametric Equations, Polar Coordinates, and Vector-Valued Functions",
        bc_only=True,
        topics=[
            Topic("9.1", "Defining and Differentiating Parametric Equations", bc_only=True),
            Topic("9.2", "Second Derivatives of Parametric Equations", bc_only=True),
            Topic("9.3", "Arc Lengths of Curves Given by Parametric Equations", bc_only=True),
            Topic("9.4", "Defining and Differentiating Vector-Valued Functions", bc_only=True),
            Topic("9.5", "Integrating Vector-Valued Functions", bc_only=True),
            Topic("9.6", "Solving Motion Problems Using Parametric and Vector-Valued Functions", bc_only=True),
            Topic("9.7", "Defining Polar Coordinates and Differentiating in Polar Form", bc_only=True),
            Topic("9.8", "Area of a Polar Region or Area Bounded by a Single Polar Curve", bc_only=True),
            Topic("9.9", "Area of a Region Bounded by Two Polar Curves", bc_only=True),
        ],
    ),
    Unit(
        number=10,
        name="Infinite Sequences and Series",
        bc_only=True,
        topics=[
            Topic("10.1", "Defining Convergent and Divergent Infinite Series", bc_only=True),
            Topic("10.2", "Working with Geometric Series", bc_only=True),
            Topic("10.3", "The nth Term Test for Divergence", bc_only=True),
            Topic("10.4", "Integral Test for Convergence", bc_only=True),
            Topic("10.5", "Harmonic Series and p-Series", bc_only=True),
            Topic("10.6", "Comparison Tests for Convergence", bc_only=True),
            Topic("10.7", "Alternating Series Test for Convergence", bc_only=True),
            Topic("10.8", "Ratio Test for Convergence", bc_only=True),
            Topic("10.9", "Determining Absolute or Conditional Convergence", bc_only=True),
            Topic("10.10", "Alternating Series Error Bound", bc_only=True),
            Topic("10.11", "Finding Taylor Polynomial Approximations of Functions", bc_only=True),
            Topic("10.12", "Lagrange Error Bound", bc_only=True),
            Topic("10.13", "Radius and Interval of Convergence of Power Series", bc_only=True),
            Topic("10.14", "Finding Taylor or Maclaurin Series for a Function", bc_only=True),
            Topic("10.15", "Representing Functions as Power Series", bc_only=True),
        ],
    ),
]


def get_unit(number: int) -> Unit | None:
    """Get a unit by its number."""
    for unit in UNITS:
        if unit.number == number:
            return unit
    return None


def get_topic(topic_id: str) -> tuple[Unit, Topic] | None:
    """Get a topic by its ID (e.g., '6.11')."""
    for unit in UNITS:
        for topic in unit.topics:
            if topic.id == topic_id:
                return unit, topic
    return None


def get_all_topics() -> list[tuple[Unit, Topic]]:
    """Get all topics with their parent units."""
    result = []
    for unit in UNITS:
        for topic in unit.topics:
            result.append((unit, topic))
    return result


def format_topic_display(unit: Unit, topic: Topic) -> str:
    """Format a topic for display in the CLI."""
    bc_tag = " [BC]" if topic.bc_only else ""
    return f"{topic.id} {topic.name}{bc_tag}"


def format_unit_display(unit: Unit) -> str:
    """Format a unit for display in the CLI."""
    bc_tag = " [BC Only]" if unit.bc_only else ""
    return f"Unit {unit.number}: {unit.name}{bc_tag}"
