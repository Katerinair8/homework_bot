class NotSendingError(Exception):
    pass

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
