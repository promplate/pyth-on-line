#!/usr/bin/env python3
"""Benchmark reactive owner-stack representations and real reactivity workloads.

The benchmark compares three otherwise-identical context implementations:

* ``mutable-list``: the existing synchronous mutable-list stack baseline.
* ``tuple-contextvar``: an immutable tuple stored in a ``ContextVar``.
* ``linked-contextvar``: an immutable linked frame stored in a ``ContextVar``.

The microbenchmarks isolate owner-stack operations.  The reactivity benchmarks use
hmr's real ``Signal``, ``Effect``, ``Derived``, dependency sets, and batching code;
only the injected Context object varies.

Run from the repository root, for example::

    python benchmarks/benchmark_reactivity_context.py
    python benchmarks/benchmark_reactivity_context.py --quick
    python benchmarks/benchmark_reactivity_context.py --json results.json

Results are medians of interleaved samples.  Each variant is calibrated separately
to approximately the same sample duration, and variant order is deterministically
shuffled on every round to reduce ordering bias.  GC is disabled only while timing
(default) and collected immediately before every sample.
"""

# Benchmark assertions intentionally include descriptive messages.
# ruff: noqa: TRY003

from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import random
import statistics
import sys
import time
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

ROOT = Path(__file__).resolve().parents[1]
HMR_PACKAGE = ROOT / "packages" / "hmr"
if str(HMR_PACKAGE) not in sys.path:
    sys.path.insert(0, str(HMR_PACKAGE))

from reactivity.primitives import Derived, Effect, Signal

VARIANTS = ("mutable-list", "tuple-contextvar", "linked-contextvar")
_SENTINEL = object()
_EMPTY: tuple[()] = ()


@dataclass(slots=True, eq=False)
class Frame:
    """One immutable stack frame, matching the linked implementation shape."""

    value: Any
    parent: Frame | None = None
    depth: int = 1
    active: bool = True

    def __init__(self, value: Any, parent: Frame | None = None) -> None:
        self.value = value
        self.parent = parent
        self.depth = 1 if parent is None else parent.depth + 1
        self.active = True

    def frames(self) -> Iterator[Frame]:
        frame: Frame | None = self
        while frame is not None:
            yield frame
            frame = frame.parent

    def __iter__(self) -> Iterator[Any]:
        values = []
        for frame in self.frames():
            values.append(frame.value)
        return reversed(values)

    def __contains__(self, value: object) -> bool:
        frame: Frame | None = self
        while frame is not None:
            if frame.value is value:
                return True
            frame = frame.parent
        return False


class OwnerContext(Protocol):
    @property
    def current_computation(self) -> Any | None: ...

    def is_computing(self, computation: Any) -> bool: ...

    @contextmanager
    def enter(self, computation: Any) -> Iterator[None]: ...

    @contextmanager
    def untrack(self) -> Iterator[None]: ...


class _ContextBase:
    """Shared behavior required by hmr primitives."""

    @property
    def leaf(self) -> _ContextBase:
        return self

    @property
    def current_computations(self) -> tuple[Any, ...]:
        raise NotImplementedError

    @property
    def current_computation(self) -> Any | None:
        raise NotImplementedError

    def is_computing(self, computation: Any) -> bool:
        raise NotImplementedError

    def push(self, computation: Any) -> Any:
        raise NotImplementedError

    def pop(self, marker: Any) -> None:
        raise NotImplementedError

    @contextmanager
    def untrack(self) -> Iterator[None]:
        raise NotImplementedError

    def schedule_callbacks(self, callbacks: Iterable[Any]) -> None:
        batch = self.current_batch
        if batch is None:
            raise AssertionError("cannot schedule callbacks without a batch")
        batch.callbacks.update(callbacks)

    @property
    def current_batch(self) -> Any | None:
        raise NotImplementedError

    @property
    def batch_depth(self) -> int:
        raise NotImplementedError

    @contextmanager
    def enter_batch(self, batch: Any) -> Iterator[None]:
        raise NotImplementedError

    def _before_enter(self, computation: Any) -> set[Any]:
        old_dependencies = {*computation.dependencies}
        computation.dispose()
        return old_dependencies

    def _after_success(self, computation: Any, old_dependencies: set[Any]) -> None:
        # The benchmark workloads always establish dependencies.  Retaining this
        # assertion catches an invalid workload without timing warning formatting.
        if not computation.dependencies:
            raise AssertionError(f"{computation!r} collected no dependencies; old={old_dependencies!r}")


