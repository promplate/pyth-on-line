<script lang="ts">
  import type { Heading, List, Node, Parent } from "mdast";
  import type { ComponentType } from "svelte";

  import Fallback from "./Fallback.svelte";
  import InlineCode from "./InlineCode.svelte";
  import Link from "./Link.svelte";
  import Code from "./Pre.svelte";

  export let node: Node;

  export let OverrideCode: ComponentType | null = null;
  export let codeProps: Record<string, any> = {};
  export let inlineCodeProps: Record<string, any> = {};

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
    <svelte:self node={child} {OverrideCode} {codeProps} {inlineCodeProps} />
  {/each}

{:else if node.type === "code"}

  <svelte:component this={OverrideCode ?? Code} {node} {...codeProps} />

{:else if node.type === "inlineCode"}

  <InlineCode {node} {...inlineCodeProps} />

{:else if node.type === "link"}

  <Link {node}>
    {#each children as child}
      <svelte:self node={child} {OverrideCode} {codeProps} {inlineCodeProps} />
    {/each}
  </Link>

{:else if "children" in node}

  <svelte:element this={getTagName(node)}>
    {#each children as child}
      <svelte:self node={child} {OverrideCode} {codeProps} {inlineCodeProps} />
    {/each}
  </svelte:element>

{:else}

  <Fallback {node} />

{/if}
