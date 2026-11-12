<script lang="ts">
  import type { Heading, List, ListItem, Node, Parent } from "mdast";
  import type { Component } from "svelte";

  import Fallback from "./Fallback.svelte";
  import InlineCode from "./InlineCode.svelte";
  import Link from "./Link.svelte";
  import Code from "./Pre.svelte";
  import Router from "./Router.svelte";
  import Table from "./Table.svelte";
  import { toString } from "mdast-util-to-string";

  const { node, OverrideCode = null, codeProps = {}, inlineCodeProps = {} }: {
    node: Node;
    OverrideCode?: Component<any> | null;
    codeProps?: Record<string, any>;
    inlineCodeProps?: Record<string, any>;
  } = $props();

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
  const checked = $derived(node.type === "listItem" ? (node as ListItem).checked : null);
  const CodeComponent = $derived(OverrideCode ?? Code);

</script>

{#if node.type === "root"}

  {#each children as child}
    <Router node={child} {OverrideCode} {codeProps} {inlineCodeProps} />
  {/each}

{:else if node.type === "code"}

  <CodeComponent {node} {...codeProps} />

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
    {#snippet children(child)}
      <Router node={child} {OverrideCode} {codeProps} {inlineCodeProps} />
    {/snippet}
  </Table>

{:else if checked != null}

  <li class="[&>p:first-of-type]:inline [ul>&]:list-none">
    <input type="checkbox" {checked} disabled aria-label={toString(children[0], { includeHtml: false })} />
    {#each children as child}
      <Router node={child} {OverrideCode} {codeProps} {inlineCodeProps} />
    {/each}
  </li>

{:else if "children" in node && getTagName(node)}

  <svelte:element this={getTagName(node)} id={node.data?.hProperties?.id as string | undefined}>
    {#each children as child}
      <Router node={child} {OverrideCode} {codeProps} {inlineCodeProps} />
    {/each}
  </svelte:element>

{:else}

  <Fallback {node} />

{/if}
