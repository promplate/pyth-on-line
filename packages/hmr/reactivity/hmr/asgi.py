"""Experimental asyncio ASGI generations, independent of any server or module loader."""

import asyncio
from collections.abc import Awaitable, Callable, MutableMapping
from contextlib import suppress
from dataclasses import dataclass, field
from logging import getLogger
from math import isfinite
from typing import Any, Literal

type Message = MutableMapping[str, Any]
type Receive = Callable[[], Awaitable[Message]]
type Send = Callable[[Message], Awaitable[None]]
type ASGIApp = Callable[[Message, Receive, Send], Awaitable[None]]

logger = getLogger(__name__)


class _Lifespan:
    def __init__(self, app: ASGIApp, scope: Message, startup_timeout: float, shutdown_timeout: float, tasks: set[asyncio.Task[None]]):
        self.app = app
        self.scope = scope
        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout
        self.incoming: asyncio.Queue[Message] = asyncio.Queue()
        self.response: asyncio.Future[Message] | None = None
        self.task: asyncio.Task[None] | None = None
        self.started = False
        self.tasks = tasks
        self.abandoned = False

    def finished(self, task: asyncio.Task[None]):
        self.tasks.discard(task)
        if not task.cancelled() and (error := task.exception()) is not None and self.abandoned:
            logger.error("Lifespan failed after its cancellation deadline", exc_info=error)

    async def send(self, message: Message):
        if self.response is None or self.response.done():
            raise RuntimeError(f"Unexpected lifespan message: {message['type']}")  # noqa: TRY003
        self.response.set_result(message)

    async def exchange(self, phase: str, deadline: float):
        assert self.task is not None
        response = self.response = asyncio.get_running_loop().create_future()
        self.incoming.put_nowait({"type": f"lifespan.{phase}"})
        try:
            done, _ = await asyncio.wait((response, self.task), timeout=deadline, return_when=asyncio.FIRST_COMPLETED)
            if response in done:
                message = response.result()
                if message["type"] != f"lifespan.{phase}.complete":
                    raise RuntimeError(f"Lifespan {phase}: {message.get('message', message['type'])}")  # noqa: TRY003
            if self.task in done and (phase == "startup" or response not in done):
                self.task.result()
                raise RuntimeError(f"Lifespan exited during {phase}")  # noqa: TRY003
            if response not in done:
                raise TimeoutError(f"Lifespan {phase} timed out after {deadline}s")  # noqa: TRY003
        finally:
            self.response = None
            response.cancel()

    async def run(self):
        await self.app(self.scope, self.incoming.get, self.send)

    async def start(self):
        self.task = asyncio.create_task(self.run(), name="hmr-lifespan")
        self.tasks.add(self.task)
        self.task.add_done_callback(self.finished)
        try:
            await self.exchange("startup", self.startup_timeout)
            self.started = True
        except BaseException:
            await self.close()
            raise

    async def close(self):
        task = self.task
        if task is None:
            return
        try:
            if self.started and not task.done():
                await self.exchange("shutdown", self.shutdown_timeout)
        finally:
            self.started = False
            task.cancel()
            done, _ = await asyncio.wait((task,), timeout=self.shutdown_timeout)
            if not done:
                self.abandoned = True
                raise TimeoutError("Lifespan ignored cancellation; its resources cannot be safely reclaimed")  # noqa: TRY003
            # Retrieve errors even when startup already reported the failure.
            with suppress(asyncio.CancelledError):
                task.result()


class _Scope:
    def __init__(self, scope: Message, send: Send):
        task = asyncio.current_task()
        assert task is not None
        self.task = task
        self.type = scope["type"]
        self.raw_send = send
        self.send_lock = asyncio.Lock()
        self.expired = False
        self.closed = False

    async def send(self, message: Message):
        async with self.send_lock:
            if self.expired:
                raise asyncio.CancelledError
            await self.raw_send(message)
            if message["type"] == "websocket.close":
                self.closed = True

    async def expire(self, timeout: float):
        self.expired = True
        try:
            if self.type == "websocket" and not self.closed:
                # A task cancellation alone usually produces an abnormal 1006 close.
                async with asyncio.timeout(timeout), self.send_lock:
                    if not self.closed:
                        await self.raw_send({"type": "websocket.close", "code": 1012})
                        self.closed = True
        except (OSError, RuntimeError, TimeoutError):
            logger.debug("Could not send the generation's WebSocket close frame", exc_info=True)
        finally:
            self.task.cancel()


