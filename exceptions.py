class NotSendingError(Exception):

    def __init__(self, message: str) -> None:
        self.message = message

class ListException(NotSendingError):
    pass

class SendMessageException(NotSendingError):
    pass

class AnswerException(Exception):
    pass

class CheckTokensException(Exception):
    pass

class EmptyListException(Exception):
    pass
