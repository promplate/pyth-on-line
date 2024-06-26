<script lang="ts">
  import type { Heading, List, Node, Parent } from "mdast";

  import Code from "./Code.svelte";
  import Fallback from "./Fallback.svelte";
  import InlineCode from "./InlineCode.svelte";
  import Link from "./Link.svelte";

  export let node: Node;

  function getTagName(node: Node): string {
    switch (node.type) {
      case "heading":
        return `h${(node as Heading).depth}`;

      case "list":
        return (node as List).ordered ? "ol" : "ul";

      case "listItem":
        return "li";

      case "strong":
        return "strong";

      case "paragraph":
        return "p";

      default:
        console.error(node);
        return "div";
    }
  }

  $: children = (node as Parent).children;

</script>

{#if node.type === "root"}

  {#each children as child}
    <svelte:self node={child} />
  {/each}

{:else if node.type === "code"}

  <Code {node} />

{:else if node.type === "inlineCode"}

  <InlineCode {node} />

{:else if node.type === "link"}

  <Link {node}>
    {#each children as child}
      <svelte:self node={child} />
    {/each}
  </Link>

{:else if "children" in node}

  <svelte:element this={getTagName(node)}>
    {#each children as child}
      <svelte:self node={child} />
    {/each}
  </svelte:element>

{:else}

  <Fallback {node} />

{/if}