class MutableListContext(_ContextBase):
    """Mutable list baseline (no ContextVar on the synchronous path)."""

    def __init__(self) -> None:
        self._owners: list[Any] = []
        self._batches: list[Any] = []

    @property
    def current_computations(self) -> tuple[Any, ...]:
        return tuple(self._owners)

    @property
    def current_computation(self) -> Any | None:
        return self._owners[-1] if self._owners else None

    def is_computing(self, computation: Any) -> bool:
        return computation in self._owners

    @property
    def current_batch(self) -> Any | None:
        return self._batches[-1] if self._batches else None

    @property
    def batch_depth(self) -> int:
        return len(self._batches)

    @contextmanager
    def enter_batch(self, batch: Any) -> Iterator[None]:
        self._batches.append(batch)
        try:
            yield
        finally:
            if self._batches.pop() is not batch:
                raise AssertionError("batch-stack mismatch")

    def push(self, computation: Any) -> None:
        self._owners.append(computation)

    def pop(self, marker: None) -> None:  # noqa: ARG002
        if self._owners.pop() is not _SENTINEL:
            raise AssertionError("owner-stack mismatch")

    @contextmanager
    def enter(self, computation: Any) -> Iterator[None]:
        old_dependencies = self._before_enter(computation)
        self._owners.append(computation)
        try:
            yield
        except BaseException:
            if computation.dependencies.issubset(old_dependencies):
                for dependency in old_dependencies:
                    dependency.subscribers.add(computation)
                computation.dependencies.update(old_dependencies)
            raise
        else:
            self._after_success(computation, old_dependencies)
        finally:
            if self._owners.pop() is not computation:
                raise AssertionError("owner-stack mismatch")

    @contextmanager
    def untrack(self) -> Iterator[None]:
        owners = self._owners[:]
        self._owners.clear()
        try:
            yield
        finally:
            self._owners[:] = owners


class TupleContextVarContext(_ContextBase):
    """Immutable owner and batch tuples in ContextVars."""

    def __init__(self) -> None:
        self._owners: ContextVar[tuple[Any, ...]] = ContextVar("tuple owners", default=_EMPTY)
        self._batches: ContextVar[tuple[Any, ...]] = ContextVar("tuple batches", default=_EMPTY)

    @property
    def current_computations(self) -> tuple[Any, ...]:
        return self._owners.get()

    @property
    def current_computation(self) -> Any | None:
        owners = self._owners.get()
        return owners[-1] if owners else None

    def is_computing(self, computation: Any) -> bool:
        return computation in self._owners.get()

    @property
    def current_batch(self) -> Any | None:
        batches = self._batches.get()
        return batches[-1] if batches else None

    @property
    def batch_depth(self) -> int:
        return len(self._batches.get())

    @contextmanager
    def enter_batch(self, batch: Any) -> Iterator[None]:
        batches = (*self._batches.get(), batch)
        token = self._batches.set(batches)
        try:
            yield
        finally:
            if self._batches.get() is not batches:
                raise AssertionError("batch-stack mismatch")
            self._batches.reset(token)

    def push(self, computation: Any) -> Token[tuple[Any, ...]]:
        return self._owners.set((*self._owners.get(), computation))

    def pop(self, marker: Token[tuple[Any, ...]]) -> None:
        if self._owners.get()[-1] is not _SENTINEL:
            raise AssertionError("owner-stack mismatch")
        self._owners.reset(marker)

    @contextmanager
    def enter(self, computation: Any) -> Iterator[None]:
        old_dependencies = self._before_enter(computation)
        owners = (*self._owners.get(), computation)
        token = self._owners.set(owners)
        try:
            yield
        except BaseException:
            if computation.dependencies.issubset(old_dependencies):
                for dependency in old_dependencies:
                    dependency.subscribers.add(computation)
                computation.dependencies.update(old_dependencies)
            raise
        else:
            self._after_success(computation, old_dependencies)
        finally:
            if self._owners.get() is not owners:
                raise AssertionError("owner-stack mismatch")
            self._owners.reset(token)

    @contextmanager
    def untrack(self) -> Iterator[None]:
        token = self._owners.set(_EMPTY)
        try:
            yield
        finally:
            self._owners.reset(token)


