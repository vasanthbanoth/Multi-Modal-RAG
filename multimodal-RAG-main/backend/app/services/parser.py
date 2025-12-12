import fitz  # PyMuPDF
from PIL import Image
import io
from typing import Tuple, List

class DocumentService:
    """
    A utility service to open files (like PDFs) and extract their contents.
    """

    def extract_from_pdf(self, file_stream: io.BytesIO) -> Tuple[str, List[Image.Image]]:
        """
        Extracts all text and images from a PDF file stream.

        Args:
            file_stream: A byte stream of the PDF file.

        Returns:
            A tuple containing:
            - A string with all the extracted text.
            - A list of PIL.Image objects for all extracted images.
        """
        text_content = ""
        image_content = []

        # Open the PDF from the stream
        pdf_document = fitz.open(stream=file_stream, filetype="pdf")

        # Iterate through each page to extract text and images
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            
            # Extract text
            text_content += page.get_text("text") + "\n"

            # Extract images
            for img in page.get_images(full=True):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                pil_image = Image.open(io.BytesIO(image_bytes))
                image_content.append(pil_image)

        return text_content, image_content

# Create a single, reusable instance of the service
document_service = DocumentService()