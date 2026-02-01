class APIClientError(Exception):
    pass

class APIRequestError(APIClientError):
    pass