class LinkedContextVarContext(_ContextBase):
    """Immutable linked owner and batch frames in ContextVars."""

    def __init__(self) -> None:
        self._owner: ContextVar[Frame | None] = ContextVar("linked owner", default=None)
        self._batch: ContextVar[Frame | None] = ContextVar("linked batch", default=None)

    @property
    def current_computations(self) -> tuple[Any, ...]:
        frame = self._owner.get()
        if frame is None:
            return _EMPTY
        return tuple(item.value for item in frame.frames() if item.active)

    @property
    def current_computation(self) -> Any | None:
        frame = self._owner.get()
        while frame is not None:
            if frame.active:
                return frame.value
            frame = frame.parent
        return None

    def is_computing(self, computation: Any) -> bool:
        frame = self._owner.get()
        while frame is not None:
            if frame.active and frame.value is computation:
                return True
            frame = frame.parent
        return False

    @property
    def current_batch(self) -> Any | None:
        frame = self._batch.get()
        while frame is not None:
            if frame.active:
                return frame.value
            frame = frame.parent
        return None

    @property
    def batch_depth(self) -> int:
        frame = self._batch.get()
        depth = 0
        while frame is not None:
            depth += frame.active
            frame = frame.parent
        return depth

    @contextmanager
    def enter_batch(self, batch: Any) -> Iterator[None]:
        frame = Frame(batch, self._batch.get())
        token = self._batch.set(frame)
        try:
            yield
        finally:
            if self._batch.get() is not frame:
                raise AssertionError("batch-stack mismatch")
            frame.active = False
            self._batch.reset(token)

    def push(self, computation: Any) -> tuple[Frame, Token[Frame | None]]:
        frame = Frame(computation, self._owner.get())
        return frame, self._owner.set(frame)

    def pop(self, marker: tuple[Frame, Token[Frame | None]]) -> None:
        frame, token = marker
        if self._owner.get() is not frame or frame.value is not _SENTINEL:
            raise AssertionError("owner-stack mismatch")
        frame.active = False
        self._owner.reset(token)

    @contextmanager
    def enter(self, computation: Any) -> Iterator[None]:
        old_dependencies = self._before_enter(computation)
        frame = Frame(computation, self._owner.get())
        token = self._owner.set(frame)
        try:
            yield
        except BaseException:
            if computation.dependencies.issubset(old_dependencies):
                for dependency in old_dependencies:
                    dependency.subscribers.add(computation)
                computation.dependencies.update(old_dependencies)
            raise
        else:
            self._after_success(computation, old_dependencies)
        finally:
            if self._owner.get() is not frame:
                raise AssertionError("owner-stack mismatch")
            frame.active = False
            self._owner.reset(token)

    @contextmanager
    def untrack(self) -> Iterator[None]:
        token = self._owner.set(None)
        try:
            yield
        finally:
            self._owner.reset(token)


CONTEXT_TYPES: dict[str, type[_ContextBase]] = {
    "mutable-list": MutableListContext,
    "tuple-contextvar": TupleContextVarContext,
    "linked-contextvar": LinkedContextVarContext,
}


@dataclass(frozen=True)
class Case:
    suite: str
    name: str
    unit: str
    build: Callable[[str], Callable[[int], int]]


@dataclass(frozen=True)
class Result:
    suite: str
    case: str
    variant: str
    unit: str
    iterations: int
    samples_ns_per_op: list[float]
    median_ns_per_op: float
    mad_ns_per_op: float
    min_ns_per_op: float
    max_ns_per_op: float
    relative_to_mutable: float = 0.0


def _prefill(context: Any, depth: int) -> list[Any]:
    markers = []
    for _ in range(depth):
        markers.append(context.push(object()))
    return markers


