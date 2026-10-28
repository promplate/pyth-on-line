<script lang="ts">
  import { getOperatorClass, parseDep } from "./pep508";

  const { dep }: { dep: string } = $props();

  interface VersionPart {
    text: string;
    class: string;
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

  const parsed = $derived(parseDep(dep));
  const versionParts = $derived(parseVersionspec(parsed.versionspec));
</script>

<a href="/pypi/{parsed.name}" class="block truncate rounded-md px-2 py-1.5 text-xs text-neutral-4 ring-0.6 ring-white/5 hover:(bg-white/5 text-white)">
  <span class="font-jb">
    <span>{parsed.name}</span>{#if parsed.extras}<span class="op-40">{parsed.extras}</span>{/if}{#if versionParts.length > 0}<span class="versionspec">
      <!-- Conditions and comma tokens can repeat, so their text is not a unique key. -->
      {#each versionParts as part (part)}
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
