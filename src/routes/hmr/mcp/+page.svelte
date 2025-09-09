<script lang="ts">
  import mcpDocs from "./MCP.md?raw";
  import cursor from "@lobehub/icons-static-svg/icons/cursor.svg?raw";
  import { page } from "$app/stores";
  import CodeBlock from "$lib/components/CodeBlock.svelte";
  import UseCopy from "$lib/components/console/UseCopy.svelte";
  import Router from "$lib/components/markdown/Router.svelte";
  import WithMarkdown from "$lib/components/reusable/WithMarkdown.svelte";
  import { updateMetadata } from "$lib/seo";
  import { Separator } from "bits-ui";

  const url = `${$page.url.origin}/hmr/mcp`;

  const placeholders = {
    "{HOST}": $page.url.origin,
    "{cursor-http}": btoa(JSON.stringify({ url })),
    "{cursor-stdio}": btoa(JSON.stringify({ command: "npx", args: ["mcp-remote", url] })),
    "{vscode-http}": encodeURIComponent(JSON.stringify({ name: "hmr-docs", type: "http", url })),
    "{vscode-stdio}": encodeURIComponent(JSON.stringify({ name: "hmr-docs", type: "stdio", command: "npx", args: ["mcp-remote", url] })),
  };

  const text = Object.entries(placeholders).reduce((acc, [key, value]) => acc.replaceAll(key, value), mcpDocs);

  const httpConfigStr = JSON.stringify({ type: "http", url }, null, 2);
  const stdioConfigStr = JSON.stringify({ type: "stdio", command: "npx", args: ["mcp-remote", url] }, null, 2);

  updateMetadata({ ogTitle: "The MCP Server for HMR", ogDescription: "Use the MCP server to provide HMR knowledge to various clients like Cursor, Claude Code, and GitHub Copilot." });
</script>