def build_current(depth: int) -> Callable[[str], Callable[[int], int]]:
    def build(variant: str) -> Callable[[int], int]:
        context = CONTEXT_TYPES[variant]()
        _prefill(context, depth)

        def run(iterations: int) -> int:
            value = None
            for _ in range(iterations):
                current = context.current_computation
                value = current if current is not None else None
            return id(value)

        return run

    return build


def build_push_pop(depth: int) -> Callable[[str], Callable[[int], int]]:
    def build(variant: str) -> Callable[[int], int]:
        context = CONTEXT_TYPES[variant]()
        _prefill(context, depth)

        def run(iterations: int) -> int:
            for _ in range(iterations):
                marker = context.push(_SENTINEL)
                context.pop(marker)
            return iterations

        return run

    return build


def build_untrack(depth: int) -> Callable[[str], Callable[[int], int]]:
    def build(variant: str) -> Callable[[int], int]:
        context = CONTEXT_TYPES[variant]()
        _prefill(context, depth)

        def run(iterations: int) -> int:
            for _ in range(iterations):
                with context.untrack():
                    if context.current_computation is not None:
                        raise AssertionError("untrack did not hide owners")
            return iterations

        return run

    return build


def build_signal_get_untracked(variant: str) -> Callable[[int], int]:
    context = CONTEXT_TYPES[variant]()
    signal = Signal(7, context=context)  # type: ignore[arg-type]

    def run(iterations: int) -> int:
        total = 0
        for _ in range(iterations):
            total += signal.get()
        return total

    return run


def build_signal_get_tracked(variant: str) -> Callable[[int], int]:
    context = CONTEXT_TYPES[variant]()
    signal = Signal(7, context=context)  # type: ignore[arg-type]
    sink = [0]
    effect = Effect(lambda: sink.__setitem__(0, signal.get()), call_immediately=False, context=context)  # type: ignore[arg-type]

    def run(iterations: int) -> int:
        for _ in range(iterations):
            effect.trigger()
        return sink[0]

    return run


def build_effect_update(variant: str) -> Callable[[int], int]:
    context = CONTEXT_TYPES[variant]()
    signal = Signal(0, check_equality=False, context=context)  # type: ignore[arg-type]
    sink = [0]
    effect = Effect(lambda: sink.__setitem__(0, signal.get()), context=context)  # type: ignore[arg-type]

    def run(iterations: int) -> int:
        start = signal.get(track=False)
        for value in range(start + 1, start + iterations + 1):
            signal.set(value)
        if sink[0] != start + iterations:
            raise AssertionError("effect did not observe the final update")
        return sink[0] + len(effect.dependencies)

    return run


def build_derived_cached(variant: str) -> Callable[[int], int]:
    context = CONTEXT_TYPES[variant]()
    signal = Signal(3, context=context)  # type: ignore[arg-type]
    derived = Derived(lambda: signal.get() + 1, context=context)  # type: ignore[arg-type]
    if derived() != 4:
        raise AssertionError("derived initialization failed")

    def run(iterations: int) -> int:
        total = 0
        for _ in range(iterations):
            total += derived()
        return total

    return run


def build_derived_chain_update(depth: int) -> Callable[[str], Callable[[int], int]]:
    def build(variant: str) -> Callable[[int], int]:
        context = CONTEXT_TYPES[variant]()
        source: Any = Signal(0, check_equality=False, context=context)  # type: ignore[arg-type]
        root = source
        for _ in range(depth):
            previous = root
            root = Derived(lambda previous=previous: previous() + 1 if isinstance(previous, Derived) else previous.get() + 1, context=context)  # type: ignore[arg-type]
        sink = [0]
        effect = Effect(lambda: sink.__setitem__(0, root()), context=context)  # type: ignore[arg-type]

        def run(iterations: int) -> int:
            start = source.get(track=False)
            for value in range(start + 1, start + iterations + 1):
                source.set(value)
            expected = start + iterations + depth
            if sink[0] != expected:
                raise AssertionError(f"derived chain returned {sink[0]}, expected {expected}")
            return sink[0] + len(effect.dependencies)

        return run

    return build


