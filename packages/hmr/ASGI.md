# Experimental ASGI generations

`reactivity.hmr.asgi.GenerationApp` keeps one server-facing ASGI3 callable while
application instances change. The prototype uses asyncio and the Python standard
library; it does not import Uvicorn or change how Python modules are loaded.

```python
from reactivity.hmr.asgi import GenerationApp

wrapper = GenerationApp(
    initial_app,
    lifespan_shared=shared_resources,  # optional ASGI lifespan callable
    startup_timeout=10,
    shutdown_timeout=10,
    drain_timeout=30,
)

# Give the server this same wrapper for its entire lifetime, with lifespan enabled.
# After the reloader has produced another ASGI3 application:
await wrapper.reload(candidate_app)
```

## Publication and draining

A reload starts the candidate's standard ASGI lifespan while the current app
continues serving. Only `lifespan.startup.complete` publishes the candidate.
`startup.failed`, an exception, premature return, or a startup timeout rejects it
and leaves dispatch unchanged. Candidate cleanup is awaited before reload returns.
Reload calls are serialized. Applications without lifespan support must explicitly
use `lifespan="off"`; exceptions are never interpreted as successful startup.

Each HTTP request selects the current generation, including subsequent requests
on an existing keep-alive connection. A WebSocket keeps that selection for its
entire connection. An SSE stream is one long HTTP scope. The generation remains
active until the ASGI callable actually returns, including background work and
`finally` blocks after sending the last response body.

After publication, the previous generation receives no new scopes. Once its
active scopes finish, its lifespan shuts down. Multiple older generations can
drain independently. At `drain_timeout`, the wrapper sends WebSocket close code
1012, then cancels outstanding scopes and waits for their cleanup before closing
lifespan resources. Partial HTTP/SSE responses are cancelled; ASGI has no general
transport-close message, so the server terminates the unfinished response. This
can produce an expected application-cancellation log on the server.

On server shutdown, publication stops, all generations drain, and shared lifespan
shuts down last. A server may apply its own connection shutdown policy before it
sends the wrapper `lifespan.shutdown`.

## Two simultaneous resource lifetimes

The optional `lifespan_shared` is a separate ASGI3 callable that handles lifespan
messages. It starts once before the initial application and shuts down after all
generations. Its callable stays fixed across reloads. Use it for resources that
must not exist twice, such as a shared pool, process-wide watcher, or sampler.

Each generation runs its own application's ordinary lifespan. Put generation
caches, clients, and background work there. Existing application lifespans are
**not automatically split**: overlapping generations must be an explicit choice
after auditing their startup side effects. Moving an existing whole lifespan to
the shared callable and selecting `lifespan="off"` is also supported.

The shared lifespan receives `scope["state"]`. Each candidate gets a shallow copy
of this mapping; its lifespan can add generation-local entries. Each request
receives another shallow copy of its own generation's state. Mutable resource
objects remain shared by reference. Rebinding a top-level shared key affects
future candidates, not already-created generation dictionaries. Request-local
key changes do not modify lifespan state. Lifespan `ContextVar` changes are not
automatically inherited by request tasks.

Hold cleanup targets in lifespan-local variables. For example, a framework
lifespan context can yield `{"client": client}` and close that same local `client`
in `finally`; looking up a module-global `client` again at shutdown can accidentally
close a newer generation's object. Startup code must clean up partially acquired
resources when it fails or is cancelled.

## Isolation boundary

A generation pins a callable and its resource lifetime, **not a Python module
snapshot**. The current HMR loader re-executes modules in the same globals mapping:

| Access from an existing scope | After module reload |
| --- | --- |
| Running coroutine's code object and local values | Retained |
| Immutable value captured by a factory closure or default argument | Retained |
| Captured mutable object | Same object; other code can still mutate it |
| Module global, including globals used by a captured helper function | May immediately see new values |
| Reactive module attribute lookup or runtime import | May resolve the updated module |
| Third-party module, monkey patch, registry, or `sys.modules` | Shared process-wide |
| Existing instance after its class is redefined | Still belongs to the old class |

Module-level installers run again and must be idempotent. Module `on_dispose`
hooks run when the module is reloaded, **before generation drain**. Do not use
them to close resources still needed by old scopes; use generation lifespan.

Startup rollback prevents publishing the candidate. It cannot undo module
assignments, patches, disposal hooks, or external writes that already happened.
A failed module execution can therefore affect the old app's globals even though
its callable is still selected. Full dependency/runtime isolation requires a new
process. A crash still affects every generation in the current process.

Timeouts require a responsive event loop and cooperative application cancellation.
Blocking Python code delays all generations. An application that suppresses
cancellation indefinitely cannot be safely killed or have its resources reclaimed
by this wrapper; the process must be restarted. This prototype is not a substitute
for process supervision or deployment isolation.

## Verification

Run `python -m pytest tests/py/test_asgi.py` from the repository root with the local
`packages/hmr` installed. Protocol tests exercise startup rejection and timeout,
state ownership, cancellation, scope cleanup, independent drains, and publication
races. The companion `promplate/hmr` Uvicorn adapter includes real-process tests
using WebSocket, SSE, HTTP keep-alive, and source-file edits.

Protocol references: [ASGI lifespan](https://asgi.readthedocs.io/en/latest/specs/lifespan.html)
and [HTTP / WebSocket scopes](https://asgi.readthedocs.io/en/latest/specs/www.html).
