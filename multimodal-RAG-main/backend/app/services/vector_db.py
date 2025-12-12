import logging
from backend.app.core.config import settings, Settings
from enum import Enum
import uuid
from typing import Dict, List, Any


# Try to import the real Pinecone client; if it's not available, provide
# a minimal in-memory adapter so the application can run without Pinecone
try:
    import pinecone as _pinecone  # type: ignore
except ImportError:
    _pinecone = None


class _InMemoryIndex:
    def __init__(self, name: str):
        self.name = name
        self._store: Dict[str, Dict[str, Any]] = {}

    def upsert(self, vectors: List[tuple]):
        for vid, vec, meta in vectors:
            self._store[vid] = {"vector": vec, "metadata": meta}

    def query(self, vector: List[float], filter_query: Dict[str, Any], top_k: int = 5, include_metadata: bool = False):
        # Very naive: return up to top_k stored items without real similarity scoring
        # Reference arguments to avoid unused-argument warnings
        _ = vector
        _ = include_metadata
        matches = []
        for vid, item in list(self._store.items())[:top_k]:
            # If a simple filter_query is provided, perform a minimal metadata match check
            if filter_query:
                meta = item.get("metadata", {})
                ok = True
                for k, v in filter_query.items():
                    if meta.get(k) != v:
                        ok = False
                        break
                if not ok:
                    continue

            matches.append({"id": vid, "score": 1.0, "metadata": item.get("metadata", {})})
        return {"matches": matches}


class _InMemoryPineconeAdapter:
    def __init__(self):
        self._indexes = set()
        self._index_objs: Dict[str, _InMemoryIndex] = {}

    def init(self, api_key: str, environment: str) -> None:
        # no-op for in-memory adapter
        _ = api_key
        _ = environment
        return None

    def list_indexes(self) -> List[str]:
        return list(self._indexes)

    def create_index(self, name: str, dimension: int, metric: str, metadata_config: Dict[str, Any]) -> None:
        # Keep signature compatible with real pinecone but only use the name
        _ = dimension
        _ = metric
        _ = metadata_config
        self._indexes.add(name)
        self._index_objs[name] = _InMemoryIndex(name)

    def Index(self, name: str) -> _InMemoryIndex:
        return self._index_objs.setdefault(name, _InMemoryIndex(name))


if _pinecone is None:
    _pinecone = _InMemoryPineconeAdapter()

class KBType(str, Enum):
    """Enumeration for Knowledge Base types."""
    GKB = "gkb"  # General Knowledge Base
    SKB = "skb"  # Specific Knowledge Base