def build_nested_effects(depth: int) -> Callable[[str], Callable[[int], int]]:
    def build(variant: str) -> Callable[[int], int]:
        context = CONTEXT_TYPES[variant]()
        signals = [Signal(index, context=context) for index in range(depth)]  # type: ignore[arg-type]
        effects: list[Effect[Any]] = []
        sink = [0]

        for index in range(depth - 1, -1, -1):
            child = effects[-1] if effects else None
            signal = signals[index]

            def body(signal: Signal[int] = signal, child: Effect[Any] | None = child) -> None:
                sink[0] += signal.get()
                if child is not None:
                    child.trigger()

            effects.append(Effect(body, call_immediately=False, context=context))  # type: ignore[arg-type]

        root = effects[-1]

        def run(iterations: int) -> int:
            before = sink[0]
            for _ in range(iterations):
                root.trigger()
            expected_delta = iterations * sum(range(depth))
            if sink[0] - before != expected_delta:
                raise AssertionError("nested effects produced the wrong checksum")
            return sink[0]

        return run

    return build


CASES = (
    Case("micro", "current-empty", "current lookup", build_current(0)),
    Case("micro", "current-depth-8", "current lookup", build_current(8)),
    Case("micro", "push-pop-depth-0", "push/pop pair", build_push_pop(0)),
    Case("micro", "push-pop-depth-8", "push/pop pair", build_push_pop(8)),
    Case("micro", "push-pop-depth-64", "push/pop pair", build_push_pop(64)),
    Case("micro", "untrack-depth-8", "untrack scope", build_untrack(8)),
    Case("reactivity", "signal-get-untracked", "Signal.get", build_signal_get_untracked),
    Case("reactivity", "signal-get-tracked", "Effect.trigger + Signal.get", build_signal_get_tracked),
    Case("reactivity", "effect-update", "Signal.set + Effect", build_effect_update),
    Case("reactivity", "derived-read-cached", "cached Derived read", build_derived_cached),
    Case("reactivity", "derived-chain-update-8", "8-node chain update", build_derived_chain_update(8)),
    Case("reactivity", "nested-effects-8", "8 nested Effect triggers", build_nested_effects(8)),
)


def time_once(fn: Callable[[int], int], iterations: int, disable_gc: bool) -> int:
    gc.collect()
    was_enabled = gc.isenabled()
    if disable_gc and was_enabled:
        gc.disable()
    try:
        start = time.perf_counter_ns()
        checksum = fn(iterations)
        elapsed = time.perf_counter_ns() - start
    finally:
        if disable_gc and was_enabled:
            gc.enable()
    if checksum is None:
        raise AssertionError("benchmark callable must return a checksum")
    return elapsed


