class IllegalMethodException(Exception):
    pass


class IllegalBodyException(Exception):
    pass


class InvalidRequestException(Exception):
    pass


class OperationFailureException(Exception):
    pass


class LockedRowUpdateRequest(Exception):
    pass


class PrimaryKeyMissingException(Exception):
    pass
