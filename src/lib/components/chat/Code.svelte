<script lang="ts">
  import type { Node } from "mdast";

  import WithCodeActions from "../reusable/WithCodeActions.svelte";
  import CodeBlock from "$lib/components/CodeBlock.svelte";

  interface Props {
    node: Node;
    runCode: ((source: string) => any) | undefined;
  }

  const { node, runCode }: Props = $props();

  function run(source: string) {
    source = source.trimEnd();

    if (source.split("\n").at(-1)!.startsWith(" ")) // heuristic to detect multiline input
      runCode?.(`${source}\n\n`);
    else
      runCode?.(`${source}\n`);
  }
</script>

<WithCodeActions {node} {run} fadeIn>
  {#snippet children({ code })}
    <CodeBlock lang={code.lang ?? "text"} code={code.value} />
  {/snippet}
</WithCodeActions>
