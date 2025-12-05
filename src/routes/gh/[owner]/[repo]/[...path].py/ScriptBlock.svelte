<script lang="ts">
  import type { Item } from "$py/notebook/notebook";

  import { highlight } from "$lib/highlight";

  export let code: string;
  export let items: Item[] = [];

  code = code.replaceAll("\r", "");

  interface ParsedDep {
    name: string;
    extras: string;
    versionspec: string;
    marker: string;
  }

  interface DepLine {
    text: string;
    prefix: string; // e.g. "#   "
    quote: string; // " or '
    dep: ParsedDep;
    suffix: string; // e.g. ","
  }

  function parseDep(depStr: string): ParsedDep {
    const [specPart, ...markerParts] = depStr.split(";");
    const marker = markerParts.length > 0 ? markerParts.join(";").trim() : "";
    const specTrimmed = specPart.trim();
    const nameMatch = specTrimmed.match(/^([a-z\d][-\w.]*[a-z\d]|[a-z\d])/i);
    if (!nameMatch)
      return { name: "", extras: "", versionspec: "", marker };
    const name = nameMatch[1];
    const afterName = specTrimmed.slice(name.length).trim();
    let extras = "";
    let afterExtras = afterName;
    if (afterName.startsWith("[")) {
      const extrasMatch = afterName.match(/^\[([^\]]*)\]/);
      if (extrasMatch) {
        extras = extrasMatch[0];
        afterExtras = afterName.slice(extrasMatch[0].length).trim();
      }
    }
    return { name, extras, versionspec: afterExtras, marker };
  }

  function getOperatorClass(spec: string): string {
    if (spec.includes("~="))
      return "compatible-release";
    if (spec.includes("==="))
      return "arbitrary-equality";
    if (spec.includes("=="))
      return "version-matching";
    if (spec.includes("!="))
      return "version-exclusion";
    if (spec.includes(">=") || spec.includes("<="))
      return "inclusive-ordered";
    if (spec.includes(">") || spec.includes("<"))
      return "exclusive-ordered";
    return "version-other";
  }

  function parseVersionspec(spec: string) {
    if (!spec)
      return [];
    return spec.split(",").map(s => s.trim()).filter(Boolean).map(segment => ({
      text: segment,
      class: getOperatorClass(segment),
    }));
  }

  // Parse PEP 723 header
  let headerLines: ({ text: string } | { depLine: DepLine })[] = [];
  let body = code;
  let hasHeader = false;
  let headerHtml = "";

  const headerStartRegex = /^(?:\s*#\s*)?\/\/\/\s*script\s*$/m;
  const headerEndRegex = /^(?:\s*#\s*)?\/\/\/\s*$/m;

  const startMatch = code.match(headerStartRegex);
  if (startMatch && startMatch.index !== undefined) {
    const startIndex = startMatch.index;
    const rest = code.slice(startIndex + startMatch[0].length);
    const endMatch = rest.match(headerEndRegex);

    if (endMatch && endMatch.index !== undefined) {
      const endIndex = startIndex + startMatch[0].length + endMatch.index + endMatch[0].length;
      const headerText = code.slice(startIndex, endIndex);
      body = code.slice(endIndex).replace(/^\n/, "");
      hasHeader = true;

      const lines = headerText.split("\n");
      let inDeps = false;

      headerLines = lines.map((line) => {
        const trimmed = line.trim();

        if (trimmed.includes("dependencies = [")) {
          inDeps = true;
          return { text: line };
        }

        if (inDeps && /^#\s*\]/.test(trimmed)) {
          inDeps = false;
          return { text: line };
        }

        if (inDeps) {
          // Match: prefix + quote + content + quote + suffix
          // e.g. '#   "anyio>=4.5",' or '#   "uvicorn>=0.31.1; sys_platform != 'emscripten'",'
          const match = line.match(/^(#\s*)(["'])(.*)\2(,?)$/);
          if (match) {
            const [, prefix, quote, content, suffix] = match;
            return {
              depLine: {
                text: line,
                prefix,
                quote,
                dep: parseDep(content),
                suffix,
              },
            };
          }
        }

        return { text: line };
      });
    }
  }

  headerHtml = renderHeaderHtml();

  function escapeHtml(value: string): string {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderHeaderHtml(): string {
    if (!hasHeader)
      return "";

    const rendered = headerLines.map((item) => {
      if ("depLine" in item) {
        const { prefix, quote, dep, suffix } = item.depLine;
        const versionParts = parseVersionspec(dep.versionspec);
        const versions = versionParts.map((part, i) => {
          const comma = i > 0 ? "<span class=\"dim\">,</span>" : "";
          return `${comma}<span class="${part.class}">${escapeHtml(part.text)}</span>`;
        }).join("");
        const extras = dep.extras ? `<span class="dim">${escapeHtml(dep.extras)}</span>` : "";
        const marker = dep.marker ? `<span class="dim">; ${escapeHtml(dep.marker)}</span>` : "";
        const link = `<a href="/pypi/${encodeURIComponent(dep.name)}" class="text-#cdcabe hover:underline">${escapeHtml(dep.name)}</a>`;

        return `<span class="line dim leading-relaxed">${escapeHtml(prefix)}${escapeHtml(quote)}${link}${extras}${versions}${marker}${escapeHtml(quote)}${escapeHtml(suffix)}</span>`;
      }

      return `<span class="line dim whitespace-pre leading-relaxed">${escapeHtml(item.text)}</span>`;
    }).join("\n");

    return `${rendered}\n`;
  }

  function mergeHeader(highlighted: string) {
    if (!hasHeader)
      return highlighted;

    const match = highlighted.match(/^<pre([^>]*)><code([^>]*)>([\s\S]*?)<\/code><\/pre>$/);
    if (!match)
      return highlighted;

    const [, preAttrs, codeAttrs, inner] = match;
    return `<pre${preAttrs}><code${codeAttrs}>${headerHtml}${inner}</code></pre>`;
  }
</script>

<section class="not-prose relative overflow-y-scroll rounded-md bg-#121212 font-jb [&>pre]:!line-height-relaxed">
  {#key body}
    {#await highlight("python", body)}
      <pre><code class="!text-#cdcabe">{@html headerHtml}{body}</code></pre>
    {:then highlighted}
      {@html mergeHeader(highlighted)}
    {/await}
  {/key}
  {#if items.length}
    <div class="m-2 flex flex-col ws-pre-wrap px-1em text-0.8em line-height-relaxed">
      {#each items as { type, text }}
        {#if type === "out"}
          <div class="text-yellow-2">{text}</div>
        {/if}
        {#if type === "err"}
          <div class="text-red-4">{text}</div>
        {/if}
        {#if type === "repr"}
          <div class="text-cyan-2">{text}</div>
        {/if}
      {/each}
    </div>
  {/if}
</section>

<style>
  section :global(pre) {
    --uno: font-mono overflow-x-scroll;
  }

  section :global(pre *) {
    --uno: font-mono selection:bg-white/10;
  }

  /* Version specifier colors - same as Dependency.svelte */
  :global(.compatible-release) { --uno: text-lime-4/70; }
  :global(.version-matching) { --uno: text-cyan-4/70; }
  :global(.version-exclusion) { --uno: text-yellow-4/70; }
  :global(.inclusive-ordered) { --uno: text-teal-4/70; }
  :global(.exclusive-ordered) { --uno: text-indigo-4/70; }
  :global(.arbitrary-equality) { --uno: text-violet-4/70; }
  :global(.version-other) { --uno: text-neutral-4; }

  :global(.dim) {
    --uno: text-#666666
  }
</style>
