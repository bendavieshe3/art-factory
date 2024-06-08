class ArtFactoryException(Exception):
    """Base exception class for Art Factory"""


class AfWarehouseNotFoundException(ArtFactoryException):
    """Exception raised when a warehouse is not found"""


class AfConfigurationException(ArtFactoryException):
    """Exception raised for configuration errors"""


class AfDuplicateException(ArtFactoryException):
    """Exception raised for an attempt to create a functional duplicate"""


class AfDoesNotExist(ArtFactoryException):
    """Exception raised when a requested model object does not exist"""


# Add more custom exceptions as needed