<div class="m-4 w-[calc(100%-2rem)] row self-center 2xl:(m-14) lg:(m-10 max-w-4xl) md:(m-8 max-w-3xl w-[calc(100%-4rem)]) sm:(m-6 w-[calc(100%-3rem)]) xl:(m-12 max-w-5xl)">

  <div class="mr-0 bg-#121212 pl-100 pr-0 pt-100 -ml-100 -mt-100 <lg:hidden -translate-x-[calc(0.3rem+2.5vw)] 2xl:(pb-14 -mb-14) lg:(pb-10 -mb-10) xl:(pb-12 -mb-12)">
    <div class="sticky w-21rem col overflow-y-scroll px-5 text-sm 2xl:(top-14 h-[calc(100dvh-7rem)]) lg:(top-10 h-[calc(100dvh-5rem)]) xl:(top-12 h-[calc(100dvh-6rem)]) -ml-5">
      <div class="mb-4 max-w-xs shrink-0 text-xs">
        <CodeBlock lang="json" code={httpConfigStr} />
      </div>
      <div class="col gap-0.7 text-neutral-4 [&>:where(button,a)]:(w-full row items-center gap-2 rounded-lg px-2 py-1.5 filter-grayscale -ml-2) [&>:where(button,a):hover]:(bg-white/7 text-white filter-none) [&>:where(button,a):focus-visible]:(outline-none ring-1.2 ring-neutral-2 ring-inset) ![&>:where(button,a):active]:(bg-neutral-2 text-neutral-8 shadow-lg shadow-neutral-2/20)">
        <UseCopy text={httpConfigStr} let:handleClick>
          <button on:click={handleClick}>
            <div class="i-si-copy-alt-fill size-4" />
            Copy to clipboard
          </button>
        </UseCopy>
        <a target="_blank" href="https://cursor.com/en/install-mcp?name=hmr-docs&config={btoa(JSON.stringify({ url }))}">
          <div class="size-4 translate-0.2 scale-110">{@html cursor.replace(/#\d{3}/g, "currentColor").replaceAll("lobe-icons-cursorundefined-fill", "fill1")}</div>
          Install in Cursor
        </a>
        <UseCopy text="claude mcp add --transport http hmr-docs {url}" let:handleClick>
          <button on:click={handleClick}>
            <div class="i-logos-claude-icon size-4" />
            Add to Claude Code
          </button>
        </UseCopy>
        <a href="vscode:mcp/install?{encodeURIComponent(JSON.stringify({ name: "hmr-docs", type: "http", url }))}">
          <div class="i-vscode-icons-file-type-vscode size-4" />
          Install in VS Code
        </a>
        <a href="vscode-insiders:mcp/install?{encodeURIComponent(JSON.stringify({ name: "hmr-docs", type: "http", url }))}">
          <div class="i-vscode-icons-file-type-vscode-insiders size-4" />
          Install in VS Code Insiders
        </a>
      </div>

      <Separator.Root class="h-3vh max-h-8 min-h-5" />
      <div class="mb-5 text-neutral-6">Or use with <a class="text-neutral-4 hover:text-neutral-2" href="https://www.npmjs.com/package/mcp-remote" title="Learn more on NPM"><code class="mr-0.2 font-mono underline underline-(0.5 neutral-6 offset-2 dashed)">mcp-remote</code></a>:</div>

      <div class="mb-4 max-w-xs shrink-0 text-xs">
        <CodeBlock lang="json" code={stdioConfigStr} />
      </div>
      <div class="col gap-0.7 text-neutral-4 [&>:where(button,a)]:(w-full row items-center gap-2 rounded-lg px-2 py-1.5 filter-grayscale -ml-2) [&>:where(button,a):hover]:(bg-white/7 text-white filter-none) [&>:where(button,a):focus-visible]:(outline-none ring-1.2 ring-neutral-2 ring-inset) ![&>:where(button,a):active]:(bg-neutral-2 text-neutral-8 shadow-lg shadow-neutral-2/20)">
        <UseCopy text={stdioConfigStr} let:handleClick>
          <button on:click={handleClick}>
            <div class="i-si-copy-alt-fill size-4" />
            Copy to clipboard
          </button>
        </UseCopy>
        <a target="_blank" href="https://cursor.com/en/install-mcp?name=hmr-docs&config={btoa(JSON.stringify({ command: "npx", args: ["mcp-remote", url] }))}">
          <div class="size-4 translate-0.2 scale-110">{@html cursor.replace(/#\d{3}/g, "currentColor").replaceAll("lobe-icons-cursorundefined-fill", "fill2")}</div>
          Install in Cursor (stdio)
        </a>
        <UseCopy text="claude mcp add --transport stdio hmr-docs npx mcp-remote {url}" let:handleClick>
          <button on:click={handleClick}>
            <div class="i-logos-claude-icon size-4" />
            Add to Claude Code (stdio)
          </button>
        </UseCopy>
        <a href="vscode:mcp/install?{encodeURIComponent(JSON.stringify({ name: "hmr-docs", type: "stdio", command: "npx", args: ["mcp-remote", url] }))}">
          <div class="i-vscode-icons-file-type-vscode size-4" />
          Install in VS Code (stdio)
        </a>
        <a href="vscode-insiders:mcp/install?{encodeURIComponent(JSON.stringify({ name: "hmr-docs", type: "stdio", command: "npx", args: ["mcp-remote", url] }))}">
          <div class="i-vscode-icons-file-type-vscode-insiders size-4" />
          Install in VS Code Insiders (stdio)
        </a>
      </div>

      <div class="invisible grow" />

      <a class="mt-5 row items-center gap-1.5 text-sm text-neutral-4 hover:text-white" href="/">
        <div class="i-material-symbols-arrow-insert-rounded" />
        Return home
      </a>
    </div>
  </div>

  <main class="mt-1 max-w-full">
    <WithMarkdown let:parse>
      <Router node={parse(text)} />
    </WithMarkdown>
  </main>

</div>
