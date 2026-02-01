import os
import urllib.request
from pathlib import Path
from urllib.parse import quote_plus

import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection

class MongoDBClient:
    """
    MongoDBClient is a handler for managing MongoDB connections safely in forking environments.
    It lazily initializes the MongoClient to avoid fork-safety warnings and supports optimized
    connection strings for both single server and replica set configurations with automatic
    retry on failover. Provides dictionary-like access to collections within a specified user
    namespace and includes a method to execute operations with automatic retry on connection
    failures. Also includes a static method to ensure the existence of a specific index on a collection.
    """

    def __init__(self, user: str = 'SharedData') -> None:
        """
        Initialize MongoDB client handler by constructing the appropriate connection string.
        
        This constructor sets up the MongoDB connection string based on environment variables.
        If the environment variable 'MONGODB_REPLICA_SET' is not present, it creates a connection
        string for a single MongoDB server. Otherwise, it creates a connection string optimized
        for a replica set with failover and retry options enabled.
        
        Args:
            user (str): The database user namespace. Defaults to 'SharedData'.
        
        Attributes:
            _user (str): The user namespace for the database.
            mongodb_conn_str (str): The constructed MongoDB connection string.
            _client: Placeholder for the MongoDB client instance, initialized on first use.
        """
        self._user = user
        self._is_docdb = 'MONGODB_DOCDB' in os.environ
        self._ca_cert_path = None
        
        mongodb_host = os.environ["MONGODB_HOST"]
        
        # Set default port based on connection type
        default_port = "8330" if self._is_docdb else "27017"
        if ':' not in mongodb_host:
            mongodb_host += ':' + os.environ.get("MONGODB_PORT", default_port)

        if self._is_docdb:
            # AWS DocumentDB connection with TLS
            # Connection string format from AWS cluster page:
            # mongodb://user:pwd@host:port/?tls=true&tlsCAFile=<cert>&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false
            self._ca_cert_path = self._get_ca_cert_path()
            encoded_user = quote_plus(os.environ["MONGODB_USER"])
            encoded_pwd = quote_plus(os.environ["MONGODB_PWD"])
            self.mongodb_conn_str = (
                f'mongodb://{encoded_user}:{encoded_pwd}@{mongodb_host}/'
                f'?tls=true'
                f'&tlsCAFile={self._ca_cert_path}'
                f'&replicaSet=rs0'
                f'&readPreference=secondaryPreferred'
                f'&retryWrites=false'  # DocumentDB does not support retryWrites
                f'&serverSelectionTimeoutMS=10000'
            )
        elif 'MONGODB_REPLICA_SET' not in os.environ:
            # Single server connection (MONGODB_HOST includes port: '10.0.0.50:27017')
            self.mongodb_conn_str = (
                f'mongodb://{os.environ["MONGODB_USER"]}:'
                f'{os.environ["MONGODB_PWD"]}@'
                f'{mongodb_host}/'
                f'?retryWrites=true'  # Automatically retry writes on failover
                f'&retryReads=true'  # Automatically retry reads on failover
            )
        else:
            # Replica set connection string optimized for fast failover with aggressive timeouts
            self.mongodb_conn_str = (
                f'mongodb://{os.environ["MONGODB_USER"]}:'
                f'{os.environ["MONGODB_PWD"]}@'
                f'{mongodb_host}/'
                f'?replicaSet={os.environ["MONGODB_REPLICA_SET"]}'
                f'&authSource={os.environ["MONGODB_AUTH_DB"]}'
                f'&retryWrites=true'  # Automatically retry writes on failover
                f'&retryReads=true'  # Automatically retry reads on failover
                f'&readPreference=primary'  # REQUIRED: Force reads from primary only
                f'&w=1'  # REQUIRED: Write to primary only (explicit override)
                f'&serverSelectionTimeoutMS=10000'  # Allow time for failover detection
            )
        self._client = None  # Client will be created on first access
        self._pid = None  # Track process ID for fork detection

    @staticmethod
    def _get_ca_cert_path() -> str:
        """
        Download AWS DocumentDB CA certificate to SOURCE_FOLDER if not present.
        
        Requires MONGODB_CA_CERT_URL environment variable to be set.
        The certificate filename is extracted from the URL.
        
        Returns:
            str: The full path to the CA certificate file.
        
        Raises:
            RuntimeError: If MONGODB_CA_CERT_URL is not set or download fails.
        """
        if 'MONGODB_CA_CERT_URL' not in os.environ:
            raise RuntimeError(
                "MONGODB_CA_CERT_URL environment variable is required when MONGODB_DOCDB is set. "
                "Example: https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem"
            )
        
        ca_cert_url = os.environ['MONGODB_CA_CERT_URL']
        cert_filename = ca_cert_url.split('/')[-1]  # Extract filename from URL
        
        source_folder = os.environ['SOURCE_FOLDER']
        Path(source_folder).mkdir(parents=True, exist_ok=True)
        cert_path = os.path.join(source_folder, cert_filename)
        
        if os.path.exists(cert_path):
            return cert_path
        
        try:
            urllib.request.urlretrieve(ca_cert_url, cert_path)
            return cert_path
        except Exception as e:
            raise RuntimeError(f"Failed to download CA certificate from {ca_cert_url}: {e}")

    @property
    def client(self) -> MongoClient:
        """
        Lazily initialize the MongoClient for this process with fork detection.
        
        Ensures process-safety by detecting fork events (when Gunicorn creates worker processes)
        and creating a new client instance per process. This prevents sharing MongoDB connections
        across processes, which would cause errors. PyMongo's built-in connection pool (default 100
        connections) is automatically process-safe with this pattern.
        """
        current_pid = os.getpid()
        
        # Detect if we're in a new process (fork event) or client hasn't been created yet
        if self._client is None or self._pid != current_pid:
            # Close old client if it exists (from parent process)
            if self._client is not None:
                try:
                    self._client.close()
                except:
                    pass  # Ignore errors closing stale client
            
            # Create new client for this process with built-in connection pooling
            if self._is_docdb:
                # Suppress DocumentDB compatibility warning from PyMongo
                import warnings
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message=".*DocumentDB.*")
                    self._client = MongoClient(
                        self.mongodb_conn_str,
                        connect=False,  # Delay connection until first operation (lazy)
                    )
            else:
                self._client = MongoClient(
                    self.mongodb_conn_str,
                    connect=False,  # Delay connection until first operation (lazy)
                )
            self._pid = current_pid
        
        return self._client

    @client.setter
    def client(self, value: MongoClient) -> None:
        """
        Set the MongoDB client instance.
        
        Parameters:
            value (MongoClient): An instance of MongoClient to be used as the database client.
        
        Returns:
            None
        """
        self._client = value

    def __getitem__(self, collection_name: str) -> Collection:
        """
        Retrieve a MongoDB collection from the user's database using dictionary-like access.
        
        Args:
            collection_name (str): The name of the collection to access.
        
        Returns:
            Collection: The MongoDB collection corresponding to the given name.
        """
        return self.client[self._user][collection_name]
    
    def execute_with_retry(self, operation, max_retries: int = 3, delay: float = 0.5):
        """
        Execute a MongoDB operation with automatic retries on connection-related failures.
        
        This method attempts to execute the provided MongoDB operation callable. If the operation
        raises a connection-related exception (such as ServerSelectionTimeoutError, NetworkTimeout,
        or AutoReconnect), it will retry the operation up to `max_retries` times with exponential
        backoff delay between attempts. On each retry, the MongoDB client is closed and reset to
        force a fresh connection.
        
        Args:
            operation (callable): A callable that performs the MongoDB operation.
            max_retries (int, optional): Maximum number of retry attempts. Defaults to 3.
            delay (float, optional): Initial delay between retries in seconds. Defaults to 0.5.
        
        Returns:
            The result of the MongoDB operation if successful.
        
        Raises:
            Exception: Re-raises the last connection-related exception if all retries fail.
            Exception: Immediately raises any non-connection-related exceptions encountered during operation.
        """
        import time
        
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                return operation()
            except (pymongo.errors.ServerSelectionTimeoutError, 
                    pymongo.errors.NetworkTimeout,
                    pymongo.errors.AutoReconnect) as e:
                last_exception = e
                if attempt < max_retries:
                    # Force client recreation on connection errors
                    if self._client:
                        self._client.close()
                        self._client = None
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    continue
                raise
            except Exception as e:
                # Don't retry on non-connection errors
                raise
        
        raise last_exception
        
    @staticmethod
    def ensure_index(coll, index_fields, **kwargs):
        """
        Ensure that a specified index exists on the given MongoDB collection.
        
        This method checks if an index with the specified fields and options already exists on the collection.
        If the index does not exist, it creates the index using the provided fields and options.
        
        Parameters:
            coll (pymongo.collection.Collection): The MongoDB collection to operate on.
            index_fields (list of tuples): A list of (field, direction) pairs specifying the index keys,
                e.g., [('status', pymongo.ASCENDING)].
            **kwargs: Additional keyword arguments to pass to the create_index method, such as 'name' or 'unique'.
        
        Returns:
            None
        """
        existing_indexes = coll.index_information()

        # Normalize input index spec for comparison
        target_index = pymongo.helpers._index_list(index_fields)

        for index_name, index_data in existing_indexes.items():
            if pymongo.helpers._index_list(index_data['key']) == target_index:
                return  # Index already exists

        coll.create_index(index_fields, **kwargs)