class BrokenXAPIError(Exception):
    pass

class AuthenticationError(BrokenXAPIError):
    pass

class RateLimitError(BrokenXAPIError):
    pass

class ServerError(BrokenXAPIError):
    pass
