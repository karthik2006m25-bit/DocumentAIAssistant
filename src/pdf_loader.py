import pymupdf
from docx import Document
from pptx import Presentation
from io import BytesIO
from pathlib import Path


# ==========================================
# PDF
# ==========================================

def extract_text_from_pdf(file):
    """
    Extract text from a PDF while preserving
    page numbers.

    Supports:
    - File paths
    - Streamlit UploadedFile
    """

    if hasattr(file, "getvalue"):
        file = BytesIO(file.getvalue())

    doc = pymupdf.open(file)

    pages = []

    for page_number, page in enumerate(doc, start=1):

        text = page.get_text("text").strip()

        if text:
            pages.append(
                f"[Page {page_number}]\n{text}"
            )

    doc.close()

    return "\n\n".join(pages)


# ==========================================
# DOCX
# ==========================================

def extract_text_from_docx(file):
    """
    Extract text from a DOCX file.

    Includes:
    - Paragraphs
    - Tables

    Supports:
    - File paths
    - Streamlit UploadedFile
    """

    if hasattr(file, "getvalue"):
        file = BytesIO(file.getvalue())

    document = Document(file)

    sections = []

    # ------------------------------------------
    # Paragraphs
    # ------------------------------------------

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if text:
            sections.append(text)

    # ------------------------------------------
    # Tables
    # ------------------------------------------

    for table_number, table in enumerate(
        document.tables,
        start=1
    ):

        sections.append(
            f"[Table {table_number}]"
        )

        for row in table.rows:

            row_text = []

            for cell in row.cells:

                cell_text = cell.text.strip()

                row_text.append(cell_text)

            sections.append(
                " | ".join(row_text)
            )

    return "\n\n".join(sections)


# ==========================================
# PPTX
# ==========================================

def extract_text_from_pptx(file):
    """
    Extract text from PowerPoint slides.

    Preserves slide numbers.

    Supports:
    - File paths
    - Streamlit UploadedFile
    """

    if hasattr(file, "getvalue"):
        file = BytesIO(file.getvalue())

    presentation = Presentation(file)

    slides = []

    for slide_number, slide in enumerate(
        presentation.slides,
        start=1
    ):

        slide_text = []

        for shape in slide.shapes:

            if hasattr(shape, "text"):

                text = shape.text.strip()

                if text:
                    slide_text.append(text)

        if slide_text:

            slides.append(
                f"[Slide {slide_number}]\n"
                + "\n".join(slide_text)
            )

    return "\n\n".join(slides)


# ==========================================
# GENERAL DOCUMENT LOADER
# ==========================================

def extract_text(file):
    """
    Automatically detect the file type
    and extract its text.

    Supports:
    - PDF
    - DOCX
    - PPTX
    """

    # Get the filename
    if hasattr(file, "name"):
        filename = file.name.lower()
    else:
        filename = str(file).lower()

    # ------------------------------------------
    # PDF
    # ------------------------------------------

    if filename.endswith(".pdf"):

        return extract_text_from_pdf(file)

    # ------------------------------------------
    # DOCX
    # ------------------------------------------

    elif filename.endswith(".docx"):

        return extract_text_from_docx(file)

    # ------------------------------------------
    # PPTX
    # ------------------------------------------

    elif filename.endswith(".pptx"):

        return extract_text_from_pptx(file)

    # ------------------------------------------
    # Unsupported
    # ------------------------------------------

    else:

        raise ValueError(
            "Unsupported file type. "
            "Supported formats: PDF, DOCX, PPTX"
        )
