"""AI-powered problem generation using OpenAI or Anthropic."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .config import Config, get_problem_count
from .topics import Topic, Unit
from .latex import Problem, Section
from .graphs import generate_graph


@dataclass
class GenerationRequest:
    topics: list[tuple[Unit, Topic]]
    length: str  # quick, medium, full


# Technique categories for organizing problems into sections
TECHNIQUE_SECTIONS = {
    "riemann_sums": {
        "title": "Riemann Sums & Approximations",
        "keywords": ["riemann", "approximat", "trapezoid", "midpoint", "left sum", "right sum"],
        "topic_ids": ["6.1", "6.2", "6.3"],
    },
    "ftc": {
        "title": "Fundamental Theorem of Calculus",
        "keywords": ["fundamental theorem", "accumulation", "F(x)", "F'(x)", "derivative of integral"],
        "topic_ids": ["6.4", "6.5", "6.6", "6.7"],
    },
    "antiderivatives": {
        "title": "Antiderivatives & Basic Integration",
        "keywords": ["antiderivative", "indefinite integral", "find the integral", "evaluate"],
        "topic_ids": ["6.8", "6.10"],
    },
    "u_substitution": {
        "title": "Integration by Substitution",
        "keywords": ["substitution", "u-sub", "u ="],
        "topic_ids": ["6.9"],
    },
    "integration_by_parts": {
        "title": "Integration by Parts",
        "keywords": ["by parts", "tabular"],
        "topic_ids": ["6.11"],
    },
    "partial_fractions": {
        "title": "Partial Fraction Decomposition",
        "keywords": ["partial fraction"],
        "topic_ids": ["6.12"],
    },
    "improper_integrals": {
        "title": "Improper Integrals",
        "keywords": ["improper", "converge", "diverge", "infinity", "∞"],
        "topic_ids": ["6.13"],
    },
}


SYSTEM_PROMPT = """You are an expert AP Calculus BC teacher creating practice problems. Generate high-quality, AP-exam-style problems that test understanding of the specified topics.

Requirements:
1. All problems must be FREE RESPONSE (no multiple choice)
2. Use proper LaTeX math notation (e.g., $\\int$, $\\frac{d}{dx}$, $\\lim_{x \\to a}$)
3. Include point values that reflect difficulty (2-6 points per problem or part)
4. Vary difficulty: ~30% straightforward, ~50% moderate, ~20% challenging
5. Include multi-part problems where appropriate (labeled a, b, c, etc.)
6. IMPORTANT: For problems involving graphs, you MUST include complete TikZ code

Output format: Return a JSON object with a "sections" array. Each section groups problems by technique:

{
  "sections": [
    {
      "title": "Section A: Riemann Sums & Approximations",
      "problems": [...]
    },
    {
      "title": "Section B: Fundamental Theorem of Calculus",
      "problems": [...]
    }
  ]
}

Each problem should have:
- "title": Brief description of the problem type
- "points": Total points for the problem
- "content": The problem statement in LaTeX (this goes in a box header)
- "tikz_graph": Optional TikZ code for graphs (see example below)
- "parts": Optional array of parts, each with:
  - "label": "a", "b", "c", etc.
  - "content": The part's question in LaTeX
  - "points": Points for this part
  - "workspace": Suggested workspace height (e.g., "5cm", "7cm")

GRAPHS - Use structured "graph" field instead of raw TikZ. Available graph types:

1. PIECEWISE LINEAR (for f(t) graphs, velocity graphs, accumulation problems):
{
  "graph": {
    "type": "piecewise",
    "points": [[0, 2], [2, 2], [4, -2], [6, -2]],
    "xlabel": "t",
    "ylabel": "f(t)"
  }
}

2. SLOPE FIELD:
{
  "graph": {
    "type": "slope_field",
    "equation": "x - y",
    "x_range": [-3, 3],
    "y_range": [-3, 3],
    "filled": true
  }
}
- Use "filled": true to show actual slope segments (for analysis questions)
- Use "filled": false for empty grid (for "sketch the slope field" questions)

3. VELOCITY GRAPH:
{
  "graph": {
    "type": "velocity",
    "points": [[0, 3], [2, 3], [5, -3], [8, 0]]
  }
}

4. ACCUMULATION GRAPH:
{
  "graph": {
    "type": "accumulation",
    "f_points": [[0, 2], [2, 2], [4, 0], [6, -2], [8, 0]]
  }
}

