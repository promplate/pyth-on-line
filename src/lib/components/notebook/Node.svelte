<script lang="ts">
  import type { NotebookAPI } from "$py/notebook/notebook";
  import type { Heading, List, Node, Parent } from "mdast";

  import Fallback from "../markdown/Fallback.svelte";
  import InlineCode from "../markdown/InlineCode.svelte";
  import Link from "../markdown/Link.svelte";
  import Code from "./Code.svelte";

  export let node: Node;
  export let pyNotebook: NotebookAPI;

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

      case "emphasis":
        return "em";

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
    <svelte:self node={child} {pyNotebook} />
  {/each}

{:else if node.type === "code"}

  <Code {node} {pyNotebook} />

{:else if node.type === "inlineCode"}

  <InlineCode {node} inspect={pyNotebook?.inspect} />

{:else if node.type === "link"}

  <Link {node}>
    {#each children as child}
      <svelte:self node={child} {pyNotebook} />
    {/each}
  </Link>

{:else if "children" in node}

  <svelte:element this={getTagName(node)}>
    {#each children as child}
      <svelte:self node={child} {pyNotebook} />
    {/each}
  </svelte:element>

{:else}

  <Fallback {node} />

{/if}
