from langchain_core.tools import Tool
from PyPDF2 import PdfReader
import io
import re
import unicodedata
import requests


def clean_text(text: str) -> str:
    # Remove non-ASCII characters (non-English)
    text = ''.join([char for char in text if char.isascii()])
    # Remove escape sequences like \x03
    text = re.sub(r'\\x[0-9A-Fa-f]{2}', '', text)
    # Normalize Unicode text (NFKD form)
    text = unicodedata.normalize('NFKD', text)
    # Remove extra spaces
    return re.sub(r'\s+', ' ', text).strip()


def ingest_document(source: str) -> str:
    """
    Ingest document text from a URL or a local file.
    Supports .pdf (via PyPDF2) or plain text files.
    """
    # If a file-like object is passed (e.g. Flask FileStorage)
    if hasattr(source, 'read'):
        filename = getattr(source, 'filename', '') or ''
        data = source.read()
        # Handle PDF streams
        if filename.lower().endswith('.pdf'):
            text = ''
            reader = PdfReader(io.BytesIO(data))
            for page in reader.pages:
                page_text = page.extract_text() or ''
                text += page_text + "\n"
            return clean_text(text)
        # Assume plain text
        try:
            text = data.decode('utf-8')
        except Exception:
            text = str(data)
        return clean_text(text)
    # String source (URL or file path)
    if isinstance(source, str) and source.startswith("http"):
        response = requests.get(source)
        response.raise_for_status()
        return clean_text(response.text)
    if isinstance(source, str) and source.lower().endswith(".pdf"):
        text = ''
        reader = PdfReader(source)
        for page in reader.pages:
            page_text = page.extract_text() or ''
            text += page_text + "\n"
        return clean_text(text)
    # local file path as string
    if isinstance(source, str):
        with open(source, 'r', encoding='utf-8') as f:
            return clean_text(f.read())
    # Fallback: stringify
    return clean_text(str(source))


python_document_reader = Tool(
    name="document_reader",
    func=ingest_document,
    description=(
        "This tool takes in a string path to a file or URL, and will try to open the file or source and return the "
        "contents within it after doing some cleaning. This function supports PDFs and plain text files as well."
    )
)