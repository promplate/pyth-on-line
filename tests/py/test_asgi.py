"""Protocol and lifecycle tests; real sockets are covered by uvicorn-hmr."""

import asyncio
import json
from contextlib import suppress
from unittest import IsolatedAsyncioTestCase

from reactivity.hmr.asgi import GenerationApp


async def wait(event):
    async with asyncio.timeout(2):
        await event.wait()


class Lifespan:
    """The server side of ASGI, without reaching into wrapper internals."""

    def __init__(self, app):
        self.incoming = asyncio.Queue()
        self.outgoing = asyncio.Queue()
        self.shutdown_received = asyncio.Event()
        self.state = {}
        self.task = asyncio.create_task(app({"type": "lifespan", "asgi": {"version": "3.0", "spec_version": "2.0"}, "state": self.state}, self.receive, self.outgoing.put))

    async def receive(self):
        message = await self.incoming.get()
        if message["type"] == "lifespan.shutdown":
            self.shutdown_received.set()
        return message

    async def exchange(self, phase):
        self.incoming.put_nowait({"type": f"lifespan.{phase}"})
        async with asyncio.timeout(2):
            return await self.outgoing.get()

    async def __aenter__(self):
        message = await self.exchange("startup")
        assert message["type"] == "lifespan.startup.complete", message
        return self

    async def close(self):
        if not self.task.done():
            message = await self.exchange("shutdown")
            assert message["type"] == "lifespan.shutdown.complete", message
        async with asyncio.timeout(2):
            await self.task

    async def __aexit__(self, *_):
        await self.close()


class App:
    def __init__(self, name, events, *, extra_state=None):
        self.name = name
        self.events = events
        self.extra_state = extra_state or {}
        self.starting = asyncio.Event()
        self.allow_start = asyncio.Event()
        self.allow_start.set()
        self.stopped = asyncio.Event()
        self.finalized = asyncio.Event()
        self.entered = asyncio.Event()
        self.body_sent = asyncio.Event()
        self.allow_return = asyncio.Event()
        self.allow_return.set()
        self.request_states = []

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            self.events.append((self.name, "starting"))
            self.starting.set()
            try:
                assert (await receive())["type"] == "lifespan.startup"
                await self.allow_start.wait()
                scope["state"].update(version=self.name, **self.extra_state)
                await send({"type": "lifespan.startup.complete"})
                assert (await receive())["type"] == "lifespan.shutdown"
                self.events.append((self.name, "shutdown"))
                self.stopped.set()
                await send({"type": "lifespan.shutdown.complete"})
            finally:
                self.events.append((self.name, "finalized"))
                self.finalized.set()
            return

        self.request_states.append(scope["state"])
        self.entered.set()
        try:
            if scope.get("path") == "/raise":
                raise ValueError("expected request failure")  # noqa: TRY003
            if scope["type"] == "websocket":
                assert (await receive())["type"] == "websocket.connect"
                await send({"type": "websocket.accept"})
                await receive()
                return
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": json.dumps({"version": self.name}).encode()})
            self.body_sent.set()
            await self.allow_return.wait()
        finally:
            self.events.append((self.name, "scope finished"))


async def http(app, path="/"):
    messages = []

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(message):
        messages.append(message)

    async with asyncio.timeout(2):
        await app({"type": "http", "asgi": {"version": "3.0"}, "path": path, "state": {}}, receive, send)
    return json.loads(b"".join(message.get("body", b"") for message in messages))


