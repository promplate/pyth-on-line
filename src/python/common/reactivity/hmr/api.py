from .core import AsyncReloader, BaseReloader, SyncReloader
from .hooks import call_post_reload_hooks, call_pre_reload_hooks


def _clean_up(r: BaseReloader):
    r.entry_module.load.dispose()
    r.entry_module.load.invalidate()


class ReloadHooksMixin(BaseReloader):
    def run_with_hooks(self):
        call_pre_reload_hooks()
        self.run_entry_file()
        call_post_reload_hooks()


class SyncReloaderAPI(SyncReloader, ReloadHooksMixin):
    def __enter__(self):
        from threading import Thread

        self.run_with_hooks()
        self.thread = Thread(target=self.start_watching)
        self.thread.start()
        return super()

    def __exit__(self, *_):
        self.stop_watching()
        self.thread.join()
        _clean_up(self)

    async def __aenter__(self):
        from asyncio import ensure_future, to_thread

        await to_thread(self.run_with_hooks)
        self.future = ensure_future(to_thread(self.start_watching))
        return super()

    async def __aexit__(self, *_):
        self.stop_watching()
        await self.future
        _clean_up(self)


class AsyncReloaderAPI(AsyncReloader, ReloadHooksMixin):
    def __enter__(self):
        from asyncio import run
        from threading import Thread

        self.run_with_hooks()
        self.thread = Thread(target=lambda: run(self.start_watching()))
        self.thread.start()
        return super()

    def __exit__(self, *_):
        self.stop_watching()
        self.thread.join()
        _clean_up(self)

    async def __aenter__(self):
        from asyncio import ensure_future, to_thread

        await to_thread(self.run_with_hooks)
        self.future = ensure_future(self.start_watching())
        return super()

    async def __aexit__(self, *_):
        self.stop_watching()
        await self.future
        _clean_up(self)
