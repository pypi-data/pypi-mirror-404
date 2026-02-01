class  QueueTelegram:

    async def message(self, tid, imog, text, button=None):
        if self.storage.index(tid) >= self.workers:
            try: await imog.edit(text=text, reply_markup=button)
            except Exception: pass

#================================================================================================