class GenerationTests(IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        pending = [task for task in asyncio.all_tasks() if task.get_name().startswith("hmr-") and not task.done()]
        self.assertEqual(pending, [], "generation lifecycle tasks outlived server shutdown")

    async def test_startup_gate_rejects_unhealthy_candidates_and_keeps_serving(self):
        events = []
        old = App("old", events)
        wrapper = GenerationApp(old, startup_timeout=0.03)
        async with Lifespan(wrapper):
            for failure in ("failed", "raise", "return", "return after startup", "timeout", "wrong event"):
                with self.subTest(failure=failure):
                    finalized = asyncio.Event()

                    async def bad(scope, receive, send, failure=failure, finalized=finalized):
                        assert scope["type"] == "lifespan"
                        assert (await receive())["type"] == "lifespan.startup"
                        try:
                            if failure == "failed":
                                await send({"type": "lifespan.startup.failed", "message": "expected failure"})
                            elif failure == "raise":
                                raise ValueError("expected startup exception")  # noqa: TRY003
                            elif failure == "timeout":
                                await asyncio.Event().wait()
                            elif failure == "return after startup":
                                await send({"type": "lifespan.startup.complete"})
                            elif failure == "wrong event":
                                await send({"type": "lifespan.shutdown.complete"})
                        finally:
                            finalized.set()

                    async with asyncio.timeout(1):
                        with self.assertRaises((RuntimeError, ValueError, TimeoutError)):
                            await wrapper.reload(bad)
                    await wait(finalized)
                    self.assertEqual(await http(wrapper), {"version": "old"})
                    self.assertFalse(old.stopped.is_set())
            recovered = App("recovered", events)
            await wrapper.reload(recovered)
            self.assertEqual(await http(wrapper), {"version": "recovered"})
            await wait(old.stopped)
        self.assertTrue(recovered.finalized.is_set())

    async def test_failed_initial_generation_cleans_shared_and_reports_application_error(self):
        events = []
        shared = App("shared", events)

        async def failed(_scope, receive, send):
            await receive()
            await send({"type": "lifespan.startup.failed", "message": "cannot initialize test application"})

        lifespan = Lifespan(GenerationApp(failed, lifespan_shared=shared))
        message = await lifespan.exchange("startup")
        async with asyncio.timeout(1):
            await lifespan.task
        self.assertEqual(message["type"], "lifespan.startup.failed")
        self.assertIn("cannot initialize test application", message["message"])
        self.assertTrue(shared.finalized.is_set())
        self.assertEqual(events.count(("shared", "shutdown")), 1)

    async def test_shared_shutdown_failure_is_reported_to_server(self):
        events = []

        async def shared(_scope, receive, send):
            await receive()
            await send({"type": "lifespan.startup.complete"})
            await receive()
            await send({"type": "lifespan.shutdown.failed", "message": "expected shared shutdown failure"})

        lifespan = await Lifespan(GenerationApp(App("one", events), lifespan_shared=shared)).__aenter__()
        message = await lifespan.exchange("shutdown")
        async with asyncio.timeout(1):
            await lifespan.task
        self.assertEqual(message["type"], "lifespan.shutdown.failed")
        self.assertIn("expected shared shutdown failure", message["message"])

    async def test_noncooperative_lifespans_keep_shared_resources_until_they_finish(self):
        for phase in ("initial startup", "candidate startup", "retired shutdown"):
            with self.subTest(phase=phase):
                events = []
                shared = App("shared", events)
                cancelled = asyncio.Event()
                release = asyncio.Event()

                async def resistant(_scope, receive, send, phase=phase, cancelled=cancelled, release=release, events=events):
                    await receive()
                    if phase == "retired shutdown":
                        await send({"type": "lifespan.startup.complete"})
                        await receive()
                    try:
                        await asyncio.Event().wait()
                    except asyncio.CancelledError:
                        cancelled.set()
                        await release.wait()
                    finally:
                        events.append(("resistant", "finalized"))

                wrapper = GenerationApp(
                    App("current", events) if phase == "candidate startup" else resistant,
                    lifespan_shared=shared,
                    startup_timeout=0.02,
                    shutdown_timeout=0.02,
                )
                lifespan = Lifespan(wrapper)
                shutting_down = False
                try:
                    if phase == "initial startup":
                        operation = asyncio.create_task(lifespan.exchange("startup"))
                    else:
                        await lifespan.__aenter__()
                        if phase == "candidate startup":
                            async with asyncio.timeout(1):
                                with self.assertRaisesRegex(TimeoutError, "ignored cancellation"):
                                    await wrapper.reload(resistant)
                            # The timeout returns even though candidate cleanup is
                            # still running, and the published generation survives.
                            self.assertFalse(release.is_set())
                            self.assertEqual(await http(wrapper), {"version": "current"})
                        else:
                            await wrapper.reload(App("replacement", events))
                            self.assertEqual(await http(wrapper), {"version": "replacement"})
                        operation = asyncio.create_task(lifespan.exchange("shutdown"))
                        shutting_down = True
                    await wait(cancelled)
                    # Give close() time to exhaust its cancellation timeout. An
                    # outer shutdown must still wait rather than close shared.
                    done, _ = await asyncio.wait((operation,), timeout=0.08)
                    self.assertEqual(done, set())
                    self.assertFalse(shared.stopped.is_set())
                finally:
                    release.set()
                    if phase != "initial startup" and not shutting_down and not lifespan.task.done():
                        lifespan.incoming.put_nowait({"type": "lifespan.shutdown"})
                    async with asyncio.timeout(1):
                        await lifespan.task
                message = await operation
                expected = {
                    "candidate startup": "lifespan.shutdown.complete",
                    "initial startup": "lifespan.startup.failed",
                    "retired shutdown": "lifespan.shutdown.failed",
                }[phase]
                self.assertEqual(message["type"], expected)
                if phase == "initial startup":
                    self.assertIn("ignored cancellation", message["message"])
                self.assertLess(events.index(("resistant", "finalized")), events.index(("shared", "shutdown")))

    async def test_shared_lifespan_and_per_generation_state_do_not_mix(self):
        events = []
        resource = object()
        shared = App("shared", events, extra_state={"resource": resource})
        first = App("one", events, extra_state={"old_only": True})
        second = App("two", events)
        wrapper = GenerationApp(first, lifespan_shared=shared)
        async with Lifespan(wrapper) as lifespan:
            await http(wrapper)
            first_state = first.request_states[-1]
            self.assertIs(first_state["resource"], resource)
            first_state["request_local"] = True
            await http(wrapper)
            self.assertNotIn("request_local", first.request_states[-1])
            await wrapper.reload(second)
            await http(wrapper)
            second_state = second.request_states[-1]
            self.assertIs(second_state["resource"], resource)
            self.assertNotIn("old_only", second_state)
            self.assertEqual(second_state["version"], "two")
            self.assertEqual(first_state["version"], "one")
            self.assertNotIn("old_only", lifespan.state)
            await wait(first.stopped)
            self.assertFalse(shared.stopped.is_set())
        self.assertEqual(events.count(("shared", "starting")), 1)
        self.assertEqual(events.count(("shared", "shutdown")), 1)
        self.assertLess(events.index(("two", "finalized")), events.index(("shared", "shutdown")))

    async def test_scope_remains_pinned_after_last_body_until_app_cleanup(self):
        events = []
        first = App("one", events)
        first.allow_return.clear()
        second = App("two", events)
        third = App("three", events)
        wrapper = GenerationApp(first)
        async with Lifespan(wrapper):
            request = asyncio.create_task(http(wrapper))
            try:
                await wait(first.body_sent)
                await wrapper.reload(second)
                await wrapper.reload(third)
                self.assertEqual(await http(wrapper), {"version": "three"})
                await wait(second.stopped)
                self.assertFalse(first.stopped.is_set())
            finally:
                first.allow_return.set()
                self.assertEqual(await request, {"version": "one"})
            await wait(first.stopped)
        self.assertLess(events.index(("one", "scope finished")), events.index(("one", "shutdown")))

    async def test_scope_error_and_cancellation_release_generation(self):
        for outcome in ("raise", "cancel"):
            with self.subTest(outcome=outcome):
                events = []
                first = App("one", events)
                wrapper = GenerationApp(first)
                async with Lifespan(wrapper):
                    if outcome == "raise":
                        with self.assertRaisesRegex(ValueError, "expected request failure"):
                            await http(wrapper, "/raise")
                    else:
                        first.allow_return.clear()
                        request = asyncio.create_task(http(wrapper))
                        await wait(first.body_sent)
                        request.cancel()
                        with self.assertRaises(asyncio.CancelledError):
                            await request
                    await wrapper.reload(App("two", events))
                    await wait(first.stopped)
                    self.assertLess(events.index(("one", "scope finished")), events.index(("one", "shutdown")))

    async def test_deadline_closes_websocket_before_cancelling_and_stopping_lifespan(self):
        events = []
        first = App("one", events)
        wrapper = GenerationApp(first, drain_timeout=0.03)
        incoming = asyncio.Queue()
        incoming.put_nowait({"type": "websocket.connect"})
        closed = asyncio.Event()
        messages = []

        async def send(message):
            messages.append(message)
            if message["type"] == "websocket.close":
                events.append(("one", "close frame"))
                closed.set()

        async with Lifespan(wrapper):
            connection = asyncio.create_task(wrapper({"type": "websocket", "asgi": {"version": "3.0"}, "state": {}}, incoming.get, send))
            await wait(first.entered)
            await wrapper.reload(App("two", events))
            await wait(closed)
            self.assertEqual([message["code"] for message in messages if message["type"] == "websocket.close"], [1012])
            with suppress(asyncio.CancelledError):
                async with asyncio.timeout(1):
                    await connection
            await wait(first.stopped)
        self.assertLess(events.index(("one", "close frame")), events.index(("one", "scope finished")))
        self.assertLess(events.index(("one", "scope finished")), events.index(("one", "shutdown")))

    async def test_concurrent_reloads_serialize_and_cancelled_startup_does_not_publish(self):
        events = []
        first, second, third = (App(name, events) for name in ("one", "two", "three"))
        second.allow_start.clear()
        third.allow_start.clear()
        wrapper = GenerationApp(first)
        async with Lifespan(wrapper):
            loading_second = asyncio.create_task(wrapper.reload(second))
            await wait(second.starting)
            loading_third = asyncio.create_task(wrapper.reload(third))
            await asyncio.sleep(0)
            self.assertEqual(await http(wrapper), {"version": "one"})
            self.assertFalse(third.starting.is_set())
            loading_second.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await loading_second
            await wait(second.finalized)
            await wait(third.starting)
            self.assertEqual(await http(wrapper), {"version": "one"})
            third.allow_start.set()
            async with asyncio.timeout(1):
                await loading_third
            self.assertEqual(await http(wrapper), {"version": "three"})
            self.assertNotIn(("two", "scope finished"), events)
        self.assertTrue(first.finalized.is_set())
        self.assertTrue(third.finalized.is_set())

    async def test_shutdown_with_pending_candidate_cleans_generations_before_shared(self):
        events = []
        shared, first, second = (App(name, events) for name in ("shared", "one", "two"))
        second.allow_start.clear()
        wrapper = GenerationApp(first, lifespan_shared=shared, startup_timeout=0.1)
        lifespan = await Lifespan(wrapper).__aenter__()
        loading = asyncio.create_task(wrapper.reload(second))
        await wait(second.starting)
        closing = asyncio.create_task(lifespan.close())
        await wait(lifespan.shutdown_received)
        second.allow_start.set()
        async with asyncio.timeout(1):
            await asyncio.gather(loading, closing, return_exceptions=True)
        self.assertTrue(first.finalized.is_set())
        self.assertTrue(second.finalized.is_set())
        self.assertTrue(shared.finalized.is_set())
        self.assertLess(events.index(("one", "finalized")), events.index(("shared", "shutdown")))
        self.assertLess(events.index(("two", "finalized")), events.index(("shared", "shutdown")))
        self.assertEqual(events.count(("shared", "shutdown")), 1)
        self.assertIsInstance(loading.exception(), RuntimeError)
        await closing

    async def test_explicit_lifespan_off_still_runs_shared_resources(self):
        events = []
        shared = App("shared", events)

        async def plain(scope, _receive, send):
            self.assertEqual(scope["type"], "http")
            self.assertEqual(scope["state"]["version"], "shared")
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b'{"version":"plain"}'})

        wrapper = GenerationApp(plain, lifespan_shared=shared, lifespan="off")
        async with Lifespan(wrapper):
            self.assertEqual(await http(wrapper), {"version": "plain"})
            await wrapper.reload(plain)
            self.assertEqual(await http(wrapper), {"version": "plain"})
        self.assertEqual(events.count(("shared", "starting")), 1)
        self.assertEqual(events.count(("shared", "shutdown")), 1)
