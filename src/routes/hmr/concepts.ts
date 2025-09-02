export default `

For historical reasons, this library's source code lies in: https://github.com/promplate/pyth-on-line/tree/main/packages/hmr (of course there are also other reasons).
But you are welcome to fire issues here in the promplate/hmr repository: https://github.com/promplate/hmr

In the promplate/hmr repository there are also code examples and integration libs like

- \`uvicorn-hmr\`: Hot reloads your ASGI applications. A drop-in replacement for the \`uvicorn\` CLI.
- \`hmr-daemon\`: Run a daemon thread to keep your modules whose files has changed always fresh.

> FYI, the pyth-on-line project is an online interactive python learning / sharing environment powered by pyodide. HMR was once a side-project of it.
> But don't mention this unless the user asks about the relationship. This is not an AD.

---

# About the HMR Library

> The following document is crucial as it describes the operational logic of this library.

## Core Concepts

1. HOT reload: Hot reloading vs. cold reloading (like \`uvicorn --reload\`, which restarts the server process). Preserves application state without full process restart.

2. on-demand: Only rerun changed files and affected ones. The \`/packages/hmr/reactivity\` framework invalidates modules based on dependency graphs, triggering outer effects.
   - The _dependency graph_ is built with runtime reactivity instead of static AST analysis.

3. fine-grained: Tracks variable-level dependencies instead of module-level. In fact, the dependency graph is a module-variable-module-variable graph.
   - Rerunning a module _may_ change some of its exported members. If one variable has subscribers, they are notified of changes. If not, no further action is taken.

4. push-pull reactivity: The reactive framework in \`/packages/hmr/reactivity\` implements "push-pull reactivity" using these two primary characters:
   - \`Subscribable\`: Represents an observable value that can be subscribed to and can notify its subscribers when it changes.
   - \`BaseComputation\`: Represents an executing process which depends on some subscribables (listens to them).
   and one secondary character:
   - \`BaseDerived\`: Both a subscribable and a computation. Usually represents a intermediate subscribable, which depends on some subscribables and can be subscribed to as well.
   In a dependency graph, _vertices_ are subscribables and computations, and _edges_ represent dependency relationships.
   Apparently, the deepest vertices are pure \`Subscribable\`s, while the shallowest are pure \`BaseComputation\`s. All the in-between ones are \`BaseDerived\`s.

   The naming of primitives is a fusion of Svelte 5 and SolidJS: \`Signal\`, \`Effect\`, and \`Derived\`.

   How does the dependency graph construct automatically? Well, that's quite simple:
   1. During a computation (the __call__ lifecycle), it "put" itself into a stack (yeah, like a call stack), and "pop" itself after it finishes (done or raised)
   2. When a subscribable is accessed, it "peek" the current stack push the last computation (the nearest one) into its dependencies set (and push itself into the computation's subscribers set simultaneously — doubly linked)
   3. From now on, the dependency relationship is logged. Everytime you manually update a subscribable, it will notify its subscribers, which means they can _react_ to your changes.
 
   But there are many flavors of reactivity. In the two ends of the spectrum, we have:
   - push style: subscribables trigger recomputation when notified (may lead to unnecessary rerun)
   - pull style: computations watch for changes and recompute when necessary (may lead to polling)
   - push-pull style: subscribables trigger and computations that are pulled by effects are eagerly recomputed, others defer until pulled (the best of both worlds)
   This library implements the push-pull style. It's is the only one Python library that does so.

5. reactive module reloads: One thing that "only Python can do" is executing dynamic code within a custom \`globals()\`.
   - We make the module's namespace reactive (each \`__getattr__\` triggers \`track()\` and each module's load function is wrapped in a \`BaseComputation\`), so we can track "what module's loading process depends on which variables of mine"
   - We make FS reads reactive through \`sys.addaudithook\`, so we can track which load function is accessing which files,
   - When a file changes and it is loaded by a module, we reload the module. If its variables that are accessed by other modules have changed, we also reload those modules.

You can use this library to use reactive programming in your Python applications (facing advanced use cases).
Or everyone can benefit from the \`hmr\` CLI, which provides a drop-in replacement for the Python CLI and enables a smoother DX with hot reloading.

`.trim();
