# -*- coding: utf-8 -*-
# @Author: Cursor
# @Date: 2025-02-12
# @Last Modified by: Gemini
# @Last Modified time: 2025-10-09

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from typing import List, Dict, Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_milvus import Milvus
from langchain_openai import AzureOpenAIEmbeddings
from pymilvus import MilvusClient, AsyncMilvusClient, connections

from .schema_milvus import SchemaMilvus, DEFAULT_SCHEMA
from ...services.init_services import get_model_balancer


#from .milvus_schema_manager import MilvusSchemaManager

class VDBService(object):
    """
    A service to manage connections to Milvus/Zilliz vector databases and embedding models.

    This service centralizes the configuration and instantiation of the Milvus client
    and provides helper methods to get embedding functions and vector store instances.

    This service generates a unique connection `alias` upon initialization. This `alias`
    is propagated to all Milvus clients created by this service, including those
    within `langchain_milvus` instances. This mechanism ensures that a single,
    shared connection is used for all operations, preventing the creation of
    multiple redundant connections and improving resource efficiency.

    Args:
        settings (dict, optional): A dictionary containing configuration for the vector store
                         and embedding models.
        endpoint (str, optional): The URI for the Zilliz cluster. Can be used for simple
                                  initialization instead of `settings`.
        token (str, optional): The token for authenticating with Zilliz. Must be provided
                               with `endpoint`.
        schema (str, optional): The schema definition for a collection. Defaults to None.
        logger (logging.Logger, optional): An optional logger instance. Defaults to None.

    Raises:
        ValueError: If required configurations are missing.
        NotImplementedError: If an unsupported provider is specified.
        RuntimeError: If the MilvusClient fails to initialize after a retry.

    Example:
        >>> # Initialize with a full settings dictionary
        >>> settings = {
        ...     "embedder": {
        ...         "provider": "azure-openai-embeddings",
        ...         "config": {
        ...             "model": "text-embedding-ada-002",
        ...             "api_version": "2023-05-15",
        ...             "api_key": "YOUR_AZURE_OPENAI_KEY",
        ...             "openai_base_url": "YOUR_AZURE_OPENAI_ENDPOINT",
        ...             "embedding_dims": 1536
        ...         }
        ...     },
        ...     "vector_store": {
        ...         "provider": "milvus",
        ...         "config": {
        ...             "host": "localhost",
        ...             "port": 19530,
        ...             "user": "root",
        ...             "password": "password",
        ...             "db_name": "default"
        ...         }
        ...     },
        ...     "index_params": {
        ...         "metric_type": "IP",
        ...         "index_type": "HNSW",
        ...         "params": {}
        ...     }
        ... }
        >>> vdb_service = VDBService(settings=settings)
        >>>
        >>> # Alternatively, initialize with an endpoint and token for Zilliz
        >>> # vdb_service_zilliz = VDBService(endpoint="YOUR_ZILLIZ_ENDPOINT", token="YOUR_ZILLIZ_TOKEN")
        >>>
        >>> # Get the raw Milvus client
        >>> client = vdb_service.get_vector_client()
        >>> print(client.list_collections())
        >>> # Get an embedding function
        >>> embeddings = vdb_service.get_embeddings()
        >>> print(embeddings)
        >>> # Get a LangChain vector store instance (will be cached)
        >>> vector_store = vdb_service.get_vector_store(collection_name="my_collection")
        >>> print(vector_store)
        >>> same_vector_store = vdb_service.get_vector_store(collection_name="my_collection")
        >>> assert vector_store is same_vector_store
    """
    _client: MilvusClient
    _async_client: Optional[AsyncMilvusClient] = None
    _instances: Dict[str, Milvus] = {}
    _async_instances: Dict[str, Milvus] = {}
    _async_instance_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    schema: str
    embedding_function: Embeddings
    index_params: dict
    connection_args: dict
    settings: dict
    
    def __init__(self, settings: dict = None, endpoint: str = None, token: str = None, schema: str = None, logger: logging.Logger = None):
        """
        Initializes the VDBService. 

        Can be initialized in two ways:
        1. By providing a full `settings` dictionary for complex configurations.
        2. By providing `endpoint` and `token` for a direct Zilliz connection.
           Note: When using this method, an `embedder` configuration is not created.
           You must either use the `ModelLoadBalancer` or pass an `Embeddings` object
           directly to methods like `get_vector_store`.
        
        Args:
            settings (dict, optional): Configuration dictionary for the service. Defaults to None.
            endpoint (str, optional): The URI for the Zilliz cluster. Used if `settings` is not provided.
            token (str, optional): The token for authenticating with the Zilliz cluster.
            schema (str, optional): Default schema for new collections. Defaults to None.
            logger (logging.Logger, optional): Logger instance. Defaults to None.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.collection_schema = None

        if settings:
            self.settings = settings
        elif endpoint and token:
            self.logger.info("Initializing VDBService with endpoint and token for a Zilliz connection.")
            self.settings = {
                "vector_store": {
                    "provider": "zilliz",
                    "config": {
                        "uri": endpoint,
                        "token": token
                    }
                }
            }
        else:
            raise ValueError("VDBService must be initialized with either a 'settings' dictionary or both 'endpoint' and 'token'.")

        vector_store_settings = self.settings.get("vector_store")
        if not vector_store_settings:
            msg = "'vector_store' not found in settings"
            self.logger.error(msg)
            raise ValueError(msg)

        provider = vector_store_settings.get("provider")
        self.connection_args = vector_store_settings.get("config")

        if not provider or not self.connection_args:
            msg = "'provider' or 'config' not found in 'vector_store' settings"
            self.logger.error(msg)
            raise ValueError(msg)

        self._provider = provider # Store provider for lazy initialization

        # Create separate aliases for sync and async clients to avoid connection handler race conditions.
        self.sync_alias = f"crewplus-vdb-sync-{uuid.uuid4()}"
        self.async_alias = f"crewplus-vdb-async-{uuid.uuid4()}"

        # The default alias in connection_args should be the sync one, as langchain_milvus
        # primarily uses a synchronous client and will pick up this alias.
        self.connection_args['alias'] = self.sync_alias

        self._client = self._initialize_milvus_client(provider)
        # lazy-initialize async milvus
        # self._async_client = self._initialize_async_milvus_client(provider)

        # Do not initialize the async client here.
        # It must be lazily initialized within an async context.
        self._async_client: Optional[AsyncMilvusClient] = None
        
        self.schema = schema
        self.index_params = self.settings.get("index_params")
        
        #self.schema_manager = MilvusSchemaManager(client=self._client, async_client=self._async_client)
        
        self.logger.info("VDBService initialized successfully")

    def _get_milvus_client_args(self, provider: str) -> dict:
        """
        Constructs the arguments for Milvus/AsyncMilvus client initialization based on the provider.
        """
        if provider == "milvus":
            host = self.connection_args.get("host", "localhost")
            port = self.connection_args.get("port", 19530)
            
            # Use https for remote hosts, and http for local connections.
            scheme = "https" if host not in ["localhost", "127.0.0.1"] else "http"
            uri = f"{scheme}://{host}:{port}"
            
            client_args = {
                "uri": uri,
                "user": self.connection_args.get("user"),
                "password": self.connection_args.get("password"),
                "db_name": self.connection_args.get("db_name"),
            }
            return {k: v for k, v in client_args.items() if v is not None}

        elif provider == "zilliz":
            # Return a copy without the default alias, as it will be added specifically for sync/async clients.
            zilliz_args = self.connection_args.copy()
            zilliz_args.pop('alias', None)
            # 增加 gRPC keepalive 选项来加固连接
            zilliz_args['channel_options'] = [
                ('grpc.keepalive_time_ms', 60000),      # 每 60 秒发送一次 ping
                ('grpc.keepalive_timeout_ms', 20000),   # 20 秒内没收到 pong 则认为连接断开
                ('grpc.enable_http_proxy', 0),
            ]
            return zilliz_args
        else:
            self.logger.error(f"Unsupported vector store provider: {provider}")
            raise NotImplementedError(f"Vector store provider '{provider}' is not supported.")

    def _initialize_milvus_client(self, provider: str) -> MilvusClient:
        """
        Initializes and returns a MilvusClient with a retry mechanism.
        """
        client_args = self._get_milvus_client_args(provider)
        client_args["alias"] = self.sync_alias

        try:
            # First attempt to connect
            return MilvusClient(**client_args)
        except Exception as e:
            self.logger.error(f"Failed to initialize MilvusClient, trying again. Error: {e}")
            # Second attempt after failure
            try:
                return MilvusClient(**client_args)
            except Exception as e_retry:
                self.logger.error(f"Failed to initialize MilvusClient on retry. Final error: {e_retry}")
                raise RuntimeError(f"Could not initialize MilvusClient after retry: {e_retry}")

    def _initialize_async_milvus_client(self, provider: str) -> AsyncMilvusClient:
        """
        Initializes and returns an AsyncMilvusClient with a retry mechanism.
        """
        client_args = self._get_milvus_client_args(provider)
        client_args["alias"] = self.async_alias
        
        try:
            return AsyncMilvusClient(**client_args)
        except Exception as e:
            self.logger.error(f"Failed to initialize AsyncMilvusClient, trying again. Error: {e}")
            time.sleep(1) # sync sleep is fine, we are in a thread
            try:
                return AsyncMilvusClient(**client_args)
            except Exception as e_retry:
                self.logger.error(f"Failed to initialize AsyncMilvusClient on retry. Final error: {e_retry}")
                raise RuntimeError(f"Could not initialize AsyncMilvusClient after retry: {e_retry}") from e_retry

    def get_vector_client(self) -> MilvusClient:
        """
        Returns the active MilvusClient instance, initializing it if necessary.

        Returns:
            MilvusClient: The initialized client for interacting with the vector database.
        """
        if self._client is None:
            self.logger.debug("Initializing synchronous MilvusClient...")
            self._client = self._initialize_milvus_client(self._provider)

        return self._client

    async def aget_async_vector_client(self) -> AsyncMilvusClient:
        """
        Lazily initializes and returns the AsyncMilvusClient.
        This ensures the client is created within the running event loop.
        """
        if self._async_client is None:
            self.logger.info("Lazily initializing AsyncMilvusClient...")
            client_args = self._get_milvus_client_args(self._provider)
            # Use the dedicated async alias
            client_args['alias'] = self.async_alias
            self._async_client = AsyncMilvusClient(**client_args)
        return self._async_client

    def get_vector_field(self, collection_name: str) -> str:
        """
        Retrieves the vector field name for a given collection from a cached instance.

        Args:
            collection_name (str): The name of the collection.

        Returns:
            str: The name of the vector field.
        
        Raises:
            ValueError: If no cached instance is found for the collection.
        """
        if collection_name in self._instances:
            return self._instances[collection_name]._vector_field
        if collection_name in self._async_instances:
            return self._async_instances[collection_name]._vector_field
        
        self.logger.warning(f"No cached instance found for collection '{collection_name}' to get vector field. Creating a temporary sync instance.")
        # As a fallback, create a temporary sync instance to fetch the schema info.
        # This is less efficient but ensures the method is robust.
        temp_instance = self.get_vector_store(collection_name)
        return temp_instance._vector_field

    def get_embeddings(self, from_model_balancer: bool = False, provider: Optional[str] = "azure-openai", model_type: Optional[str] = "embedding-large") -> Embeddings:
        """
        Gets an embedding function, either from the model balancer or directly from settings.

        Args:
            from_model_balancer (bool): If True, uses the central model balancer service.
                                        If False, creates a new instance based on 'embedder' settings.
            model_type (str, optional): The type of model to get from the balancer. Defaults to "embedding-large".

        Returns:
            Embeddings: An instance of a LangChain embedding model.
        """
        if from_model_balancer:
            model_balancer = get_model_balancer()
            return model_balancer.get_model(provider=provider, model_type=model_type)

        embedder_config = self.settings.get("embedder")
        if not embedder_config:
            self.logger.error("'embedder' configuration not found in settings.")
            raise ValueError("'embedder' configuration not found in settings.")

        provider = embedder_config.get("provider")
        config = embedder_config.get("config")

        if not provider or not config:
            self.logger.error("Embedder 'provider' or 'config' not found in settings.")
            raise ValueError("Embedder 'provider' or 'config' not found in settings.")

        if provider == "azure-openai":
            # Map the settings config to AzureOpenAIEmbeddings parameters.
            azure_config = {
                "azure_deployment": config.get("model"),
                "openai_api_version": config.get("api_version"),
                "api_key": config.get("api_key"),
                "azure_endpoint": config.get("openai_base_url"),
                "dimensions": config.get("embedding_dims"),
                "chunk_size": config.get("chunk_size", 16),
                "request_timeout": config.get("request_timeout", 60),
                "max_retries": config.get("max_retries", 2)
            }
            # Filter out None values to use client defaults.
            azure_config = {k: v for k, v in azure_config.items() if v is not None}
            
            return AzureOpenAIEmbeddings(**azure_config)
        else:
            self.logger.error(f"Unsupported embedding provider: {provider}")
            raise NotImplementedError(f"Embedding provider '{provider}' is not supported yet.")
        
    def _check_collection_exists(self, collection_name: str) -> bool:
        """
        Checks if a collection exists.

        Args:
            collection_name (str): The name of the collection to check.

        Returns:
            bool: True if the collection exists, False otherwise.

        Raises:
            RuntimeError: If the check operation fails due to connection issues.
        """
        try:
            client = self.get_vector_client()
            return client.has_collection(collection_name)
        except Exception as e:
            self.logger.error(f"An error occurred while checking collection '{collection_name}': {e}")
            raise RuntimeError(f"Failed to check collection '{collection_name}'.") from e

    async def _acheck_collection_exists(self, collection_name: str) -> bool:
        """
        Asynchronously checks if a collection exists.

        Args:
            collection_name (str): The name of the collection to check.

        Returns:
            bool: True if the collection exists, False otherwise.

        Raises:
            RuntimeError: If the check operation fails due to connection issues.
        """
        try:
            client = await self.aget_async_vector_client()
            return await client.has_collection(collection_name)
        except Exception as e:
            self.logger.error(f"An error occurred while checking collection '{collection_name}': {e}")
            raise RuntimeError(f"Failed to check collection '{collection_name}'.") from e

    def _ensure_collection_exists(self, collection_name: str, embeddings: Embeddings, check_existence: bool = True):
        """
        Checks if a collection exists and creates it if it doesn't.
        This operation is wrapped in a try-except block to handle potential failures
        during collection creation.
        """
        try:
            client = self.get_vector_client()
            if check_existence and not client.has_collection(collection_name):
                self.logger.info(f"Collection '{collection_name}' does not exist. Creating it.")
                
                schema_milvus = SchemaMilvus(
                    embedding_function=embeddings,
                    collection_name=collection_name,
                    connection_args=self.connection_args,
                    index_params=self.index_params
                )

                schema_to_use = self.schema or DEFAULT_SCHEMA
                if not self.schema:
                    self.logger.warning(f"No schema provided for VDBService. Using DEFAULT_SCHEMA for collection '{collection_name}'.")
                
                schema_milvus.set_schema(schema_to_use)
                
                if not schema_milvus.create_collection():
                    raise RuntimeError(f"SchemaMilvus failed to create collection '{collection_name}'.")
        except Exception as e:
            self.logger.error(f"An error occurred while ensuring collection '{collection_name}' : {e}")
            raise RuntimeError(f"Failed to ensure collection '{collection_name}' .") from e

    async def _aensure_collection_exists(self, collection_name: str, embeddings: Embeddings, check_existence: bool = True):
        """
        Asynchronously checks if a collection exists and creates it if it doesn't.
        """
        try:
            # Call the new lazy initializer for the async client
            client = await self.aget_async_vector_client()
            if check_existence and not await client.has_collection(collection_name):
                self.logger.info(f"Collection '{collection_name}' does not exist. Creating it.")
                
                schema_milvus = SchemaMilvus(
                    embedding_function=embeddings,
                    collection_name=collection_name,
                    connection_args=self.connection_args,
                    index_params=self.index_params
                )

                #ensure using async connection alias
                schema_milvus.aclient._using = self.async_alias

                schema_to_use = self.schema or DEFAULT_SCHEMA
                if not self.schema:
                    self.logger.warning(f"No schema provided for VDBService. Using DEFAULT_SCHEMA for collection '{collection_name}'.")
                
                schema_milvus.set_schema(schema_to_use)
                
                if not await schema_milvus.acreate_collection():
                    raise RuntimeError(f"SchemaMilvus failed to create collection '{collection_name}'.")
        except Exception as e:
            self.logger.error(f"An error occurred while ensuring collection '{collection_name}' : {e}")
            raise RuntimeError(f"Failed to ensure collection '{collection_name}' .") from e

    def _is_good_connection(self, vdb_instance: Milvus, collection_name: str) -> tuple[bool, bool | None]:
        """
        Checks if the Milvus instance has a good connection by verifying collection existence.
        
        Args:
            vdb_instance (Milvus): The cached vector store instance.
            collection_name (str): The name of the collection to check.

        Returns:
            tuple[bool, bool | None]: A tuple of (is_connected, collection_exists).
                                     collection_exists is None if the connection failed.
        """
        try:
            # Use has_collection as a lightweight way to verify the connection and collection status.
            # If the server is unreachable, this will raise an exception.
            collection_exists = vdb_instance.client.has_collection(collection_name)
            if collection_exists:
                self.logger.debug(f"Connection for cached instance of '{collection_name}' is alive.")
            else:
                self.logger.warning(f"Collection '{collection_name}' not found for cached instance. It may have been dropped.")
            return True, collection_exists
        except Exception as e:
            self.logger.warning(f"Connection check failed for cached instance of '{collection_name}': {e}")
            return False, None

    async def _ais_good_connection(self, vdb_instance: Milvus, collection_name: str) -> tuple[bool, bool | None]:
        """
        Asynchronously checks if the Milvus instance has a good connection.
        """
        try:
            collection_exists = await vdb_instance.aclient.has_collection(collection_name)
            if collection_exists:
                self.logger.debug(f"Connection for cached instance of '{collection_name}' is alive.")
            else:
                self.logger.warning(f"Collection '{collection_name}' not found for cached instance. It may have been dropped.")
            return True, collection_exists
        except Exception as e:
            self.logger.warning(f"Connection check failed for cached instance of '{collection_name}': {e}")
            return False, None

    def get_vector_store(self, collection_name: str, embeddings: Embeddings = None, metric_type: str = "IP") -> Milvus:
        """
        Gets a vector store instance, creating it if it doesn't exist for the collection.
        This method validates both the embedding function and the vector store connection
        before caching the instance to prevent faulty instances from being reused.

        Args:
            collection_name (str): The name of the collection in the vector database.
            embeddings (Embeddings, optional): An embedding model instance. If None, one is created.
            metric_type (str): The distance metric for the index. Defaults to "IP".

        Returns:
            Milvus: LangChain Milvus instance, which is compatible with both Zilliz and Milvus.
        """
        if not collection_name:
            self.logger.error("get_vector_store called with no collection_name.")
            raise ValueError("collection_name must be provided.")

        # Check for a cached instance. If found, return it immediately.
        if collection_name in self._instances:
            self.logger.info(f"Returning existing vector store instance for collection: {collection_name}")
            return self._instances[collection_name]

        self.logger.info(f"Creating new vector store instance for collection: {collection_name}")
        if embeddings is None:
            embeddings = self.get_embeddings()

        # Check collection exists before proceeding. Implicit creation is not supported.
        if not self._check_collection_exists(collection_name):
            self.logger.error(f"Collection '{collection_name}' does not exist. Implicit collection creation is not supported.")
            raise ValueError(f"Collection '{collection_name}' does not exist. Please create the collection explicitly before use.")

        # # 1. Validate the embedding function before proceeding.
        # try:
        #     self.logger.info(f"Testing embedding function for collection '{collection_name}'...")
        #     embeddings.embed_query("validation_test_string")
        #     self.logger.info("Embedding function is valid.")
        # except Exception as e:
        #     self.logger.error(
        #         f"The provided embedding function is invalid and failed with error: {e}. "
        #         f"Cannot create a vector store for collection '{collection_name}'."
        #     )
        #     raise RuntimeError(f"Invalid embedding function provided.") from e

        # If embeddings are valid, proceed to create the Milvus instance.
        index_params = self.index_params or {
            "metric_type": metric_type,
            "index_type": "AUTOINDEX",
            "params": {}
        }
        
        vdb = self._create_milvus_instance_with_retry(
            collection_name=collection_name,
            embeddings=embeddings,
            index_params=index_params
        )

        # Cache the newly created instance.
        self._instances[collection_name] = vdb

        return vdb

    async def _get_or_create_async_client(self) -> AsyncMilvusClient:
        """
        Lazily initializes the AsyncMilvusClient.
        Based on grpcio source, the client MUST be initialized in a thread
        with a running event loop. Therefore, we initialize it directly in the
        main async context. The synchronous __init__ is fast enough not to
        block the event loop meaningfully.
        """
        if self._async_client is None:
            self.logger.info("Lazily initializing AsyncMilvusClient directly in the main event loop...")
            provider = self.settings.get("vector_store", {}).get("provider")
            # This is a synchronous call, but it's lightweight and must run here.
            self._async_client = self._initialize_async_milvus_client(provider)
            
        return self._async_client

    async def aget_vector_store(self, collection_name: str, embeddings: Embeddings = None, metric_type: str = "IP") -> Milvus:
        """
        Asynchronously gets a vector store instance, creating it if it doesn't exist.
        This version is optimized to handle high concurrency using a lock.
        """
        if not collection_name:
            self.logger.error("aget_vector_store called with no collection_name.")
            raise ValueError("collection_name must be provided.")

        lock = self._async_instance_locks[collection_name]
        async with lock:
            if collection_name in self._async_instances:
                self.logger.info(f"Returning existing async vector store instance for collection: {collection_name} (post-lock)")
                return self._async_instances[collection_name]

            self.logger.info(f"Creating new async vector store instance for collection: {collection_name}")
            if embeddings is None:
                embeddings = self.get_embeddings()

            # CRITICAL: Ensure the shared async client is initialized *under the lock*
            # before any operation that might use it.
            await self._get_or_create_async_client()

            # Check collection exists before proceeding. Implicit creation is not supported.
            if not await self._acheck_collection_exists(collection_name):
                self.logger.error(f"Collection '{collection_name}' does not exist. Implicit collection creation is not supported.")
                raise ValueError(f"Collection '{collection_name}' does not exist. Please create the collection explicitly before use.")

            vdb = await self._acreate_milvus_instance_with_retry(
                collection_name=collection_name,
                embeddings=embeddings,
                metric_type=metric_type
            )

            self.logger.info(f"Swapping to async alias for instance of collection {collection_name}")
            vdb.aclient._using = self.async_alias

            self._async_instances[collection_name] = vdb
            return vdb

    async def _acreate_milvus_instance_with_retry(
        self,
        embeddings: Embeddings,
        collection_name: str,
        metric_type: str = "IP",
    ) -> Milvus:
        """
        Asynchronously creates a Milvus instance with retry logic, ensuring the connection
        is established in the target thread.
        """
        retries = 3
        last_exception = None

        for attempt in range(retries):
            try:
                conn_args = self.connection_args.copy()
                # Langchain's Milvus class will use the alias to find the connection.
                conn_args["alias"] = self.sync_alias

                def _create_instance_in_thread():
                    # --- START: CRITICAL FIX ---
                    # Manually connect within the thread before creating the Milvus instance.
                    # This ensures pymilvus registers the connection details for the current thread.
                    try:
                        connections.connect(**conn_args)
                        self.logger.info(f"Successfully connected to Milvus with alias '{self.sync_alias}' in thread.")
                    except Exception as e:
                        self.logger.error(f"Failed to manually connect in thread: {e}")
                        raise

                    # Now, creating the Milvus instance will find the existing connection via the alias.
                    instance = Milvus(
                        embedding_function=embeddings,
                        collection_name=collection_name,
                        connection_args=conn_args, # Pass args for completeness
                        # metric_type=metric_type,  # <-- CRITICAL FIX: REMOVE THIS LINE
                        consistency_level="Strong",
                        # --- START: CRITICAL FIX ---
                        # Pass self.index_params to the Milvus constructor here
                        index_params=self.index_params,
                        # --- END: CRITICAL FIX ---
                    )
                    return instance
                    # --- END: CRITICAL FIX ---

                self.logger.info(f"Attempt {attempt + 1}/{retries}: Creating Milvus instance for collection '{collection_name}' in a separate thread...")
                vdb = await asyncio.to_thread(_create_instance_in_thread)
                self.logger.info("Successfully created Milvus instance.")
                return vdb

            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Attempt {attempt + 1}/{retries} failed to create Milvus instance: {e}. Retrying in {2 ** attempt}s..."
                )
                await asyncio.sleep(2 ** attempt)
        
        raise RuntimeError(
            f"Failed to create Milvus instance after {retries} retries."
        ) from last_exception

    def _create_milvus_instance_with_retry(self, collection_name: str, embeddings: Embeddings, index_params: dict, connection_args: Optional[dict] = None) -> Milvus:
        """
        Creates a Milvus instance with a retry mechanism for connection failures.
        """
        retries = 2
        conn_args = connection_args if connection_args is not None else self.connection_args
        for attempt in range(retries + 1):
            try:
                vdb = Milvus(
                    embedding_function=embeddings,
                    collection_name=collection_name,
                    connection_args=conn_args,
                    index_params=index_params
                )
                self.logger.info(f"Successfully connected to Milvus for collection '{collection_name}' on attempt {attempt + 1}.")
                return vdb  # Return on success
            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1}/{retries + 1} to connect to Milvus for collection '{collection_name}' failed: {e}"
                )
                if attempt < retries:
                    self.logger.info("Retrying in 3 seconds...")
                    time.sleep(3)
                else:
                    self.logger.error(f"Failed to connect to Milvus for collection '{collection_name}' after {retries + 1} attempts.")
                    raise RuntimeError(f"Could not connect to Milvus after {retries + 1} attempts.") from e

    def drop_collection(self, collection_name: str) -> None:
        """
        Deletes a collection from the vector database and removes it from the cache.

        Args:
            collection_name (str): The name of the collection to drop.

        Raises:
            ValueError: If collection_name is not provided.
            RuntimeError: If the operation fails on the database side.
        """
        if not collection_name:
            self.logger.error("drop_collection called without a collection_name.")
            raise ValueError("collection_name must be provided.")

        self.logger.info(f"Attempting to drop collection: {collection_name}")

        try:
            client = self.get_vector_client()
            client.drop_collection(collection_name=collection_name)
            self.logger.info(f"Successfully dropped collection: {collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to drop collection '{collection_name}': {e}")
            raise RuntimeError(f"An error occurred while dropping collection '{collection_name}'.") from e
        finally:
            # Whether successful or not, remove the stale instance from the cache.
            if collection_name in self._instances:
                del self._instances[collection_name]
                self.logger.info(f"Removed '{collection_name}' from instance cache.")

    async def adrop_collection(self, collection_name: str) -> None:
        """
        Asynchronously deletes a collection from the vector database and removes it from the cache.

        Args:
            collection_name (str): The name of the collection to drop.

        Raises:
            ValueError: If collection_name is not provided.
            RuntimeError: If the operation fails on the database side.
        """
        if not collection_name:
            self.logger.error("adrop_collection called without a collection_name.")
            raise ValueError("collection_name must be provided.")

        self.logger.info(f"Attempting to drop collection asynchronously: {collection_name}")

        try:
            client = await self.aget_async_vector_client()
            await client.drop_collection(collection_name=collection_name)
            self.logger.info(f"Successfully dropped collection asynchronously: {collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to drop collection '{collection_name}' asynchronously: {e}")
            raise RuntimeError(f"An error occurred while dropping collection '{collection_name}' asynchronously.") from e
        finally:
            # Whether successful or not, remove the stale instance from the cache.
            if collection_name in self._async_instances:
                del self._async_instances[collection_name]
                self.logger.info(f"Removed '{collection_name}' from instance cache.")

    def delete_data_by_filter(self, collection_name: str = None, filter: str = None) -> None:
        """ Delete data by filter

        Args:
            collection_name (str): collection_name
            filter (str): filter
        """
        self.logger.info(f"Delete data by filter:{filter}")

        try:
            client=self.get_vector_client()
            if collection_name is None or client is None or filter is None:
                return RuntimeError(f"collection_name must be not null or check out your client to link milvus")
            client.delete(collection_name=collection_name, filter=filter)
        except Exception as e:
            raise RuntimeError(f"delete collection data failed: {str(e)}")

    async def adelete_data_by_filter(self, collection_name: str = None, filter: str = None) -> None:
        """ Asynchronously delete data by filter

        Args:
            collection_name (str): collection_name
            filter (str): filter
        """
        self.logger.info(f"Delete data by filter asynchronously:{filter}")

        try:
            client= await self.aget_async_vector_client()
            if collection_name is None or client is None or filter is None:
                return RuntimeError(f"collection_name must be not null or check out your client to link milvus")
            await client.delete(collection_name=collection_name, filter=filter)
        except Exception as e:
            raise RuntimeError(f"delete collection data failed: {str(e)}")

    async def aget_docs_by_ids(self, collection_names: List[str], ids: List[str], embeddings: Embeddings, output_fields: List[str] = None) -> List[Document]:
        """
        Retrieves documents from multiple collections by their primary key IDs using a direct query.

        Args:
            collection_names: A list of collection names to search within.
            ids: A list of primary key IDs to retrieve.
            embeddings: The embedding function instance, required to interact with the collection.
            output_fields: A list of fields to return from the database. If None, defaults are used.

        Returns:
            A list of LangChain Document objects.
        """
        if not ids or not collection_names:
            return []

        # Default fields to retrieve if not specified. 'text' is assumed to be the page_content.
        if output_fields is None:
            # [FIX] Changed 'id' to 'source_id' and 'pk' to match the actual schema.
            # We must request fields that actually exist in the collection.
            output_fields = ["pk", "source_id", "text"]

        async def _query_one_collection(collection_name: str) -> List[Document]:
            """Helper coroutine to query a single collection."""
            try:
                # Use aget_vector_store to get a cached, async-ready instance
                vector_store = await self.aget_vector_store(collection_name, embeddings)
                
                # [FIX] The query should target the `source_id` field (VARCHAR) 
                # which stores the business-related UUIDs, not the `pk` field (INT64).
                query_field = "source_id"
                
                # Format IDs for a Milvus 'in' expression. The IDs are already strings (UUIDs).
                formatted_ids = ", ".join([f'"{str(id_val)}"' for id_val in ids])
                expr = f'{query_field} in [{formatted_ids}]'
                
                # The langchain_milvus Milvus instance doesn't expose an async query method directly.
                # We need to use the underlying async client.
                async_client = await self.aget_async_vector_client()

                self.logger.info(f"Querying collection '{collection_name}' asynchronously: {expr}")
                # Use the underlying pymilvus async client's 'query' method.
                results = await async_client.query(
                    collection_name=collection_name,
                    filter=expr,
                    output_fields=output_fields
                )
                
                # Convert the raw dictionary results from Milvus back into LangChain Document objects.
                docs = []
                for res in results:
                    # 'text' field is used as the main content of the Document.
                    page_content = res.pop('text', '') 
                    # All other retrieved fields become part of the metadata.
                    docs.append(Document(page_content=page_content, metadata=res))
                return docs
            except Exception as e:
                self.logger.error(f"Failed to retrieve documents by ID from collection '{collection_name}': {e}")
                return []

        # Run queries concurrently across all specified collections.
        search_coroutines = [_query_one_collection(name) for name in collection_names]
        list_of_doc_lists = await asyncio.gather(*search_coroutines)
        
        # Flatten the results from all collections and ensure uniqueness using a dictionary,
        # in case the same ID exists in multiple collections.
        all_docs = {}
        for doc_list in list_of_doc_lists:
            for doc in doc_list:
                # [FIX] Use 'source_id' for deduplication, as 'id' does not exist in the metadata.
                # 'source_id' is the business key we are querying by.
                doc_id = doc.metadata.get("source_id")
                if doc_id and doc_id not in all_docs:
                    all_docs[doc_id] = doc

        return list(all_docs.values())

    @staticmethod
    def delete_old_indexes(url: str = None, vdb: Milvus = None) -> (bool | None):
        """ Delete old indexes of the same source_url

        Args:
            url (str): source url
            vdb (Milvus): Milvus/Zilliz instance
        """
        # Logging is not performed in static method
        if url is None or vdb is None:
            return None

        # Delete indexes of the same source_url
        expr = f'source_url == "{url}" or source == "{url}"'
        pks = vdb.get_pks(expr)

        # Delete entities by pks
        if pks is not None and len(pks) > 0 :
            res = vdb.delete(pks)
            return res

    @staticmethod
    def delete_old_indexes_by_id(source_id: str = None, vdb: Milvus = None) -> (bool | None):
        """ Delete old indexes of the same source_id

        Args:
            source_id (str): source id
        """
        # Logging is not performed in static method
        if source_id is None or vdb is None:
            return None

        # Delete indexes of the same source_id
        expr = f'source_id == "{source_id}"'
        pks = vdb.get_pks(expr)

        # Delete entities by pks
        if pks is not None and len(pks) > 0 :
            res = vdb.delete(pks)
            return res
        