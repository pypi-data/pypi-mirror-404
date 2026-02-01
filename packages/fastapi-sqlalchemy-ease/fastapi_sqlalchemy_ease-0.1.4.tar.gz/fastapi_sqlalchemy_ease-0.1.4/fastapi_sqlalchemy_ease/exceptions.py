class DatabaseError(Exception):
    """Base error - all other errors inherit from this"""
    pass

class DatabaseNotInitializedError(DatabaseError):
    """Raised when someone uses db before calling init_app()"""
    pass