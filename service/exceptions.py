class UrlLimitReachedError(Exception):
    """Raised when a user at their creation limit tries to shorten a new url"""
    pass

class CustomUrlExistsError(Exception):
    """Raised when a custom URL is already in use"""
    pass

class AdminPrivilegesRequiredError(Exception):
    """Raised when an action requires admin privileges."""
    pass