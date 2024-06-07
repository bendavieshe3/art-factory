class ArtFactoryException(Exception):
    """Base exception class for Art Factory"""


class WarehouseNotFoundException(ArtFactoryException):
    """Exception raised when a warehouse is not found"""


class ConfigurationException(ArtFactoryException):
    """Exception raised for configuration errors"""


# Add more custom exceptions as needed
