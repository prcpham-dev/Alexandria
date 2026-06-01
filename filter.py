import re
import os
from pathlib import Path
from docx import Document
from docx.shared import Pt
from copy import deepcopy
import copy

BASE_DIR   = Path(__file__).parent
INPUT_DIR  = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

_STRIP_PREFIX = re.compile(
    r"^"
    r"(?:"
        r"(?:\[?\d+\]?[\.\):\-]?\s*)"
        r"|"
        r"(?:\d{1,2}:\d{2}(?::\d{2})?\s*)"
    r")+"
)

_SKIP_LINE = re.compile(
    r"^"
    r"(?:"
        r"\d{1,2}:\d{2}(?::\d{2})?"
        r"|"
        r"\d+\s+minutes?,\s*\d+\s+seconds?"
        r"|"
        r"\d+\s+hours?,\s*\d+\s+minutes?,\s*\d+\s+seconds?"
    r")\s*$"
)


def strip_prefix(text: str) -> str:
    """
    Remove leading number / timestamp prefixes from a line of text.
    """
    return _STRIP_PREFIX.sub("", text).strip()


def process_paragraphs(raw_lines: list[str]) -> list[str]:
    """
    Apply the merge/split logic to a list of raw text lines:
      - Lines that are pure timestamps or time labels are skipped entirely.
      - A line starting with a lowercase letter is joined to the previous paragraph.
      - A line starting with an uppercase letter starts a new paragraph,
        with a blank line inserted before it as a separator.
    Returns a list of strings where empty strings represent blank lines.
    """
    paragraphs: list[str] = []

    for raw in raw_lines:
        if _SKIP_LINE.match(raw.strip()):
            continue

        text = strip_prefix(raw).strip()

        if not text:
            continue

        first_char = text[0]

        if paragraphs and first_char.islower():
            paragraphs[-1] = paragraphs[-1].rstrip() + " " + text
        else:
            if paragraphs:
                paragraphs.append("")
            paragraphs.append(text)

    return paragraphs


def process_docx(src_path: Path, dst_path: Path) -> None:
    """
    Read a .docx file, run it through the filter, and save the result.
    """
    doc = Document(src_path)
    raw_lines = [p.text for p in doc.paragraphs if p.text.strip()]
    cleaned = process_paragraphs(raw_lines)
    new_doc = Document()

    try:
        style = doc.styles["Normal"]
        new_style = new_doc.styles["Normal"]
        new_style.font.name = style.font.name
        new_style.font.size = style.font.size
    except Exception:
        pass

    for para_text in cleaned:
        new_doc.add_paragraph(para_text)

    new_doc.save(dst_path)
    print(f"  done  {src_path.name}  ->  {dst_path.name}")


def main():
    """
    CLI entry point: process all .docx files found in the input folder.
    """
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    docx_files = list(INPUT_DIR.glob("*.docx"))

    if not docx_files:
        print("No .docx files found in the 'input' folder.")
        print(f"  -> Put your Word documents in: {INPUT_DIR}")
        return

    print(f"Found {len(docx_files)} file(s) to process...\n")

    for src in docx_files:
        dst = OUTPUT_DIR / (src.stem + "_filtered" + src.suffix)
        try:
            process_docx(src, dst)
        except Exception as exc:
            print(f"  error  {src.name}: {exc}")

    print(f"\nDone! Cleaned files are in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
