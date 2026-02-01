"""PDF compilation from LaTeX."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


def compile_pdf(latex_content: str, output_dir: Path | None = None) -> Path:
    """Compile LaTeX content to PDF.

    Args:
        latex_content: The LaTeX document content
        output_dir: Directory to save the PDF. Defaults to current directory.

    Returns:
        Path to the generated PDF file

    Raises:
        RuntimeError: If pdflatex is not available or compilation fails
    """
    if output_dir is None:
        output_dir = Path.cwd()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base_name = f"BC_Practice_{timestamp}"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        tex_file = tmpdir / f"{base_name}.tex"

        # Write LaTeX content
        tex_file.write_text(latex_content, encoding="utf-8")

        # Try to compile with pdflatex
        try:
            # Run twice for proper references
            for _ in range(2):
                result = subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        "-output-directory", str(tmpdir),
                        str(tex_file),
                    ],
                    capture_output=True,
                    timeout=60,
                    # Don't use text=True to avoid encoding issues
                )

            pdf_file = tmpdir / f"{base_name}.pdf"

            if pdf_file.exists():
                # Move to output directory
                final_path = output_dir / f"{base_name}.pdf"
                shutil.move(str(pdf_file), str(final_path))
                return final_path
            else:
                # Check log for errors
                log_file = tmpdir / f"{base_name}.log"
                if log_file.exists():
                    try:
                        log_content = log_file.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        log_content = log_file.read_text(encoding="latin-1")
                    # Find error lines
                    errors = [
                        line for line in log_content.split("\n")
                        if line.startswith("!")
                    ]
                    if errors:
                        raise RuntimeError(
                            f"LaTeX compilation failed:\n" + "\n".join(errors[:5])
                        )
                raise RuntimeError("PDF compilation failed - no output file generated")

        except FileNotFoundError:
            raise RuntimeError(
                "pdflatex not found. Please install a LaTeX distribution:\n"
                "  macOS: brew install --cask mactex\n"
                "  Ubuntu: sudo apt install texlive-full\n"
                "  Windows: Install MiKTeX from https://miktex.org/"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("PDF compilation timed out after 60 seconds")


def check_pdflatex_available() -> bool:
    """Check if pdflatex is available on the system."""
    try:
        subprocess.run(
            ["pdflatex", "--version"],
            capture_output=True,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
