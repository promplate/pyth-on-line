<script lang="ts">
  export let dep: string;

  interface ParsedDep {
    name: string;
    extras: string;
    versionspec: string;
    marker: string;
  }

  interface VersionPart {
    text: string;
    class: string;
  }

  function parseDep(depStr: string): ParsedDep {
    // PEP 508: name [extras] versionspec ; marker
    // Split by semicolon to separate marker
    const [specPart, ...markerParts] = depStr.split(";");
    const marker = markerParts.length > 0 ? markerParts.join(";").trim() : "";

    // Parse the spec part: name [extras] versionspec
    const specTrimmed = specPart.trim();

    // Match: name optionally followed by [extras] and/or version spec
    const nameMatch = specTrimmed.match(/^([a-z\d][-\w.]*[a-z\d]|[a-z\d])/i);
    if (!nameMatch) {
      return { name: "", extras: "", versionspec: "", marker: "" };
    }

    const name = nameMatch[1];
    const afterName = specTrimmed.slice(name.length).trim();

    // Check for [extras]
    let extras = "";
    let afterExtras = afterName;
    if (afterName.startsWith("[")) {
      const extrasMatch = afterName.match(/^\[([^\]]*)\]/);
      if (extrasMatch) {
        extras = extrasMatch[0]; // Include the brackets
        afterExtras = afterName.slice(extrasMatch[0].length).trim();
      }
    }

    const versionspec = afterExtras;

    return { name, extras, versionspec, marker };
  }

  function getOperatorClass(spec: string): string {
    // Categorize by operator type
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

    const parts: VersionPart[] = [];
    const segments = spec
      .split(",")
      .map(s => s.trim())
      .filter(s => s.length > 0);

    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i];
      parts.push({
        text: segment,
        class: getOperatorClass(segment),
      });
      // Add comma separator (except after last segment)
      if (i < segments.length - 1) {
        parts.push({
          text: ",",
          class: "separator",
        });
      }
    }

    return parts;
  }

  $: parsed = parseDep(dep);
  $: versionParts = parseVersionspec(parsed.versionspec);
</script>

<a href="/pypi/{parsed.name}" class="block truncate rounded-md px-2 py-1.5 text-xs text-neutral-4 ring-0.6 ring-white/5 hover:(bg-white/5 text-white)">
  <span class="font-jb">
    <span>{parsed.name}</span>{#if parsed.extras}<span class="op-40">{parsed.extras}</span>{/if}{#if versionParts.length > 0}<span class="versionspec">
      {#each versionParts as part (part.text + part.class)}
        {#if part.class === "separator"}
          <span class="op-40">{part.text}</span>
        {:else}
          <span class={part.class}>{part.text}</span>
        {/if}
      {/each}
    </span>
    {/if}
    {#if parsed.marker}
      <span class="op-40"> ; {parsed.marker}</span>
    {/if}
  </span>
</a>

<style>
  .version-other {
    --uno: text-neutral-4;
  }

  /* ~= */
  .compatible-release {
    --uno: text-lime-4/60;
  }
  a:hover .compatible-release {
    --uno: text-lime-4;
  }

  /* == */
  .version-matching {
    --uno: text-cyan-4/60;
  }
  a:hover .version-matching {
    --uno: text-cyan-4;
  }

  /* != */
  .version-exclusion {
    --uno: text-yellow-4/60;
  }
  a:hover .version-exclusion {
    --uno: text-yellow-4;
  }

  /* >= <= */
  .inclusive-ordered {
    --uno: text-teal-4/60;
  }
  a:hover .inclusive-ordered {
    --uno: text-teal-4;
  }

  /* > < */
  .exclusive-ordered {
    --uno: text-indigo-4/60;
  }
  a:hover .exclusive-ordered {
    --uno: text-indigo-4;
  }

  /* === */
  .arbitrary-equality {
    --uno: text-violet-4/60;
  }
  a:hover .arbitrary-equality {
    --uno: text-violet-4;
  }
</style>
