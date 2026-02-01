class QueuedAlready(Exception):
    pass

class RateLimited(Exception):
    pass

class Cancelled(Exception):
    pass

class Queuefull(Exception):
    pass
