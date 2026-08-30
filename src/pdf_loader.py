import pymupdf
from docx import Document
from pptx import Presentation


# ==========================================
# PDF
# ==========================================

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF while preserving
    page numbers.
    """

    doc = pymupdf.open(file_path)

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

def extract_text_from_docx(file_path):
    """
    Extract text from a DOCX file.
    Includes paragraphs and tables.
    """

    document = Document(file_path)

    sections = []

    # -------------------------------
    # Paragraphs
    # -------------------------------

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if text:
            sections.append(text)

    # -------------------------------
    # Tables
    # -------------------------------

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

def extract_text_from_pptx(file_path):
    """
    Extract text from PowerPoint slides.
    Preserves slide numbers.
    """

    presentation = Presentation(file_path)

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

def extract_text(file_path):
    """
    Automatically detect the file type
    and extract its text.
    """

    file_path = str(file_path).lower()

    if file_path.endswith(".pdf"):

        return extract_text_from_pdf(file_path)

    elif file_path.endswith(".docx"):

        return extract_text_from_docx(file_path)

    elif file_path.endswith(".pptx"):

        return extract_text_from_pptx(file_path)

    else:

        raise ValueError(
            "Unsupported file type. "
            "Supported formats: PDF, DOCX, PPTX"
        )