5. NO GRAPH (describe in text instead):
{
  "graph": null,
  "content": "The graph of f consists of line segments connecting (0,2), (2,0), and (4,-1)."
}

IMPORTANT: Always use "graph" field with structured data, NOT "tikz_graph" with raw code.

Section titles should be SHORT (max 30 chars after "Section X: "):
- "Section A: Riemann Sums"
- "Section B: FTC"
- "Section C: Antiderivatives"
- "Section D: U-Substitution"
- "Section E: Integration by Parts"
- "Section F: Partial Fractions"
- "Section G: Improper Integrals"

Order sections logically (e.g., Riemann Sums before FTC, basic integration before advanced techniques).

Important:
- Make problems realistic and exam-appropriate
- Ensure mathematical correctness
- Balance computational and conceptual questions
- Use contexts (physics, economics, etc.) where appropriate
- Include at least one graph-based problem if FTC or accumulation topics are selected
- Distribute problems evenly across selected topics"""


def build_user_prompt(topics: list[tuple[Unit, Topic]], problem_count: int) -> str:
    """Build the user prompt for problem generation."""
    topic_list = []
    for unit, topic in topics:
        bc_tag = " [BC Only]" if topic.bc_only else ""
        topic_list.append(f"- {topic.id} {topic.name}{bc_tag} (Unit {unit.number}: {unit.name})")

    topics_str = "\n".join(topic_list)

    # Determine which sections to include based on topics
    section_hints = []
    topic_ids = [t.id for _, t in topics]

    if any(tid in ["6.1", "6.2", "6.3"] for tid in topic_ids):
        section_hints.append("Riemann Sums & Approximations")
    if any(tid in ["6.4", "6.5", "6.6", "6.7"] for tid in topic_ids):
        section_hints.append("Fundamental Theorem of Calculus (include a graph-based problem)")
    if any(tid in ["6.8", "6.10"] for tid in topic_ids):
        section_hints.append("Antiderivatives & Basic Integration")
    if any(tid == "6.9" for tid in topic_ids):
        section_hints.append("Integration by Substitution")
    if any(tid == "6.11" for tid in topic_ids):
        section_hints.append("Integration by Parts [BC]")
    if any(tid == "6.12" for tid in topic_ids):
        section_hints.append("Partial Fraction Decomposition [BC]")
    if any(tid == "6.13" for tid in topic_ids):
        section_hints.append("Improper Integrals [BC]")

    sections_hint = ""
    if section_hints:
        sections_hint = f"\n\nOrganize problems into these sections:\n" + "\n".join(f"- {s}" for s in section_hints)

    return f"""Generate {problem_count} AP BC Calculus practice problems covering these topics:

{topics_str}
{sections_hint}

Requirements:
- Distribute problems across the selected topics
- Include a mix of computational and conceptual problems
- All problems should be free response with clear point values
- Total points should be approximately {problem_count * 4} to {problem_count * 5}
- Group problems into sections by technique (Section A, Section B, etc.)
- Include TikZ graph code for any problems that involve graphs

Return ONLY the JSON object with sections, no other text."""


def parse_ai_response(content: str) -> dict:
    """Parse the AI response to extract sections and problems."""
    # Try to parse as JSON directly
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "sections" in data:
            return data
        elif isinstance(data, dict) and "problems" in data:
            # Old format - wrap in single section
            return {"sections": [{"title": "Practice Problems", "problems": data["problems"]}]}
        elif isinstance(data, list):
            # Direct array - wrap in single section
            return {"sections": [{"title": "Practice Problems", "problems": data}]}
    except json.JSONDecodeError:
        pass

    # Try to extract JSON object from markdown
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if "sections" in data:
                return data
        except json.JSONDecodeError:
            pass

    # Try to extract JSON array from markdown
    json_match = re.search(r'\[[\s\S]*\]', content)
    if json_match:
        try:
            problems = json.loads(json_match.group())
            return {"sections": [{"title": "Practice Problems", "problems": problems}]}
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse JSON from response")


async def generate_with_openai(
    api_key: str,
    topics: list[tuple[Unit, Topic]],
    problem_count: int,
) -> dict:
    """Generate problems using OpenAI API."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(topics, problem_count)},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    return parse_ai_response(content)


async def generate_with_anthropic(
    api_key: str,
    topics: list[tuple[Unit, Topic]],
    problem_count: int,
) -> dict:
    """Generate problems using Anthropic API."""
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=api_key)

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=12000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": build_user_prompt(topics, problem_count)},
        ],
    )

    content = response.content[0].text
    return parse_ai_response(content)


