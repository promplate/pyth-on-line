<script lang="ts">
  import type { Node } from "mdast";

  import WithCodeActions from "../reusable/WithCodeActions.svelte";
  import CodeBlock from "$lib/components/CodeBlock.svelte";

  export let node: Node;
  export let runCode: ((source: string) => any) | undefined;

  function run(source: string) {
    source = source.trimEnd();

    if (source.split("\n").at(-1)!.startsWith(" ")) // heuristic to detect multiline input
      runCode?.(`${source}\n\n`);
    else
      runCode?.(`${source}\n`);
  }
</script>

<WithCodeActions {node} {run} fadeIn let:code>
  <CodeBlock lang={code.lang ?? "text"} code={code.value} />
</WithCodeActions>
