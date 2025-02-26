from .core import AsyncReloader, SyncReloader


class SyncReloaderAPI(SyncReloader):
    def __enter__(self):
        from threading import Thread

        self.run_entry_file()
        self.thread = Thread(target=self.start_watching)
        self.thread.start()
        return super()

    def __exit__(self, *_):
        self.stop_watching()
        self.thread.join()
        self.run_entry_file.dispose()
        self.run_entry_file.invalidate()

    async def __aenter__(self):
        from asyncio import ensure_future, to_thread

        self.run_entry_file()
        self.future = ensure_future(to_thread(self.start_watching))
        return super()

    async def __aexit__(self, *_):
        self.stop_watching()
        await self.future
        self.run_entry_file.dispose()
        self.run_entry_file.invalidate()


class AsyncReloaderAPI(AsyncReloader):
    def __enter__(self):
        from asyncio import run
        from threading import Thread

        self.run_entry_file()
        self.thread = Thread(target=lambda: run(self.start_watching()))
        self.thread.start()
        return super()

    def __exit__(self, *_):
        self.stop_watching()
        self.thread.join()
        self.run_entry_file.dispose()
        self.run_entry_file.invalidate()

    async def __aenter__(self):
        from asyncio import ensure_future, to_thread

        await to_thread(self.run_entry_file)
        self.future = ensure_future(self.start_watching())
        return super()

    async def __aexit__(self, *_):
        self.stop_watching()
        await self.future
        self.run_entry_file.dispose()
        self.run_entry_file.invalidate()
