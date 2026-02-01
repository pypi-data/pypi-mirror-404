"""Text formatting utilities for cleaning HTML and wrapping text."""

import re

from bs4 import BeautifulSoup


def clean_html(html_content: str) -> str:
    """Remove HTML tags and clean content while preserving structure.

    Args:
        html_content: HTML string to clean

    Returns:
        Cleaned text with preserved structure
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Replace common HTML elements with readable text
    for br in soup.find_all("br"):
        br.replace_with("\n")

    for p in soup.find_all("p"):
        p.insert_after("\n\n")

    for li in soup.find_all("li"):
        li.insert_before("  • ")
        li.insert_after("\n")

    for pre in soup.find_all("pre"):
        pre.insert_before("\n")
        pre.insert_after("\n")

    # Get text with proper spacing
    text = soup.get_text()

    # Clean up excessive whitespace while preserving intentional line breaks
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Remove excessive blank lines (more than 2 consecutive)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def wrap_text(text: str, width: int = 78) -> str:
    """Wrap text to specified width while preserving structure.

    Args:
        text: Text to wrap
        width: Maximum line width (default: 78)

    Returns:
        Text wrapped to specified width
    """
    lines = text.split("\n")
    wrapped_lines = []

    for line in lines:
        if not line.strip():
            wrapped_lines.append("")
            continue

        # Don't wrap lines that start with bullet points or are code-like
        if (
            line.strip().startswith("•")
            or line.strip().startswith("-")
            or line.strip().startswith("*")
        ):
            wrapped_lines.append(line)
            continue

        # Don't wrap lines that look like code (indented or have special chars)
        if line.startswith("    ") or line.startswith("\t"):
            wrapped_lines.append(line)
            continue

        # Wrap long lines
        words = line.split()
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > width and current_line:
                wrapped_lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length
            else:
                current_line.append(word)
                current_length += word_length

        if current_line:
            wrapped_lines.append(" ".join(current_line))

    return "\n".join(wrapped_lines)
