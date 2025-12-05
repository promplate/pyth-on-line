<script lang="ts">
  import type { HeaderLineData } from "./header/types";

  import Header from "./header/Header.svelte";
  import { highlight } from "$lib/highlight";

  export let code: string;

  code = code.replaceAll("\r", "");

  interface Dep {
    name: string;
    extras: string;
    versionspec: string;
    marker: string;
  }

  function parseVersionspec(spec: string) {
    if (!spec)
      return [];
    return spec.split(",").map(s => s.trim()).filter(Boolean);
  }

  function parseDep(depStr: string): Dep {
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

  let headerLines: HeaderLineData[] = [];
  let body = code;
  let hasHeader = false;

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

      headerLines = lines.map((line): HeaderLineData => {
        const trimmed = line.trim();

        if (trimmed.includes("dependencies = [")) {
          inDeps = true;
          return { kind: "text", text: line };
        }

        if (inDeps && /^#\s*\]/.test(trimmed)) {
          inDeps = false;
          return { kind: "text", text: line };
        }

        if (inDeps) {
          const match = line.match(/^(#\s*)(["'])(.*)\2(,?)$/);
          if (match) {
            const [, prefix, quote, content, suffix] = match;
            const dep = parseDep(content);
            return {
              kind: "dep",
              line: {
                prefix,
                quote,
                name: dep.name,
                extras: dep.extras,
                versionParts: parseVersionspec(dep.versionspec),
                marker: dep.marker ? ` ; ${dep.marker}` : "",
                suffix,
              },
            };
          }
        }
        return { kind: "text", text: line };
      });
    }
  }
</script>

<pre class="not-prose relative overflow-x-scroll overflow-y-scroll rounded-md bg-#121212 leading-relaxed selection:bg-white/10 [&>pre]:!line-height-relaxed"
>{#if hasHeader}<code class="text-#666666"><Header {headerLines} /></code>
{/if}{#await highlight("python", body)}<code class="text-#cdcabe">{body}</code>{:then highlighted}<code>{@html highlighted.replace(/^<pre([^>]*)><code([^>]*)>([\s\S]*?)<\/code><\/pre>$/, "$3")}</code>{/await}</pre>

<style>
  code {
    --uno: font-jb;
  }
</style>
