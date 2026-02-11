class ProcessingError(Exception):
    def __init__(self, reason: str, retryable: bool):
        self.reason = reason
        self.retryable = retryable
