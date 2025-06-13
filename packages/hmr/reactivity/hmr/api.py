import sys

from .core import HMR_CONTEXT, AsyncReloader, BaseReloader, SyncReloader
from .hooks import call_post_reload_hooks, call_pre_reload_hooks


class LifecycleMixin(BaseReloader):
    def run_with_hooks(self):
        """
        Runs the entry module within a hot module replacement context, invoking pre- and post-reload hooks.
        
        Temporarily replaces the `__main__` module with the entry module, executes pre-reload hooks, runs the entry file inside an HMR effect, and then executes post-reload hooks.
        """
        self._original_main_module = sys.modules["__main__"]
        sys.modules["__main__"] = self.entry_module
        call_pre_reload_hooks()
        self.effect = HMR_CONTEXT.effect(self.run_entry_file)
        call_post_reload_hooks()

    def clean_up(self):
        """
        Cleans up resources and restores the original `__main__` module.
        
        Disposes of the effect and entry module load, invalidates the module load, and resets the `__main__` entry in `sys.modules` to its original state.
        """
        self.effect.dispose()
        self.entry_module.load.dispose()
        self.entry_module.load.invalidate()
        sys.modules["__main__"] = self._original_main_module


class SyncReloaderAPI(SyncReloader, LifecycleMixin):
    def __enter__(self):
        """
        Enters the synchronous reloader context, running lifecycle hooks and starting the watcher thread.
        
        Returns:
            The context manager from the superclass.
        """
        from threading import Thread

        self.run_with_hooks()
        self.thread = Thread(target=self.start_watching)
        self.thread.start()
        return super()

    def __exit__(self, *_):
        """
        Cleans up resources and stops the watcher thread when exiting the context manager.
        """
        self.stop_watching()
        self.thread.join()
        self.clean_up()

    async def __aenter__(self):
        """
        Asynchronously enters the context, initializing lifecycle hooks and starting the file watcher in a background thread.
        
        Awaits the completion of pre-reload hooks and schedules the file watching process to run concurrently, then yields control before returning the superclass's asynchronous context manager.
        """
        from asyncio import ensure_future, sleep, to_thread

        await to_thread(self.run_with_hooks)
        self.future = ensure_future(to_thread(self.start_watching))
        await sleep(0)
        return super()

    async def __aexit__(self, *_):
        """
        Exits the asynchronous context manager, stopping the watcher, awaiting its completion, and cleaning up resources.
        """
        self.stop_watching()
        await self.future
        self.clean_up()


class AsyncReloaderAPI(AsyncReloader, LifecycleMixin):
    def __enter__(self):
        """
        Enters the synchronous context for the asynchronous reloader, starting the watcher in a separate thread.
        
        Initializes lifecycle hooks, launches the file-watching coroutine in a new thread with its own event loop, and waits for the watcher to be ready before returning the parent context manager.
        """
        from asyncio import run
        from threading import Event, Thread

        self.run_with_hooks()

        e = Event()

        async def task():
            """
            Signals that the watcher thread has started, then begins asynchronous file watching.
            
            This function sets the provided threading event to indicate readiness and then awaits the start of the file watching process.
            """
            e.set()
            await self.start_watching()

        self.thread = Thread(target=lambda: run(task()))
        self.thread.start()
        e.wait()
        return super()

    def __exit__(self, *_):
        """
        Cleans up resources and stops the watcher thread when exiting the context manager.
        """
        self.stop_watching()
        self.thread.join()
        self.clean_up()

    async def __aenter__(self):
        """
        Asynchronously enters the context, initializing lifecycle hooks and starting the file watcher.
        
        Awaits the execution of lifecycle hooks in a separate thread, schedules the file watching process as an asynchronous future, and yields control before returning the superclass's asynchronous context manager.
        """
        from asyncio import ensure_future, sleep, to_thread

        await to_thread(self.run_with_hooks)
        self.future = ensure_future(self.start_watching())
        await sleep(0)
        return super()

    async def __aexit__(self, *_):
        """
        Exits the asynchronous context manager, stopping the watcher, awaiting its completion, and cleaning up resources.
        """
        self.stop_watching()
        await self.future
        self.clean_up()