def calibrate(fn: Callable[[int], int], target_ns: int, disable_gc: bool) -> int:
    iterations = 1
    while True:
        elapsed = time_once(fn, iterations, disable_gc)
        if elapsed >= target_ns or iterations >= 1 << 30:
            return iterations
        scale = max(2, min(10, target_ns // max(elapsed, 1)))
        iterations *= scale


def run_case(case: Case, *, rounds: int, warmups: int, target_ns: int, disable_gc: bool, seed: int) -> list[Result]:
    functions = {variant: case.build(variant) for variant in VARIANTS}
    iterations = {variant: calibrate(functions[variant], target_ns, disable_gc) for variant in VARIANTS}
    rng = random.Random(f"{seed}:{case.suite}:{case.name}")

    for _ in range(warmups):
        order = list(VARIANTS)
        rng.shuffle(order)
        for variant in order:
            time_once(functions[variant], iterations[variant], disable_gc)

    samples: dict[str, list[float]] = {variant: [] for variant in VARIANTS}
    for _ in range(rounds):
        order = list(VARIANTS)
        rng.shuffle(order)
        for variant in order:
            elapsed = time_once(functions[variant], iterations[variant], disable_gc)
            samples[variant].append(elapsed / iterations[variant])

    results = []
    for variant in VARIANTS:
        values = samples[variant]
        median = statistics.median(values)
        results.append(
            Result(
                suite=case.suite,
                case=case.name,
                variant=variant,
                unit=case.unit,
                iterations=iterations[variant],
                samples_ns_per_op=values,
                median_ns_per_op=median,
                mad_ns_per_op=statistics.median(abs(value - median) for value in values),
                min_ns_per_op=min(values),
                max_ns_per_op=max(values),
            )
        )

    baseline = next(result.median_ns_per_op for result in results if result.variant == "mutable-list")
    return [Result(**{**asdict(result), "relative_to_mutable": result.median_ns_per_op / baseline}) for result in results]


def environment() -> dict[str, Any]:
    cpu_model = "unknown"
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text().splitlines():
            if line.startswith("model name"):
                cpu_model = line.partition(":")[2].strip()
                break
    return {
        "python": sys.version.replace("\n", " "),
        "python_executable": sys.executable,
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "cpu": cpu_model,
        "pid": os.getpid(),
        "clock": "time.perf_counter_ns",
    }


def print_results(results: list[Result]) -> None:
    print("\nMedian time (ns/op); ratio is relative to mutable-list within each row")
    print(f"{'suite / case':<42} {'variant':<20} {'ns/op':>12} {'MAD':>10} {'ratio':>9}")
    print("-" * 98)
    previous_case: tuple[str, str] | None = None
    for result in results:
        key = (result.suite, result.case)
        label = f"{result.suite} / {result.case}" if key != previous_case else ""
        print(f"{label:<42} {result.variant:<20} {result.median_ns_per_op:>12.1f} {result.mad_ns_per_op:>10.1f} {result.relative_to_mutable:>8.2f}x")
        previous_case = key


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rounds", type=int, default=9, help="measured samples per variant (default: 9)")
    parser.add_argument("--warmups", type=int, default=3, help="warmup samples per variant (default: 3)")
    parser.add_argument("--target-ms", type=float, default=100.0, help="approximate duration of each sample (default: 100)")
    parser.add_argument("--seed", type=int, default=20260823, help="deterministic interleaving seed")
    parser.add_argument("--gc", action="store_true", help="leave cyclic GC enabled while timing")
    parser.add_argument("--suite", choices=("all", "micro", "reactivity"), default="all")
    parser.add_argument("--quick", action="store_true", help="use 3 rounds, 1 warmup, and 10 ms samples")
    parser.add_argument("--json", type=Path, help="also write environment, protocol, and raw samples as JSON")
    args = parser.parse_args()
    if args.quick:
        args.rounds = 3
        args.warmups = 1
        args.target_ms = 10.0
    if args.rounds < 1 or args.warmups < 0 or args.target_ms <= 0:
        parser.error("rounds and target-ms must be positive; warmups must be non-negative")
    return args


def main() -> None:
    args = parse_args()
    selected = [case for case in CASES if args.suite == "all" or case.suite == args.suite]
    env = environment()
    print(f"Python: {env['python'].split()[0]} ({env['implementation']})")
    print(f"CPU: {env['cpu']}")
    print(f"Protocol: {args.rounds} rounds, {args.warmups} warmups, ~{args.target_ms:g} ms/sample, GC {'enabled' if args.gc else 'disabled while timing'}")

    results: list[Result] = []
    for index, case in enumerate(selected, 1):
        print(f"[{index:>2}/{len(selected)}] {case.suite} / {case.name}", flush=True)
        results.extend(
            run_case(
                case,
                rounds=args.rounds,
                warmups=args.warmups,
                target_ns=int(args.target_ms * 1_000_000),
                disable_gc=not args.gc,
                seed=args.seed,
            )
        )
    print_results(results)

    if args.json:
        payload = {
            "environment": env,
            "protocol": {
                "rounds": args.rounds,
                "warmups": args.warmups,
                "target_ms": args.target_ms,
                "seed": args.seed,
                "gc_disabled_while_timing": not args.gc,
                "variant_order": list(VARIANTS),
                "note": "Variants are interleaved in a deterministic shuffled order per measured round.",
            },
            "results": [asdict(result) for result in results],
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"\nWrote raw results to {args.json}")


if __name__ == "__main__":
    main()
