from .function01 import Queues
from .function01 import QUEUES
from .function03 import QueueCore
from ..exceptions import Queuefull
from .function02 import QueueTelegram
from ..exceptions import QueuedAlready
#================================================================================================

class Queue(QueueCore, QueueTelegram):

    def __init__(self, **kwargs):
        self.waiting = kwargs.get("wait", 1)
        self.limited = kwargs.get("limit", 100)
        self.workers = kwargs.get("workers", 1)
        self.maxsize = kwargs.get("maxsize", 100)
        self.storage = kwargs.get("storage", Queues)

#================================================================================================

    async def total(self):
        return len(self.storage)

    async def remove(self, tid, uid=None):
        QUEUES.remove(uid) if uid and uid in QUEUES else 0
        self.storage.remove(tid) if tid in self.storage else 0

    async def clean(self, uid=None, tid=None):
        QUEUES.remove(uid) if uid else QUEUES.clear()
        self.storage.remove(tid) if tid else self.storage.clear()

    async def position(self, tid):
        return self.storage.index(tid) - self.workers + 1 if tid in self.storage else 0
    
    async def add(self, tid, priority=-1):
        if len(self.storage) >= self.maxsize: raise Queuefull("Hey now I'm very busy.")
        if tid in self.storage: raise QueuedAlready("Already Added!")
        self.storage.append(tid) if priority == -1 else self.storage.insert(priority, tid)

#================================================================================================
