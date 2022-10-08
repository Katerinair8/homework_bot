from sqlite3 import InternalError


class ListException(Exception):
    pass

class EmptyListException(Exception):
    pass

class AnswerException(Exception):
    pass