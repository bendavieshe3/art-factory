class ArtFactoryException(Exception):
    """Base exception class for Art Factory"""

    def __init__(self, message="Art Factory Exception"):
        self.message = message
        super().__init__(self.message)


class AfWarehouseNotFoundException(ArtFactoryException):
    """Exception raised when a warehouse is not found"""

    def __init__(self, message="Warehouse not found"):
        self.message = message
        super().__init__(self.message)


class AfConfigurationException(ArtFactoryException):
    """Exception raised for configuration errors"""

    def __init__(self, message="Error found in configuration"):
        self.message = message
        super().__init__(self.message)


class AfDuplicateException(ArtFactoryException):
    """Exception raised for an attempt to create a functional duplicate"""

    def __init__(self, message="Duplicates are not allowed"):
        self.message = message
        super().__init__(self.message)


class AfDoesNotExistException(ArtFactoryException):
    """Exception raised when a requested model object does not exist"""

    def __init__(self, message="Object does not exist"):
        self.message = message
        super().__init__(self.message)


# Add more custom exceptions as needed
