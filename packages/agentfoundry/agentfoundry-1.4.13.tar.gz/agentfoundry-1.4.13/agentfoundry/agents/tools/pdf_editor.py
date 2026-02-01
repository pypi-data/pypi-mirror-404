"""PDF editing tool with optional PyMuPDF dependency.

If PyMuPDF is not installed, the tool still registers but returns a clear
message when invoked instead of failing import at load time.
"""

from typing import Optional, List

try:  # Prefer canonical import name
    import fitz as pymupdf  # type: ignore
except Exception:  # pragma: no cover
    try:
        import pymupdf  # type: ignore
    except Exception:
        pymupdf = None  # lazily checked at call time
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


class CreatePDFInput(BaseModel):
    """Input schema for the pdf_generator tool."""
    input_path: str = Field(..., description="The source PDF path (str)")
    output_path: str = Field(..., description="The destination PDF path (str)")
    replacements: Optional[dict] = Field(default=None, description="The dict mapping original text to new text")
    highlight_texts: Optional[List[str]] = Field(
        default=None,
        description="List of strings to highlight in yellow instead of redacting"
    )


def redact_and_replace_or_highlight_pdf(input_path: str, output_path: str, replacements: Optional[dict] = None, highlight_texts: Optional[List[str]] = None):
    if pymupdf is None:
        return (
            "PyMuPDF (fitz) is not installed. Install with 'pip install pymupdf' "
            "to enable PDF redaction/highlighting."
        )
    counts = {
        "replacements": {},
        "highlights": {}
    }
    if replacements is None:
        replacements = {}
    if highlight_texts is None:
        highlight_texts = []
    for txt in highlight_texts:
        counts['highlights'][txt] = 0
    try:
        doc = pymupdf.open(input_path)
        for page in doc:
            overlays = []
            for find_text, replace_text in replacements.items():
                rects = page.search_for(find_text)
                for r in rects:
                    page.add_redact_annot(r, fill=(1,1,1))
                    overlays.append((r, replace_text))
                    if find_text in counts['replacements']:
                        counts['replacements'][find_text] += 1
                    else:
                        counts['replacements'][find_text] = 1
            if overlays:
                page.apply_redactions()
            # Now overlay replacements with dynamic sizing
            for rect, text in overlays:
                # 1) pick a “max” font size based on the box height
                max_fs = rect.height * 0.6
                # 2) measure text width at max_fs
                font = pymupdf.Font("helv")
                text_w = font.text_length(text, max_fs)
                # 3) scale down if it doesn’t fit
                if text_w > rect.width:
                    fs = max_fs * (rect.width / text_w)
                else:
                    fs = max_fs
                y_off = rect.y1 - 0.25*(rect.y1 - rect.y0)
                # 4) insert at top‐left
                page.insert_text(
                    (rect.x0, y_off),
                    text,
                    fontname="helv",
                    fontsize=fs,
                    color=(0, 0, 0),  # black
                )
            if highlight_texts:
                for txt in highlight_texts:
                    text = txt.replace("$", "")
                    for r in page.search_for(text):
                        annot = page.add_highlight_annot(r)
                        # set the fill/stroke to yellow
                        annot.set_colors(stroke=(1, 1, 0), fill=(1, 1, 0))
                        annot.update()
                        if txt in counts['highlights']:
                            counts["highlights"][txt] += 1
                        else:
                            counts["highlights"][txt] = 1
        doc.save(output_path)
        doc.close()
        return counts
    except Exception as err:
        error = f"Error editing PDF: {err}"
        print(error)
        return error


pdf_redactor_tool = StructuredTool(
    name="pdf_editor",
    func=redact_and_replace_or_highlight_pdf,
    description=(
        "Redacts+replaces text and/or highlights text in a PDF. If using the highlighting feature, ensure that the "
        "highlighted text exists inside the PDF."
        "Input must be a JSON string with keys:\n"
        " - input_path: source PDF path\n"
        " - output_path: destination PDF path\n"
        " - replacements: dict of original→new text (optional)\n"
        " - highlight_texts: list of strings to highlight in yellow (optional)\n\n"
        "Returns a dict with counts for 'replaced' and 'highlighted'."
    ),
    args_schema=CreatePDFInput
)
