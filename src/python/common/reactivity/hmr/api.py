from .core import AsyncReloader, BaseReloader, SyncReloader


def _clean_up(r: BaseReloader):
    r.run_entry_file.dispose()
    r.run_entry_file.invalidate()
    r.entry_module.load.dispose()
    r.entry_module.load.invalidate()


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
        _clean_up(self)

    async def __aenter__(self):
        from asyncio import ensure_future, to_thread

        await to_thread(self.run_entry_file)
        self.future = ensure_future(to_thread(self.start_watching))
        return super()

    async def __aexit__(self, *_):
        self.stop_watching()
        await self.future
        _clean_up(self)


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
        _clean_up(self)

    async def __aenter__(self):
        from asyncio import ensure_future, to_thread

        await to_thread(self.run_entry_file)
        self.future = ensure_future(self.start_watching())
        return super()

    async def __aexit__(self, *_):
        self.stop_watching()
        await self.future
        _clean_up(self)
