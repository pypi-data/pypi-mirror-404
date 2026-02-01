import markdown
import pdfkit
import tempfile
import os
import base64
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing import Optional


class CreatePDFInput(BaseModel):
    """Input schema for the pdf_generator tool."""
    md: str = Field(..., description="The Markdown text to convert")
    image_paths: Optional[List[str]] = Field(None, description="The Optional list of file paths to PNG/JPEG images to embed")


def pdf_generator(md: str, image_paths: List[str] = None) -> str:
    """
    Generate a PDF from markdown and embed optional plots.

    :param md: Markdown text to convert.
    :param image_paths: Optional list of file paths to PNG/JPEG images to embed.
    :return: Path to the generated PDF.
    """
    try:
        # Convert markdown to HTML (including tables)
        html = markdown.markdown(md, extensions=['tables'])

        # Embed each image as a base64-encoded data URI
        if image_paths:
            for img_path in image_paths:
                if not os.path.isfile(img_path):
                    continue
                ext = os.path.splitext(img_path)[1].lower().lstrip('.')
                mime = 'jpeg' if ext in ('jpg', 'jpeg') else 'png'
                with open(img_path, 'rb') as img_f:
                    b64 = base64.b64encode(img_f.read()).decode('utf-8')
                html += f'<p><img src="data:image/{mime};base64,{b64}" /></p>'

        # Render HTML to PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdfkit.from_string(
                html,
                tmp.name,
                options={"enable-local-file-access": None}
            )
            return tmp.name
    except Exception as e:
        return f"Error generating PDF: {e}"


pdf_creator_tool = StructuredTool(
    name="pdf_file_creator",
    func=pdf_generator,
    description=(
        "Creates a PDF file from markdown text, optionally embedding PNG/JPEG plots. "
        "Usage: pdf_generator(md, image_paths=[...]) returns the path to the generated PDF."
    ),
    args_schema=CreatePDFInput
)

# Alias tool name expected by allowed tool list
pdf_creator = StructuredTool.from_function(
    func=pdf_generator,
    name="pdf_creator",
    description="Create a PDF from markdown text, optionally embedding PNG/JPEG images.",
    args_schema=CreatePDFInput,
)
