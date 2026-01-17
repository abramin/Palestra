from typing import Protocol

class UnitOfWork(Protocol):
    def __enter__(self):
        # Initialize resources, e.g., database connection
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        # Clean up resources, commit or rollback transactions
        pass

    def commit(self):
        # Commit the transaction
        pass

    def rollback(self):
        # Rollback the transaction
        pass