import argparse
import os
import sys
import io
import hashlib
from pathlib import Path

# Add the project root to the Python path to allow importing app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.services.parser import document_service
from backend.app.services.embedding import embedding_service
from backend.app.services.storage_service import storage_service
from backend.app.services.vector_db import vector_db_service, KBType

def process_pdf(file_path: Path):
    """
    Processes a single PDF file: extracts content, uploads to S3, creates embeddings,
    and upserts to the vector database as part of the Global Knowledge Base (GKB).
    """
    print(f"\n--- Processing PDF: {file_path.name} ---")

    if not storage_service.is_enabled:
        print("ERROR: Storage service is not configured. Cannot upload files. Aborting.")
        return

    try:
        with open(file_path, "rb") as f:
            file_stream = io.BytesIO(f.read())

        # 1. Extract content from PDF
        text, images = document_service.extract_from_pdf(file_stream)
        print(f"Extracted {len(text)} characters of text and {len(images)} images.")

        # 2. Process and ingest the extracted text
        if text.strip():
            text_hash = hashlib.md5(text.encode()).hexdigest()
            text_object_name = f"text/gkb/{text_hash}.txt"
            s3_uri = f"s3://{storage_service.bucket_name}/{text_object_name}"

            # Upload text to S3
            storage_service.upload_file(io.BytesIO(text.encode('utf-8')), text_object_name)

            # Create embedding and upsert to Pinecone
            print(f"Ingesting text content (S3 URI: {s3_uri})")
            text_embedding = embedding_service.create_text_embedding(text)
            vector_db_service.upsert(
                vector=text_embedding,
                kb_type=KBType.GKB,
                source_type="text",
                source_id=s3_uri,
                context_id="gkb_default" # GKB items belong to a default context
            )

        # 3. Process and ingest each extracted image
        for i, img in enumerate(images):
            img_hash = hashlib.md5(img.tobytes()).hexdigest()
            # Use the original PDF name to provide more context in the filename
            img_object_name = f"images/gkb/{file_path.stem}_{i}_{img_hash}.png"
            s3_uri = f"s3://{storage_service.bucket_name}/{img_object_name}"

            # Convert PIL image to byte stream for uploading
            with io.BytesIO() as img_stream:
                img.save(img_stream, format='PNG')
                img_stream.seek(0)
                storage_service.upload_file(img_stream, img_object_name)

            # Create embedding and upsert to Pinecone
            print(f"Ingesting image {i+1} (S3 URI: {s3_uri})")
            image_embedding = embedding_service.create_image_embedding(img)
            vector_db_service.upsert(
                vector=image_embedding,
                kb_type=KBType.GKB,
                source_type="image",
                source_id=s3_uri,
                context_id="gkb_default"
            )
        
        print(f"Successfully processed and ingested {file_path.name}")
    except (OSError, ValueError, RuntimeError) as e:
        print(f"ERROR: Failed to process {file_path.name}. Reason: {e}")

def main():
    """
    Main function to parse arguments and start the ingestion process.
    """
    parser = argparse.ArgumentParser(description="Bulk ingest documents into the Global Knowledge Base (GKB).")
    parser.add_argument("path", type=str, help="Path to a single PDF file or a directory containing PDFs.")
    args = parser.parse_args()

    source_path = Path(args.path)
    if not source_path.exists():
        print(f"Error: The path '{source_path}' does not exist.")
        sys.exit(1)

    pdf_files = []
    if source_path.is_dir():
        print(f"Scanning directory '{source_path}' for PDF files...")
        pdf_files.extend(source_path.rglob("*.pdf"))
    elif source_path.is_file() and source_path.suffix.lower() == ".pdf":
        pdf_files.append(source_path)
    
    if not pdf_files:
        print("No PDF files found to process.")
        return

    print(f"Found {len(pdf_files)} PDF file(s) to ingest.")
    for pdf_file in pdf_files:
        process_pdf(pdf_file)

if __name__ == "__main__":
    main()