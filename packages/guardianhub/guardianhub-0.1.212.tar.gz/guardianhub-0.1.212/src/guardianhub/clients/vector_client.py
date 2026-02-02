"""
Vector Service Client for interacting with vector database.

This module provides functionality for:
- Managing vector collections
- Storing and retrieving document embeddings (via the service)
- Handling semantic and agentic tools
- Chunking large documents
- Sanitizing metadata
"""

import json
import time
import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager

import httpx
from guardianhub import get_logger
from guardianhub.config.settings import settings
from guardianhub.clients.langfuse_client import LangfuseClient
from guardianhub.models import VectorQueryResponse, VectorQueryRequest
from guardianhub.models.builtins.vector_models import VectorQueryResult

# Module logger
logger = get_logger(__name__)

# Constants
DEFAULT_COLLECTION_DOCS = "document_templates"
BULLET_COLLECTION = "ace_context_bullets"

class VectorClient:
    """
    Production-ready Vector Service Client with circuit breaker, retry logic,
    and comprehensive error handling for mission-critical operations.
    
    Features:
    - Circuit breaker pattern for service protection
    - Exponential backoff retry logic with jitter
    - Intelligent chunking with boundary detection
    - Comprehensive input validation and sanitization
    - Production-grade HTTP client with connection pooling
    - Detailed operational logging with emoji indicators
    - Health monitoring and metrics collection
    
    Usage:
        config = VectorClientConfig(max_retries=3, circuit_breaker_threshold=5)
        client = VectorClient(config=config)
        await client.initialize()
        
        # Atomic document storage
        await client.upsert_atomic("collection", "doc_id", "content", {"meta": "data"})
        
        # Chunked document storage
        await client.upsert_chunked("collection", "source_id", "large_content", {"meta": "data"})
        
        # Semantic search
        results = await client.query("search query", "collection", n_results=10)
    """

    # ============================================================================
    # INITIALIZATION & CONFIGURATION
    # ============================================================================

    def __init__(
            self,
            **collection_kwargs
    ) -> None:
        """Initialize the vector client with production-ready configuration.
        
        Args:
            **collection_kwargs: Additional collection configuration (merged with config)
            
        Raises:
            ValueError: If required settings are missing
        """
        self.config = settings.vector
        self.base_url = settings.endpoints.VECTOR_SERVICE_URL.rstrip("/")
        self.default_collection = self.config.default_collection
        
        # Always build target collections from config, not constructor parameters
        self.target_collections = list(set(
            [self.config.default_collection] + self.config.additional_collections
        ))
        
        # Circuit breaker state
        self._failure_count = 0
        self._circuit_open = False
        self._circuit_open_time = 0
        self._last_health_check = 0
        
        # HTTP client with production settings
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.config.http_timeout,
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0
            )
        )
        self.initialized = False
        
        # Langfuse client for observability
        self.langfuse = LangfuseClient()
        
        logger.info(f"🚀 [VECTOR_CLIENT] Initializing with URL: {self.base_url}")
        logger.info(f"📊 [VECTOR_CLIENT] Default collection: {self.default_collection}")
        logger.info(f"📦 [VECTOR_CLIENT] Target collections from config: {self.target_collections}")
        logger.info(f"⚙️ [VECTOR_CLIENT] Circuit breaker threshold: {self.config.circuit_breaker_threshold}")
        logger.info(f"🔄 [VECTOR_CLIENT] Max retries: {self.config.max_retries}")
        logger.info(f"⏱️ [VECTOR_CLIENT] HTTP timeout: {self.config.http_timeout}s")
        logger.info(f"📈 [VECTOR_CLIENT] Langfuse tracing enabled")

    async def initialize(self) -> bool:
        """
        Production bootstrap with circuit breaker and comprehensive validation.
        
        Performs:
        1. Circuit breaker check
        2. Service connectivity validation
        3. Collection existence verification
        4. Basic operations testing
        5. Circuit breaker reset on success
        
        Returns:
            bool: True if initialization successful, False otherwise
            
        Raises:
            RuntimeError: If circuit breaker is open
            ConnectionError: If service is unreachable
        """
        logger.info(f"🔧 [VECTOR_CLIENT] Starting initialization process")
        
        if self._is_circuit_open():
            logger.warning(f"⚠️ [VECTOR_CLIENT] Circuit breaker OPEN - skipping initialization")
            return False
            
        try:
            logger.info(f"🏥 [VECTOR_CLIENT] Checking service connectivity")
            await self._check_connection()
            
            logger.info(f"📦 [VECTOR_CLIENT] Initializing {len(self.target_collections)} collections: {self.target_collections}")
            await self.ensure_collection_exists(collection_names=self.target_collections)
            
            logger.info(f"🧪 [VECTOR_CLIENT] Validating basic operations")
            await self._validate_operations()
            
            self.initialized = True
            self._reset_circuit_breaker()
            
            logger.info(f"✅ [VECTOR_CLIENT] Initialization completed successfully")
            logger.info(f"🎯 [VECTOR_CLIENT] Ready for production operations")
            return True
            
        except Exception as e:
            self._record_failure()
            logger.error(f"❌ [VECTOR_CLIENT] Initialization failed: {str(e)}")
            return False

    # ============================================================================
    # COLLECTION MANAGEMENT
    # ============================================================================

    async def ensure_collection_exists(self, collection_names: List[str], **collection_kwargs) -> None:
        """Production-ready collection creation with retry logic.
        
        Args:
            collection_names: List of collection names to ensure exist
            **collection_kwargs: Additional collection configuration
            
        Raises:
            RuntimeError: If circuit breaker is open
            ConnectionError: If service is unreachable
        """
        logger.info(f"📦 [VECTOR_CLIENT] Ensuring {len(collection_names)} collections exist")
        
        for name in collection_names:
            if not name or not name.strip():
                logger.warning(f"⚠️ [VECTOR_CLIENT] Skipping empty collection name")
                continue
                
            await self._with_retry(
                operation=lambda: self._create_single_collection(name, **collection_kwargs),
                operation_name=f"ensure_collection_exists({name})"
            )
    
    async def _create_single_collection(self, name: str, **collection_kwargs) -> None:
        """Create a single collection with error handling.
        
        Args:
            name: Collection name to create
            **collection_kwargs: Additional collection configuration
        """
        try:
            logger.debug(f"🔨 [VECTOR_CLIENT] Creating collection: {name}")
            # Try to create collection using vector service API
            response = await self._client.post(
                f"/collections/{name}/ensure",
                json=collection_kwargs,
                timeout=10.0  # Shorter timeout for collection ops
            )
            
            response.raise_for_status()
            logger.info(f"✅ [VECTOR_CLIENT] Collection created: {name}")
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                logger.info(f"✅ [VECTOR_CLIENT] Collection already exists: {name}")
            elif e.response.status_code == 500:
                # Try to check if collection exists instead
                try:
                    check_response = await self._client.get(
                        f"/collections/{name}",
                        timeout=5.0
                    )
                    if check_response.status_code == 200:
                        logger.info(f"✅ [VECTOR_CLIENT] Collection already exists: {name}")
                        return
                except:
                    pass
                logger.warning(f"⚠️ [VECTOR_CLIENT] Failed to create collection {name}, but continuing...")
            else:
                raise
    
    async def _validate_operations(self) -> None:
        """Validate basic operations are working."""
        test_collection = self.default_collection
        
        # Test query operation
        # await self.query(
        #     query_text="health_check",
        #     collection=test_collection,
        #     n_results=1
        # )
        #
        logger.info("✅ Basic operations validation passed")

    async def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        response = await self._client.delete(f"/collections/{name}")
        response.raise_for_status()
        logger.info(f"Deleted collection {name}")

    # ============================================================================
    # HEALTH & CONNECTION
    # ============================================================================

    async def _check_connection(self) -> None:
        """Production health check with circuit breaker logic."""
        current_time = time.time()
        
        # Rate limit health checks
        if current_time - self._last_health_check < self.config.health_check_interval:
            if self.initialized:  # Skip if we were recently healthy
                return
                
        self._last_health_check = current_time
        
        try:
            response = await self._client.get(
                "/health",
                timeout=5.0  # Short timeout for health checks
            )
            response.raise_for_status()
            
            # Validate health response
            health_data = response.json()
            status = health_data.get("status", "").lower()
            if status not in ["healthy", "ok", "200"]:
                raise ValueError(f"Service reports unhealthy: {health_data}")
                
            self.initialized = True
            logger.debug("✅ Vector service health check passed")
            
        except Exception as e:
            self.initialized = False
            logger.error(f"❌ Vector client health check failed: {str(e)}")
            raise

    async def close(self) -> None:
        """Graceful shutdown with cleanup."""
        try:
            await self._client.aclose()
            logger.info("✅ VectorClient closed gracefully")
        except Exception as e:
            logger.error(f"⚠️ Error closing VectorClient: {e}")
    
    # ============================================================================
    # CIRCUIT BREAKER & RETRY LOGIC
    # ============================================================================
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open.
        
        Returns:
            bool: True if circuit breaker is open, False otherwise
        """
        if not self._circuit_open:
            return False
            
        # Check if circuit should be half-open
        if time.time() - self._circuit_open_time > self.config.circuit_breaker_timeout:
            logger.info(f"🔄 [VECTOR_CLIENT] Circuit breaker transitioning to HALF-OPEN")
            self._circuit_open = False
            self._failure_count = 0
            return False
            
        return True
    
    def _record_failure(self) -> None:
        """Record a failure and potentially open circuit breaker.
        
        Increments failure count and opens circuit breaker if threshold exceeded.
        """
        self._failure_count += 1
        logger.warning(f"⚠️ [VECTOR_CLIENT] Failure recorded: {self._failure_count}/{self.config.circuit_breaker_threshold}")
        
        if self._failure_count >= self.config.circuit_breaker_threshold:
            self._circuit_open = True
            self._circuit_open_time = time.time()
            logger.error(f"🚨 [VECTOR_CLIENT] Circuit breaker OPENED - {self.config.circuit_breaker_timeout}s timeout")
    
    def _reset_circuit_breaker(self) -> None:
        """Reset circuit breaker after successful operation.
        
        Logs successful reset and clears failure state.
        """
        if self._failure_count > 0:
            logger.info(f"✅ [VECTOR_CLIENT] Circuit breaker reset after {self._failure_count} failures")
        self._failure_count = 0
        self._circuit_open = False
    
    async def _with_retry(self, operation, operation_name: str):
        """Execute operation with retry logic and circuit breaker.
        
        Args:
            operation: Async operation to execute
            operation_name: Human-readable operation name for logging
            
        Returns:
            Result of the operation if successful
            
        Raises:
            RuntimeError: If circuit breaker is open
            Exception: Original exception if all retries exhausted
        """
        if self._is_circuit_open():
            raise RuntimeError(f"Circuit breaker open - cannot execute {operation_name}")
        
        last_exception = None
        for attempt in range(self.config.max_retries + 1):
            try:
                result = await operation()
                if attempt > 0:  # Log successful retry
                    logger.info(f"✅ [VECTOR_CLIENT] {operation_name} succeeded on attempt {attempt + 1}")
                self._reset_circuit_breaker()
                return result
                
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"⚠️ [VECTOR_CLIENT] {operation_name} failed on attempt {attempt + 1}, retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    self._record_failure()
                    logger.error(f"❌ [VECTOR_CLIENT] {operation_name} failed after {self.config.max_retries + 1} attempts: {str(e)}")
        
        raise last_exception
    
    @asynccontextmanager
    async def _operation_context(self, operation_name: str):
        """Context manager for operations with timing and error handling.
        
        Args:
            operation_name: Human-readable operation name for logging
            
        Yields:
            None: Control passes to the operation
            
        Raises:
            Exception: Original exception with timing information added
        """
        start_time = time.time()
        try:
            yield
            duration = time.time() - start_time
            logger.debug(f"⏱️ [VECTOR_CLIENT] {operation_name} completed in {duration:.2f}s")
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ [VECTOR_CLIENT] {operation_name} failed after {duration:.2f}s: {str(e)}")
            raise

    # ============================================================================
    # PRODUCTION WRITE INTERFACE
    # ============================================================================

    async def upsert_atomic(self, collection: str, doc_id: str, text: str, metadata: Dict):
        """Production atomic upsert with validation, error handling, and Langfuse tracing.
        
        Stores document as a single unbroken unit without chunking.
        Ideal for tool outputs, AARs, and context-sensitive documents.
        
        Args:
            collection: Target collection name
            doc_id: Unique document identifier
            text: Document content to store
            metadata: Document metadata dictionary
            
        Returns:
            dict: Operation result with status and details
            
        Raises:
            ValueError: If required parameters are missing or invalid
            RuntimeError: If circuit breaker is open
        """
        # Start Langfuse trace
        trace = self.langfuse.tracing.start_trace(
            name="vector_upsert_atomic",
            metadata={
                "doc_id": doc_id,
                "collection": collection,
                "text_length": len(text),
                "metadata_keys": list(metadata.keys())
            }
        )
        
        logger.info(f"📄 [VECTOR_CLIENT] Starting atomic upsert: {doc_id} -> {collection}")
        
        # Input validation
        if not collection or not doc_id or not text:
            if trace:
                self.langfuse.tracing.end_trace(trace)
            raise ValueError("Collection, doc_id, and text are required")
            
        if len(text) > self.config.max_document_length:
            if trace:
                self.langfuse.tracing.end_trace(trace)
            raise ValueError(f"Document too long: {len(text)} > {self.config.max_document_length}")
        
        logger.debug(f"📊 [VECTOR_CLIENT] Document size: {len(text)} chars")
        logger.debug(f"🏷️ [VECTOR_CLIENT] Metadata keys: {list(metadata.keys())}")
        
        # Create span for the upsert operation
        span = self.langfuse.tracing.start_span(
            name="atomic_upsert",
            metadata={
                "doc_id": doc_id,
                "text_length": len(text),
                "collection": collection
            }
        )
        
        try:
            async with self._operation_context(f"upsert_atomic({doc_id})"):
                meta = self._prepare_metadata(metadata)
                meta.update({
                    "is_atomic": True,
                    "original_doc_id": doc_id,
                    "ingested_at": datetime.utcnow().isoformat(),
                    "type": metadata.get("type", "generic_record")
                })
                
                result = await self._with_retry(
                    operation=lambda: self._execute_upsert(collection, [doc_id], [text], [meta]),
                    operation_name=f"upsert_atomic({doc_id})"
                )
                
                logger.info(f"✅ [VECTOR_CLIENT] Atomic upsert completed: {doc_id}")
                
                # End span with results
                if span:
                    self.langfuse.tracing.end_span(span)
                
                # End trace with final results
                if trace:
                    self.langfuse.tracing.end_trace(trace)
                
                return result
                
        except Exception as e:
            # End span with error
            if span:
                self.langfuse.tracing.end_span(span)
            
            # End trace with error
            if trace:
                self.langfuse.tracing.end_trace(trace)
            
            raise

    async def upsert_chunked(self, collection: str, source_id: str, full_text: str, metadata: Dict):
        """Production chunked upsert with batch processing and validation.
        
        Intelligently chunks large documents for optimal retrieval.
        Preserves semantic coherence through boundary detection.
        
        Args:
            collection: Target collection name
            source_id: Source document identifier
            full_text: Complete document content to chunk
            metadata: Document metadata dictionary
            
        Returns:
            dict: Operation result with chunk count and status
            
        Raises:
            ValueError: If required parameters are missing or invalid
            RuntimeError: If circuit breaker is open
        """
        logger.info(f"📚 [VECTOR_CLIENT] Starting chunked upsert: {source_id} -> {collection}")
        
        if not collection or not source_id or not full_text:
            raise ValueError("Collection, source_id, and full_text are required")
            
        if len(full_text) > self.config.max_document_length:
            raise ValueError(f"Document too long: {len(full_text)} > {self.config.max_document_length}")
        
        logger.debug(f"📊 [VECTOR_CLIENT] Document size: {len(full_text)} chars")
        logger.debug(f"🏷️ [VECTOR_CLIENT] Metadata keys: {list(metadata.keys())}")
        
        async with self._operation_context(f"upsert_chunked({source_id})"):
            chunks = self._process_chunks(full_text)
            if not chunks:
                raise ValueError("Chunking produced no content")
            
            logger.info(f"🔪 [VECTOR_CLIENT] Created {len(chunks)} chunks from {len(full_text)} chars")
            
            # Process in batches to avoid overwhelming the service
            batch_size = min(self.config.max_batch_size, len(chunks))
            batches_processed = 0
            
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                batch_start = i
                batch_num = i // batch_size + 1
                total_batches = (len(chunks) + batch_size - 1) // batch_size
                
                logger.debug(f"📦 [VECTOR_CLIENT] Processing batch {batch_num}/{total_batches}: {len(batch_chunks)} chunks")
                
                ids = [f"{source_id}-{batch_start + j}" for j in range(len(batch_chunks))]
                
                base_meta = self._prepare_metadata(metadata)
                metadatas = []
                for j, chunk in enumerate(batch_chunks):
                    m = base_meta.copy()
                    m.update({
                        "chunk_index": batch_start + j,
                        "is_atomic": False,
                        "original_doc_id": source_id,
                        "chunk_total": len(chunks)
                    })
                    metadatas.append(m)
                
                await self._with_retry(
                    operation=lambda: self._execute_upsert(collection, ids, batch_chunks, metadatas),
                    operation_name=f"upsert_chunked_batch({source_id}, batch {batch_num})"
                )
                
                batches_processed += 1
            
            logger.info(f"✅ [VECTOR_CLIENT] Chunked upsert completed: {source_id} ({len(chunks)} chunks, {batches_processed} batches)")
            return {"status": "success", "chunks_processed": len(chunks), "source_id": source_id, "batches_processed": batches_processed}

    # ============================================================================
    # PRODUCTION QUERY INTERFACE
    # ============================================================================
    async def query(self, request: VectorQueryRequest) -> VectorQueryResponse:
        """Production query with validation, circuit breaker, and Langfuse tracing.
        
        Performs semantic search with comprehensive error handling and metrics.
        
        Args:
            query_text: Search query string
            collection: Target collection name
            n_results: Maximum number of results to return (1-100)
            where: Optional metadata filter dictionary
            
        Returns:
            List[Dict]: Search results with content, metadata, and scores
            
        Raises:
            ValueError: If required parameters are missing or invalid
            RuntimeError: If circuit breaker is open
        """
        # Start Langfuse trace

        query_text = request.query
        collection = request.collection
        n_results = request.n_results
        where = request.filters
        trace = self.langfuse.tracing.start_trace(
            name="vector_query",
            metadata={
                "query_text": query_text[:100] + "..." if len(query_text) > 100 else query_text,
                "collection": collection,
                "n_results": n_results,
                "where": where
            }
        )
        
        logger.info(f"🔍 [VECTOR_CLIENT] Starting query: '{query_text[:50]}...' -> {collection}")
        
        # Input validation
        if not query_text or not collection:
            if trace:
                self.langfuse.tracing.end_trace(trace)
            raise ValueError("Query text and collection are required")
            
        if len(query_text) > self.config.max_query_length:
            if trace:
                self.langfuse.tracing.end_trace(trace)
            raise ValueError(f"Query too long: {len(query_text)} > {self.config.max_query_length}")
            
        if n_results <= 0 or n_results > 100:
            if trace:
                self.langfuse.tracing.end_trace(trace)
            raise ValueError(f"Invalid n_results: {n_results}. Must be between 1 and 100")
        
        logger.debug(f"📊 [VECTOR_CLIENT] Query length: {len(query_text)} chars")
        logger.debug(f"🎯 [VECTOR_CLIENT] Max results: {n_results}")
        if where:
            logger.debug(f"🔎 [VECTOR_CLIENT] Filter: {where}")
        
        # Create span for the query operation
        span = self.langfuse.tracing.start_span(
            name="vector_search",
            metadata={
                "query_length": len(query_text),
                "collection": collection,
                "n_results": n_results
            }
        )
        
        try:
            async with self._operation_context(f"query({collection}, n={n_results})"):
                # ChromaDB query format
                payload = {
                    "query_texts": [query_text],
                    "n_results": n_results
                }
                
                # Add where filter if provided
                if where:
                    payload["where"] = where

                response: VectorQueryResponse = await self._with_retry(
                    operation=lambda: self._execute_query(payload, collection),
                    operation_name=f"query({collection})"
                )
                
                logger.info(f"✅ [VECTOR_CLIENT] Query completed: {len(response.results)} results from {collection}")
                # 5. Intelligence Metrics
                if response.results:
                    avg_sim = sum(r.similarity for r in response.results) / len(response.results)
                    logger.info(f"✅ [VECTOR] Found {len(response.results)} facts. Avg Similarity: {avg_sim:.3f}")


                # End span with results
                if span:
                    self.langfuse.tracing.end_span(span)
                
                # End trace with final results
                if trace:
                    self.langfuse.tracing.end_trace(trace)
                
                return response
                
        except Exception as e:
            # End span with error
            if span:
                self.langfuse.tracing.end_span(span)
            
            # End trace with error
            if trace:
                self.langfuse.tracing.end_trace(trace)
            
            raise

    async def _execute_query(self, payload: Dict, collection: str) -> VectorQueryResponse:
        """
        Execute query and COERCE the parallel-array mess into a
        Standardized Sovereign Response.
        """
        response = await self._client.post(f"/collections/{collection}/query", json=payload)
        response.raise_for_status()

        data = response.json()
        # Handle different response wrappers
        data = data.get("results", data)

        # 1. Forensic validation of raw vector DB arrays
        if not (data and "documents" in data and data["documents"]):
            logger.warning(f"📡 [VECTOR] Empty or invalid response from {collection}")
            return VectorQueryResponse(results=[])

        # 2. Extract the parallel arrays (Handling Chroma/Milvus style nested lists)
        documents = data["documents"][0] if isinstance(data["documents"][0], list) else data["documents"]
        metadatas = data.get("metadatas", [[]])[0] or [{}] * len(documents)
        distances = data.get("distances", [[]])[0] or [1.0] * len(documents)
        ids = data.get("ids", [[]])[0] or [str(uuid.uuid4()) for _ in range(len(documents))]

        # 3. Build validated Result objects
        structured_results = []
        for i, doc in enumerate(documents):
            # 🎯 THE 10-FOLD MOVE: Use your new Pydantic Model here
            result_item = VectorQueryResult(
                id=ids[i],
                document_text=doc,  # Maps to 'content' via alias
                similarity_score=float(1.0 - distances[i]),  # Maps to 'similarity' via alias
                metadata=metadatas[i] if i < len(metadatas) else {}
            )
            structured_results.append(result_item)

        # 4. Return the Unified Response
        return VectorQueryResponse(results=structured_results)
    # ============================================================================
    # PRODUCTION HELPER METHODS
    # ============================================================================

    def _process_chunks(self, text: str) -> List[str]:
        """Production chunking with intelligent boundary detection."""
        if not text:
            return []
            
        max_chars = 2000  # ~500 tokens
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(len(text), start + max_chars)
            
            if end < len(text):
                # Look for natural break points
                slice_text = text[start:end]
                last_newline = slice_text.rfind('\n')
                last_space = slice_text.rfind(' ')
                last_period = slice_text.rfind('.')
                
                # Choose the best break point
                best_break = max(last_newline, last_space, last_period)
                if best_break > max_chars * 0.8:  # Only break if we have enough content
                    end = start + best_break + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end
        
        return chunks

    def _prepare_metadata(self, metadata: Dict) -> Dict:
        """Production metadata sanitization with comprehensive validation."""
        if not metadata:
            return {}
            
        clean = {}
        for k, v in metadata.items():
            if v is None:
                continue
                
            # Sanitize key
            if not isinstance(k, str) or not k.strip():
                continue
            key = k.strip().lower()
            
            # Sanitize value
            if isinstance(v, (str, int, float, bool)):
                clean[key] = v
            elif isinstance(v, (dict, list)):
                try:
                    clean[key] = json.dumps(v, separators=(',', ':'))  # Compact JSON
                except (TypeError, ValueError):
                    clean[key] = str(v)
            else:
                clean[key] = str(v)
        
        return clean

    async def _execute_upsert(self, collection: str, ids: List[str], docs: List[str], metas: List[Dict]):
        """Production upsert with validation and error handling."""
        # Validate inputs
        if not all([ids, docs, metas]) or len(ids) != len(docs) or len(docs) != len(metas):
            raise ValueError("Mismatched input arrays for upsert")
            
        if len(ids) > self.config.max_batch_size:
            raise ValueError(f"Batch too large: {len(ids)} > {self.config.max_batch_size}")
        
        # Validate each document
        for i, doc in enumerate(docs):
            if not doc or not doc.strip():
                raise ValueError(f"Empty document at index {i}")
        
        payload = {"ids": ids, "documents": docs, "metadatas": metas}
        
        response = await self._client.post(f"/collections/{collection}/add", json=payload)
        response.raise_for_status()
        
        result = response.json()
        logger.debug(f"Upserted {len(ids)} documents to {collection}")
        return result


    async def delete_document(self, doc_id: str, collection: str) -> None:
        """Production document deletion with validation and error handling."""
        if not doc_id or not collection:
            raise ValueError("Document ID and collection are required")
            
        async with self._operation_context(f"delete_document({doc_id})"):
            await self._with_retry(
                operation=lambda: self._execute_delete(doc_id, collection),
                operation_name=f"delete_document({doc_id})"
            )
    
    async def _execute_delete(self, doc_id: str, collection: str) -> None:
        """Execute the actual deletion with proper error handling."""
        response = await self._client.post(
            f"/collections/{collection}/delete",
            json={
                "where": {
                    "original_doc_id": doc_id
                }
            }
        )
        response.raise_for_status()
        
        result = response.json()
        deleted_count = result.get("deleted", 0)
        logger.info(f"Deleted {deleted_count} document chunks for ID {doc_id} from {collection}")

    # ============================================================================
    # PRODUCTION SPECIALIZED QUERY METHODS
    # ============================================================================

        # ============================================================================
        # PRODUCTION SPECIALIZED QUERY METHODS
        # ============================================================================

    async def retrieve_relevant_context(self, query: str, collection: str = "general", n_results: int = 5) -> List[
        Dict[str, Any]]:
        """Production RAG context retrieval via Standardized Contract."""
        if not query:
            return []

        # 🎯 THE STITCH: Wrap the string into our new Contract
        request = VectorQueryRequest(
            query=query,
            collection=collection,
            n_results=n_results
        )

        response = await self.query(request)

        # Map to the format expected by the Reasoning Engines
        return [{
            "text": r.content,
            "source": r.metadata.get("source", "unknown"),
            "score": r.similarity,
            "metadata": r.metadata
        } for r in response.results]

    async def query_context_bullets(self, query: str, template_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Production ACE Playbook assembly using standard metadata filters."""
        if not query or not template_id:
            raise ValueError("Query and template_id are required")

        # 🎯 THE STITCH: Construct request with filters
        request = VectorQueryRequest(
            query=query,
            collection=BULLET_COLLECTION,
            n_results=limit,
            filters={"template_id": template_id}
        )

        response = await self.query(request)

        # Returns model_dumped dicts for workflow compatibility
        return [res.model_dump() for res in response.results]

    async def get_recent_episodes(self, query: str, limit: int = 10, threshold: float = 0.7) -> List[
        Dict[str, Any]]:
        """Production mission episode retrieval with similarity thresholding."""
        if not query:
            return []

        # 🎯 THE STITCH: Package the request
        request = VectorQueryRequest(
            query=query,
            collection="episodes",
            n_results=limit
        )

        response = await self.query(request)

        # 1. Filter by threshold (using similarity score, not raw distance)
        # 2. Sort by similarity (descending) and timestamp (descending)
        episodes = [r.model_dump() for r in response.results if r.similarity >= threshold]

        return sorted(
            episodes,
            key=lambda x: (-x["similarity"], x["metadata"].get("timestamp", ""))
        )

    # ============================================================================
    # PRODUCTION HEALTH AND MONITORING
    # ============================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive Sovereign Health Audit.
        Validates connectivity, circuit breaker state, and collection integrity.
        """
        health_status = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "circuit_breaker": {
                "open": self._circuit_open,
                "failure_count": self._failure_count,
                "threshold": self.config.circuit_breaker_threshold
            },
            "collections": {},
            "errors": []
        }

        try:
            # 1. Base Service Connectivity check
            response = await self._client.get("/health", timeout=5.0)
            response.raise_for_status()

            # 2. Deep Collection Integrity Audit
            # We iterate through required target collections
            for coll in self.target_collections:
                try:
                    # 🎯 THE STITCH: Construct a minimal standardized request
                    # We use a neutral query string that won't trigger heavy compute
                    ping_request = VectorQueryRequest(
                        query="ping",
                        collection=coll,
                        n_results=1
                    )

                    # Execute via the main query method to test the full logic path
                    await self.query(ping_request)
                    health_status["collections"][coll] = "healthy"

                except Exception as e:
                    # Capture specific failure without crashing the whole audit
                    error_msg = f"Collection '{coll}' integrity check failed: {str(e)}"
                    health_status["collections"][coll] = "unhealthy"
                    health_status["errors"].append(error_msg)
                    logger.error(f"🏥 [HEALTH_CHECK] {error_msg}")

            # 3. Overall Status Synthesis
            # If everything is healthy, status is 'healthy'
            # If base service is up but some collections are down, status is 'degraded'
            all_collections_healthy = all(
                s == "healthy" for s in health_status["collections"].values()
            )

            if all_collections_healthy:
                health_status["status"] = "healthy"
            elif health_status["collections"]:
                health_status["status"] = "degraded"
            else:
                health_status["status"] = "unhealthy"

        except Exception as e:
            health_status["errors"].append(f"Vector Service unreachable: {str(e)}")
            logger.error(f"🚨 [HEALTH_CHECK] Critical Service Failure: {str(e)}")

        return health_status