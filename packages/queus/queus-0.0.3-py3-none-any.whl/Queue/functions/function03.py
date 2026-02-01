import asyncio
from collections import Counter
from .function01 import QUEUES
from ..exceptions import RateLimited
#==================================================================================================================

class QueueCore:

    async def queue(self, tid):
        while tid in self.storage:
            if self.storage.index(tid) >= self.workers: await asyncio.sleep(self.waiting)
            else: break

#==================================================================================================================

    async def checklimit(self, uid):
        mains = Counter(QUEUES)[uid]
        if mains >= self.limited:
            raise RateLimited(f"Reached Your limit {self.limited}/{self.limited} please wait few minutes.")
        else:
            QUEUES.append(uid)

#==================================================================================================================
