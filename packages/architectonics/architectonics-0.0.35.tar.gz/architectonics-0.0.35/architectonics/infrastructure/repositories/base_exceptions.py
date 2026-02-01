class ObjectNotFoundException(Exception):
    """Exception raised when can't find a row."""


class ObjectAlreadyExistsException(Exception):
    """Exception raised when unique constraint failes."""


class IntegrityErrorException(Exception):
    """Exception raised when integrity constraint fails."""
