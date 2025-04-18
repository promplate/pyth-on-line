from .core import AsyncReloader, BaseReloader, SyncReloader, create_effect
from .hooks import call_post_reload_hooks, call_pre_reload_hooks


class LifecycleMixin(BaseReloader):
    def run_with_hooks(self):
        call_pre_reload_hooks()
        self.effect = create_effect(self.run_entry_file)
        call_post_reload_hooks()

    def clean_up(self):
        self.effect.dispose()
        self.entry_module.load.dispose()
        self.entry_module.load.invalidate()


class SyncReloaderAPI(SyncReloader, LifecycleMixin):
    def __enter__(self):
        from threading import Thread

        self.run_with_hooks()
        self.thread = Thread(target=self.start_watching)
        self.thread.start()
        return super()

    def __exit__(self, *_):
        self.stop_watching()
        self.thread.join()
        self.clean_up()

    async def __aenter__(self):
        from asyncio import ensure_future, to_thread

        await to_thread(self.run_with_hooks)
        self.future = ensure_future(to_thread(self.start_watching))
        return super()

    async def __aexit__(self, *_):
        self.stop_watching()
        await self.future
        self.clean_up()


class AsyncReloaderAPI(AsyncReloader, LifecycleMixin):
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
        self.clean_up()

    async def __aenter__(self):
        from asyncio import ensure_future, to_thread

        await to_thread(self.run_with_hooks)
        self.future = ensure_future(self.start_watching())
        return super()

    async def __aexit__(self, *_):
        self.stop_watching()
        await self.future
        self.clean_up()