async def generate_problems(
    config: Config,
    topics: list[tuple[Unit, Topic]],
    length: str,
) -> list[Section]:
    """Generate problems using the configured AI provider."""
    problem_count = get_problem_count(length)
    api_key = config.get_api_key()

    if not api_key:
        raise ValueError("No API key configured")

    # Generate raw response from AI
    if config.provider == "openai":
        raw_response = await generate_with_openai(api_key, topics, problem_count)
    elif config.provider == "anthropic":
        raw_response = await generate_with_anthropic(api_key, topics, problem_count)
    else:
        raise ValueError(f"Unknown provider: {config.provider}")

    # Convert to our data structures
    sections = []
    problem_number = 1

    for raw_section in raw_response.get("sections", []):
        problems = []

        for raw in raw_section.get("problems", []):
            parts = None
            if raw.get("parts"):
                parts = [
                    {
                        "label": p["label"],
                        "content": p["content"],
                        "points": p["points"],
                        "workspace": p.get("workspace", "5cm"),
                    }
                    for p in raw["parts"]
                ]

            # Handle graph generation from structured data
            tikz_graph = None

            if raw.get("graph") and isinstance(raw["graph"], dict):
                graph_data = raw["graph"]
                graph_type = graph_data.get("type", "")
                # Build kwargs from graph data, excluding "type"
                kwargs = {k: v for k, v in graph_data.items() if k != "type"}
                # Convert list points to tuples if needed
                if "points" in kwargs and kwargs["points"]:
                    kwargs["points"] = [tuple(p) for p in kwargs["points"]]
                if "f_points" in kwargs and kwargs["f_points"]:
                    kwargs["f_points"] = [tuple(p) for p in kwargs["f_points"]]
                if "v_points" in kwargs and kwargs["v_points"]:
                    kwargs["v_points"] = [tuple(p) for p in kwargs["v_points"]]
                # Convert x_range/y_range from list to tuple
                if "x_range" in kwargs and kwargs["x_range"]:
                    kwargs["x_range"] = tuple(kwargs["x_range"])
                if "y_range" in kwargs and kwargs["y_range"]:
                    kwargs["y_range"] = tuple(kwargs["y_range"])
                # Generate TikZ from template
                try:
                    tikz_graph = generate_graph(graph_type, **kwargs)
                except Exception:
                    pass  # Skip graph on error
            elif raw.get("tikz_graph"):
                # Fallback to raw tikz if provided (legacy)
                tikz_graph = raw["tikz_graph"]

            problems.append(Problem(
                number=problem_number,
                title=raw.get("title", f"Problem {problem_number}"),
                points=raw.get("points", 4),
                content=raw.get("content", ""),
                parts=parts,
                tikz_graph=tikz_graph,
            ))
            problem_number += 1

        if problems:
            total_points = sum(p.points for p in problems)
            sections.append(Section(
                title=raw_section.get("title", "Practice Problems"),
                subtitle=None,
                points=total_points,
                problems=problems,
            ))

    # Fallback if no sections were created
    if not sections:
        sections.append(Section(
            title="Practice Problems",
            subtitle=None,
            points=0,
            problems=[],
        ))

    return sections


def generate_topics_header(topics: list[tuple[Unit, Topic]]) -> str:
    """Generate a short header describing the topics."""
    units = set(unit.number for unit, _ in topics)
    if len(units) == 1:
        unit_num = list(units)[0]
        return f"Unit {unit_num}"
    elif len(units) <= 3:
        return "Units " + ", ".join(str(u) for u in sorted(units))
    else:
        return "Mixed Topics"


def generate_topics_subtitle(topics: list[tuple[Unit, Topic]]) -> str:
    """Generate a clean subtitle describing the unit focus."""
    units = {}
    for unit, _ in topics:
        if unit.number not in units:
            units[unit.number] = unit.name

    if len(units) == 1:
        # Single unit - use the unit name
        unit_num = list(units.keys())[0]
        unit_name = units[unit_num]
        return f"Unit {unit_num}: {unit_name}"
    elif len(units) <= 3:
        # Multiple units - list them
        unit_strs = [f"Unit {num}" for num in sorted(units.keys())]
        return " \\& ".join(unit_strs)
    else:
        # Many units
        return "Comprehensive Review"
