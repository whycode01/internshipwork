from io import BytesIO
from PyPDF2 import PdfReader

def parse_pdf(content: bytes) -> str:
    """
    Extract all text from a PDF file and return as a single cleaned string.
    Ensures no duplicate lines/questions.
    """
    reader = PdfReader(BytesIO(content))
    text_set = set()
    combined_text = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            for line in page_text.splitlines():
                clean_line = line.strip()
                if clean_line and clean_line not in text_set:
                    text_set.add(clean_line)
                    combined_text.append(clean_line)

    return "\n".join(combined_text)