@dataclass(eq=False)
class _Generation:
    app: ASGIApp
    state: dict[str, Any]
    lifespan: _Lifespan | None
    scopes: set[_Scope] = field(default_factory=set)
    empty: asyncio.Event = field(default_factory=asyncio.Event)

    def __post_init__(self):
        self.empty.set()


class GenerationApp:
    """Pin each HTTP/WebSocket scope to an app, then drain it after publication.

    Lifespan is strict by default: applications must acknowledge startup and
    shutdown, or explicitly select ``lifespan="off"``. A separate shared ASGI
    lifespan may run alongside every generation's standard application lifespan.
    Use one wrapper per asyncio event loop. Modules and patches are not isolated.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        lifespan_shared: ASGIApp | None = None,
        lifespan: Literal["on", "off"] = "on",
        startup_timeout: float = 10,
        shutdown_timeout: float = 10,
        drain_timeout: float = 30,
    ):
        if lifespan not in ("on", "off"):
            raise ValueError("lifespan must be 'on' or 'off'")  # noqa: TRY003
        if any(not isfinite(value) or value <= 0 for value in (startup_timeout, shutdown_timeout, drain_timeout)):
            raise ValueError("Lifespan and drain timeouts must be finite and positive")  # noqa: TRY003
        self._initial: ASGIApp | None = app
        self._shared_app = lifespan_shared
        self._lifespan = lifespan
        self._startup_timeout = startup_timeout
        self._shutdown_timeout = shutdown_timeout
        self._drain_timeout = drain_timeout
        self._lock = asyncio.Lock()
        self._current: _Generation | None = None
        self._shared: _Lifespan | None = None
        self._scope: Message = {}
        self._shared_state: dict[str, Any] = {}
        self._drainers: set[asyncio.Task[None]] = set()
        # Include unpublished candidates: even failed startup may leave a task
        # that ignores cancellation and is still using shared resources.
        self._lifespan_tasks: set[asyncio.Task[None]] = set()
        self._shutdown_errors: list[Exception] = []
        self._started = False
        self._closing = False

    def _new_lifespan(self, app: ASGIApp, state: dict[str, Any]):
        return _Lifespan(app, {**self._scope, "state": state}, self._startup_timeout, self._shutdown_timeout, self._lifespan_tasks)

    async def _close_shared(self):
        shared_task = self._shared.task if self._shared is not None else None
        pending = [task for task in self._lifespan_tasks if task is not shared_task and not task.done()]
        if pending:
            # A timeout cannot make user code stop using its resources. Preserve
            # shared resources until even cancellation-resistant candidates exit.
            await asyncio.gather(*(asyncio.shield(task) for task in pending), return_exceptions=True)
        if self._shared is not None:
            await self._shared.close()

    async def _start_generation(self, app: ASGIApp):
        if not callable(app):
            raise TypeError("A generation must be an ASGI3 callable")  # noqa: TRY003
        state = self._shared_state.copy()
        lifespan = self._new_lifespan(app, state) if self._lifespan == "on" else None
        if lifespan is not None:
            await lifespan.start()
        return _Generation(app, state, lifespan)

    async def _startup(self, scope: Message):
        async with self._lock:
            if self._started or self._closing:
                raise RuntimeError("A GenerationApp lifespan can only run once")  # noqa: TRY003
            self._scope = {**scope, "type": "lifespan", "asgi": {"version": "3.0", "spec_version": "2.0"}}
            self._shared_state = scope.get("state", {}).copy()
            try:
                if self._shared_app is not None:
                    self._shared = self._new_lifespan(self._shared_app, self._shared_state)
                    await self._shared.start()
                assert self._initial is not None
                self._current = await self._start_generation(self._initial)
                self._initial = None
                self._started = True
            except BaseException:
                await self._close_shared()
                self._closing = True
                raise

    async def reload(self, app: ASGIApp):
        """Start and publish a candidate, leaving the current app on failure.

        This rolls back dispatch only, not module execution or external effects.
        Calls are serialized; existing requests keep running during startup.
        """
        async with self._lock:
            if not self._started or self._closing:
                raise RuntimeError("Cannot reload outside the running lifespan")  # noqa: TRY003
            candidate = await self._start_generation(app)
            if self._closing:
                if candidate.lifespan is not None:
                    await candidate.lifespan.close()
                raise RuntimeError("Application is shutting down")  # noqa: TRY003
            previous = self._current
            self._current = candidate  # No await between publication and retirement.
            assert previous is not None
            self._retire(previous)

    def _retire(self, generation: _Generation):
        task = asyncio.create_task(self._drain(generation), name="hmr-drain")
        self._drainers.add(task)
        task.add_done_callback(self._drainers.discard)

    async def _drain(self, generation: _Generation):
        try:
            try:
                async with asyncio.timeout(self._drain_timeout):
                    await generation.empty.wait()
            except TimeoutError:
                logger.warning("Generation drain deadline reached; closing %s active scopes", len(generation.scopes))
                await asyncio.gather(*(scope.expire(self._shutdown_timeout) for scope in tuple(generation.scopes)))
                # Never close resources while a scope's finally block still uses
                # them. Python cannot forcibly stop cancellation-resistant code.
                await generation.empty.wait()
            if generation.lifespan is not None:
                await generation.lifespan.close()
        except Exception as error:
            self._shutdown_errors.append(error)
            logger.exception("Generation shutdown failed")

    async def _shutdown(self):
        self._closing = True  # Prevent a pending startup from publishing afterwards.
        async with self._lock:
            if self._current is not None:
                self._retire(self._current)
                self._current = None
            await asyncio.gather(*tuple(self._drainers))
            try:
                await self._close_shared()
            finally:
                self._shared = None
                self._shared_app = None
            if self._shutdown_errors:
                raise ExceptionGroup("Generation shutdown failed", self._shutdown_errors)  # noqa: TRY003

    async def _serve_lifespan(self, scope: Message, receive: Receive, send: Send):
        message = await receive()
        if message["type"] != "lifespan.startup":
            raise RuntimeError("Expected lifespan.startup")  # noqa: TRY003
        try:
            await self._startup(scope)
        except Exception as error:
            logger.debug("Application startup failed", exc_info=True)
            await send({"type": "lifespan.startup.failed", "message": str(error)})
            return
        try:
            try:
                await send({"type": "lifespan.startup.complete"})
                message = await receive()
                if message["type"] != "lifespan.shutdown":
                    raise RuntimeError("Expected lifespan.shutdown")  # noqa: TRY003
            finally:
                await self._shutdown()
        except Exception as error:
            logger.debug("Application shutdown failed", exc_info=True)
            await send({"type": "lifespan.shutdown.failed", "message": str(error)})
            return
        await send({"type": "lifespan.shutdown.complete"})

    async def __call__(self, scope: Message, receive: Receive, send: Send):
        if scope["type"] == "lifespan":
            return await self._serve_lifespan(scope, receive, send)
        if scope["type"] not in ("http", "websocket"):
            raise ValueError(f"Unsupported ASGI scope: {scope['type']}")  # noqa: TRY003
        generation = self._current
        if generation is None or self._closing:
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1012})
            else:
                await send({"type": "http.response.start", "status": 503, "headers": []})
                await send({"type": "http.response.body", "body": b"Application unavailable"})
            return
        lease = _Scope(scope, send)
        # Pin and count before the first await, including on HTTP keep-alive.
        generation.scopes.add(lease)
        generation.empty.clear()
        try:
            await generation.app({**scope, "state": generation.state.copy()}, receive, lease.send)
        except asyncio.CancelledError:
            if not lease.expired or lease.type == "http":
                # ASGI has no transport-close event for a partial HTTP response.
                # The server aborts the stream when the application is cancelled.
                raise
        finally:
            generation.scopes.remove(lease)
            if not generation.scopes:
                generation.empty.set()
