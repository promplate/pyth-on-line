# Linked reactive context benchmark

Measured on CPython 3.14.6 on an Intel Xeon 2.80 GHz Linux host.
Each case uses three warm-up rounds and nine measured rounds of about 100 ms each. Variant order is deterministically shuffled per round and GC is disabled only while timing.

Run:

```bash
python benchmarks/benchmark_reactivity_context.py
```

Representative median overhead versus the existing mutable-list context:

- current owner lookup at depth 8: **+6%**
- untracked `Signal.get()`: **+17%**
- cached `Derived` read: **+5%**
- tracked `Signal.get()` through an `Effect`: **+21%**
- `Signal.set()` with an observing `Effect`: **+19%**
- 8-node derived-chain update: **+13%**
- 8 nested effect triggers: **+27%**

The isolated push/pop microbenchmark is intentionally adversarial: linked frames are **4.5–6.0×** slower than list append/pop because each entry allocates a frame and updates a `ContextVar`. Real reactive workloads amortize that cost across dependency tracking and recomputation.

These numbers are machine- and runtime-sensitive; rerun the script on the target Python/runtime when evaluating regressions.
