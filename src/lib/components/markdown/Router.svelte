<script lang="ts">
  import type { Heading, List, Node, Parent } from "mdast";
  import type { ComponentType } from "svelte";

  import Fallback from "./Fallback.svelte";
  import InlineCode from "./InlineCode.svelte";
  import Link from "./Link.svelte";
  import Code from "./Pre.svelte";
  import Router from "./Router.svelte";
  import Table from "./Table.svelte";

  interface Props {
    node: Node;
    OverrideCode?: ComponentType | null;
    codeProps?: Record<string, any>;
    inlineCodeProps?: Record<string, any>;
  }

  const {
    node,
    OverrideCode = null,
    codeProps = {},
    inlineCodeProps = {},
  }: Props = $props();

  function getTagName(node: Node) {
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

      case "blockquote":
        return "blockquote";

      default:
        console.error(node);
        return null;
    }
  }

  const children = $derived((node as Parent).children);

</script>

{#if node.type === "root"}

  {#each children as child}
    <Router node={child} {OverrideCode} {codeProps} {inlineCodeProps} />
  {/each}

{:else if node.type === "code"}

  {@const SvelteComponent = OverrideCode ?? Code}
  <SvelteComponent {node} {...codeProps} />

{:else if node.type === "inlineCode"}

  <InlineCode {node} {...inlineCodeProps} />

{:else if node.type === "link"}

  <Link {node}>
    {#each children as child}
      <Router node={child} {OverrideCode} {codeProps} {inlineCodeProps} />
    {/each}
  </Link>

{:else if node.type === "table"}

  <Table {node}>
    {#snippet children({ child })}
      <Router node={child} {OverrideCode} {codeProps} {inlineCodeProps} />
    {/snippet}
  </Table>

{:else if "children" in node && getTagName(node)}

  <svelte:element this={getTagName(node)}>
    {#each children as child}
      <Router node={child} {OverrideCode} {codeProps} {inlineCodeProps} />
    {/each}
  </svelte:element>

{:else}

  <Fallback {node} />

{/if}
