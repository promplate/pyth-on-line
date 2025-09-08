<script lang="ts">
  import NotebookLayout from "../../../routes/(notebook)/+layout.svelte";
  import mcpDocs from "./MCP.md?raw";
  import { page } from "$app/stores";
  import Notebook from "$lib/components/notebook/Notebook.svelte";

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

<NotebookLayout>
  <Notebook {text} />
</NotebookLayout>