class VectorDBService:
    """
    A service to manage all communications with the Pinecone vector database.
    Implements GKB/SKB logic using metadata filters.
    """
    def __init__(self, config: Settings):
        """
        Initializes the Pinecone client and ensures the index exists.
        Uses guarded attribute access for `pinecone` to avoid static-analysis complaints
        when stubs for the external library are missing.
        """
        logging.info("VectorDBService: Initializing Pinecone...")

        # Initialize pinecone client (use module-level `_pinecone` which may be
        # the real client, a new-style Pinecone instance, or an in-memory adapter)
        pinecone_client = None
        try:
            # New pinecone releases require creating a Pinecone() instance
            if hasattr(_pinecone, "Pinecone") and config.PINECONE_API_KEY:
                # Create a Pinecone client instance
                try:
                    pc = _pinecone.Pinecone(api_key=config.PINECONE_API_KEY)
                    pinecone_client = pc
                    logging.info("VectorDBService: Connected to real Pinecone client.")
                except Exception as init_err:
                    logging.warning(f"VectorDBService: Failed to initialize Pinecone client: {init_err}. Using in-memory fallback.")
                    pinecone_client = None
            elif config.PINECONE_API_KEY:
                # Older module-level API
                try:
                    _pinecone.init(api_key=config.PINECONE_API_KEY, environment=config.PINECONE_ENVIRONMENT)  # type: ignore[attr-defined]
                    pinecone_client = _pinecone
                    logging.info("VectorDBService: Connected to Pinecone with older API.")
                except Exception as init_err:
                    logging.warning(f"VectorDBService: Failed to initialize Pinecone (older API): {init_err}. Using in-memory fallback.")
                    pinecone_client = None
            else:
                logging.info("VectorDBService: No PINECONE_API_KEY provided. Using in-memory fallback.")
                pinecone_client = None
        except Exception as e:
            logging.warning(f"VectorDBService: Unexpected error during Pinecone init: {e}. Using in-memory fallback.")
            pinecone_client = None
        
        # If real Pinecone client failed to initialize, use in-memory adapter
        if pinecone_client is None:
            pinecone_client = _InMemoryPineconeAdapter()
            logging.info("VectorDBService: Using in-memory Pinecone adapter.")

        self.index_name = config.PINECONE_INDEX_NAME
        self.dimension = 512  # Dimension for CLIP model openai/clip-vit-base-patch32

        # Ensure index exists and create/connect using the resolved client
        existing = []
        try:
            result = pinecone_client.list_indexes()  # type: ignore[attr-defined]
            # Some clients return an object with .names(), others return a list
            if hasattr(result, "names"):
                existing = result.names()  # type: ignore[attr-defined]
            else:
                existing = result if isinstance(result, list) else []
        except Exception as e:
            logging.warning(f"VectorDBService: Could not list indexes: {e}. Skipping index creation check.")
            existing = []

        if self.index_name not in existing:
            logging.info("VectorDBService: Index '%s' not found. Attempting to create...", self.index_name)
            try:
                # Try the simpler create_index signature first
                try:
                    pinecone_client.create_index(  # type: ignore[attr-defined]
                        name=self.index_name,
                        dimension=self.dimension,
                        metric="cosine",
                        metadata_config={"indexed": ["kb_type", "context_id"]}
                    )
                    logging.info("VectorDBService: Index created successfully with metadata_config.")
                except TypeError:
                    # New Pinecone API requires spec; try ServerlessSpec if available
                    ServerlessSpec = getattr(_pinecone, "ServerlessSpec", None) or getattr(pinecone_client, "ServerlessSpec", None)
                    if ServerlessSpec is not None:
                        # Extract a valid AWS region from PINECONE_ENVIRONMENT or AWS_REGION
                        # Valid AWS regions: us-east-1, us-west-2, eu-west-1, etc.
                        # If PINECONE_ENVIRONMENT contains "gcp", try gcp-starter or default to us-west-2
                        env_region = config.PINECONE_ENVIRONMENT or ""
                        aws_region = config.AWS_REGION or ""
                        
                        # Pick a valid region
                        if "gcp" in env_region.lower():
                            region = "gcp-starter"
                        elif aws_region and not "gcp" in aws_region.lower():
                            region = aws_region
                        else:
                            region = "us-west-2"
                        
                        cloud = "gcp" if region == "gcp-starter" else "aws"
                        
                        logging.info(f"VectorDBService: Creating index with ServerlessSpec cloud={cloud}, region={region}")
                        try:
                            spec = ServerlessSpec(cloud=cloud, region=region)
                            pinecone_client.create_index(  # type: ignore[attr-defined]
                                name=self.index_name,
                                dimension=self.dimension,
                                metric="cosine",
                                spec=spec
                            )
                            logging.info("VectorDBService: Index created successfully with ServerlessSpec.")
                        except Exception as spec_err:
                            logging.warning(f"VectorDBService: Failed to create index with ServerlessSpec: {spec_err}. Index may already exist.")
                    else:
                        logging.warning("VectorDBService: ServerlessSpec not available; cannot create index.")
            except Exception as e:
                logging.warning(f"VectorDBService: Could not create index '{self.index_name}': {e}. Continuing with existing index or in-memory fallback.")

        try:
            # Obtain an index object with upsert/query methods
            if hasattr(pinecone_client, "Index"):
                self.index = pinecone_client.Index(self.index_name)  # type: ignore[attr-defined]
            elif hasattr(pinecone_client, "index"):
                self.index = pinecone_client.index(self.index_name)  # type: ignore[attr-defined]
            else:
                # Fallback to module-level Index if available
                self.index = _pinecone.Index(self.index_name)  # type: ignore[attr-defined]
        except Exception as e:
            logging.warning(f"VectorDBService: Could not obtain index object: {e}. Using in-memory fallback.")
            # Create a fallback in-memory index
            if isinstance(pinecone_client, _InMemoryPineconeAdapter):
                self.index = pinecone_client.Index(self.index_name)
            else:
                # Last resort: create a minimal in-memory index
                self.index = _InMemoryIndex(self.index_name)

        logging.info("VectorDBService: Pinecone initialized and connected to index.")

    def upsert(
        self,
        vector: list[float],
        kb_type: KBType,
        source_type: str,
        source_id: str,
        context_id: str | None = None
    ) -> str:
        """
        Upserts a vector into the Pinecone index with appropriate metadata.

        Args:
            vector: The embedding vector.
            kb_type: The knowledge base type (GKB or SKB).
            source_type: The type of the source data (e.g., 'text', 'image').
            source_id: A unique identifier for the source data (e.g., filename, hash).
            context_id: A unique identifier for the context (e.g., user_id, session_id),
                        required for SKB.

        Returns:
            The unique ID of the upserted vector.
        """
        if kb_type == KBType.SKB and not context_id:
            raise ValueError("context_id is required for SKB upserts.")

        vector_id = str(uuid.uuid4())
        metadata = {
            "kb_type": kb_type.value,
            "source_type": source_type,
            "source_id": source_id,
            "context_id": context_id or "gkb_default"
        }
        
        self.index.upsert(vectors=[(vector_id, vector, metadata)])
        return vector_id

    def query(
        self,
        vector: list[float],
        kb_type: KBType,
        context_id: str | None = None,
        top_k: int = 5
    ) -> list[dict]:
        """
        Queries the index using metadata filters for GKB/SKB logic.
        """
        filter_query = {"kb_type": kb_type.value}
        if kb_type == KBType.SKB and context_id:
            filter_query["context_id"] = context_id
        
        results = self.index.query(vector=vector, filter=filter_query, top_k=top_k, include_metadata=True)
        return results.get('matches', [])

# Create a single, reusable instance of the service
vector_db_service = VectorDBService(settings)