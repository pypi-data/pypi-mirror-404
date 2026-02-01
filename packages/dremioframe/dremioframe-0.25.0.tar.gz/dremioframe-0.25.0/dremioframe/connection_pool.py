from typing import List, Optional, Dict, Any
from queue import Queue, Empty
from contextlib import contextmanager
from dremioframe.client import DremioClient
import time

class ConnectionPool:
    """
    Manages a pool of DremioClient instances to reuse connections.
    """
    def __init__(self, max_size: int = 5, timeout: int = 30, **client_kwargs):
        self.max_size = max_size
        self.timeout = timeout
        self.client_kwargs = client_kwargs
        self.pool: Queue[DremioClient] = Queue(maxsize=max_size)
        self.created_count = 0
        
        # Pre-fill pool? No, lazy creation is better usually.
        # Or fill min_size? Let's stick to lazy for now.

    def _create_client(self) -> DremioClient:
        """Create a new client instance."""
        return DremioClient(**self.client_kwargs)

    def get_client(self) -> DremioClient:
        """
        Get a client from the pool.
        If pool is empty and created_count < max_size, create new.
        If pool is empty and created_count >= max_size, wait up to timeout.
        """
        try:
            # Try to get from pool immediately
            return self.pool.get(block=False)
        except Empty:
            # Pool is empty
            if self.created_count < self.max_size:
                # Create new
                self.created_count += 1
                return self._create_client()
            else:
                # Wait for a client to be returned
                try:
                    return self.pool.get(block=True, timeout=self.timeout)
                except Empty:
                    raise TimeoutError("Connection pool exhausted and timed out.")

    def release_client(self, client: DremioClient):
        """
        Return a client to the pool.
        """
        try:
            self.pool.put(client, block=False)
        except Exception:
            # Pool full? Should not happen if logic is correct.
            # If full, maybe close the client?
            # For now, just ignore or log.
            pass

    @contextmanager
    def client(self):
        """
        Context manager for getting and releasing a client.
        Usage:
            with pool.client() as client:
                client.sql(...)
        """
        client = self.get_client()
        try:
            yield client
        finally:
            self.release_client(client)

    def close_all(self):
        """
        Close all clients in the pool.
        Note: DremioClient doesn't have explicit close() usually (FlightClient handles it),
        but if we added session management, we might need it.
        """
        while not self.pool.empty():
            try:
                client = self.pool.get(block=False)
                # client.close() if exists
            except Empty:
                break
        self.created_count = 0
