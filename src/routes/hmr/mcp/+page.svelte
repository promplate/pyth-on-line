<script lang="ts">
  import mcpDocs from "./MCP.md?raw";
  import { page } from "$app/stores";
  import Router from "$lib/components/markdown/Router.svelte";
  import WithMarkdown from "$lib/components/reusable/WithMarkdown.svelte";

  const url = `${$page.url.origin}/hmr/mcp`;

  const placeholders = {
    "{HOST}": $page.url.origin,
    "{cursor-http}": btoa(JSON.stringify({ url })),
    "{cursor-stdio}": btoa(JSON.stringify({ command: "npx", args: ["mcp-remote", url] })),
    "{vscode-http}": encodeURIComponent(JSON.stringify({ name: "hmr-docs", type: "http", url })),
    "{vscode-stdio}": encodeURIComponent(JSON.stringify({ name: "hmr-docs", type: "stdio", command: "npx", args: ["mcp-remote", url] })),
  };

  const text = Object.entries(placeholders).reduce((acc, [key, value]) => acc.replaceAll(key, value), mcpDocs);
</script>

<div class="m-4 w-[calc(100%-2rem)] self-center 2xl:(m-10 w-4xl) lg:(m-7 w-2xl) md:m-6 sm:(m-5 w-xl) xl:(m-8 w-3xl) [&_article]:(lg:text-3.75 xl:text-base)">
  <WithMarkdown let:parse>
    <Router node={parse(text)} />
  </WithMarkdown>
</div>
