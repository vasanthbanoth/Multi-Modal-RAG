from .embedding import EmbeddingService
from .vector_db import VectorDBService, KBType
from .storage_service import StorageService
from .llm_gen import GenerativeService
from PIL import Image
import logging
from urllib.parse import urlparse

class RAGPipelineService:
    """
    Orchestrates the entire RAG workflow, from query to final answer.
    """
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_db_service: VectorDBService,
        storage_service: StorageService,
        generative_service: GenerativeService,
    ):
        self.embedding_service = embedding_service
        self.vector_db_service = vector_db_service
        self.storage_service = storage_service
        self.generative_service = generative_service

    def run_pipeline(
        self, query: str, kb_type: KBType, context_id: str | None = None
    ) -> dict:
        """
        Executes the full RAG pipeline.

        1. Creates an embedding for the user's query.
        2. Queries the vector DB for relevant context (both text and images).
        3. Retrieves the actual content of the context from cloud storage.
        4. Sends the query and retrieved context to an LLM to generate a final answer.
        """
        # 1. Create query embedding
        logging.info("Running RAG pipeline for query: '%s'", query)
        query_vector = self.embedding_service.create_text_embedding(query)

        # 2. Query vector DB for context
        search_results = self.vector_db_service.query(
            query_vector, kb_type, context_id, top_k=3
        )

        # 3. Retrieve content from storage and format for LLM
        context_for_llm = []
        if not self.storage_service.is_enabled:
            logging.warning("Storage service is disabled, cannot retrieve context from S3.")
        else:
            for match in search_results:
                metadata = match.get("metadata", {})
                source_id = metadata.get("source_id")
                source_type = metadata.get("source_type")

                if not source_id or not source_id.startswith("s3://"):
                    continue

                # Parse the S3 URI to get the object key
                s3_path = urlparse(source_id).path.lstrip('/')
                file_stream = self.storage_service.download_file_as_stream(s3_path)

                if file_stream:
                    if source_type == "image":
                        pil_image = Image.open(file_stream)
                        context_for_llm.append({"type": "image", "content": pil_image})
                    elif source_type == "text":
                        text_content = file_stream.read().decode("utf-8")
                        context_for_llm.append({"type": "text", "content": text_content})

        # 4. Generate final answer
        final_answer = self.generative_service.generate_response(query, context_for_llm)

        return {
            "query": query,
            "answer": final_answer,
            "retrieved_context": [
                {"id": m["id"], "score": m["score"], "metadata": m.get("metadata", {})}
                for m in search_results
            ],
        }