<script lang="ts">
  import type { DepLineData } from "./types";

  export let data: DepLineData;

  const { prefix, quote, name, extras, versionParts, marker, suffix } = data;

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
    return "";
  }
</script>

{prefix}{quote}<a href="/pypi/{encodeURIComponent(name)}" class="text-#cdcabe hover:underline">{name}</a>{extras}{#each versionParts as part, i}{#if i > 0}<span class="dim">,</span>{/if}<span class={getOperatorClass(part)}>{part}</span>{/each}{marker}{quote}{suffix}

<style>
  .compatible-release {
    --uno: text-lime-4/70;
  }
  .version-matching {
    --uno: text-cyan-4/70;
  }
  .version-exclusion {
    --uno: text-yellow-4/70;
  }
  .inclusive-ordered {
    --uno: text-teal-4/70;
  }
  .exclusive-ordered {
    --uno: text-indigo-4/70;
  }
  .arbitrary-equality {
    --uno: text-violet-4/70;
  }
  :global(.dim) {
    --uno: text-#666666;
  }
</style>
