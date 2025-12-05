<script lang="ts">
  export let text: string;
  export let index: number;

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

  $: cls = getOperatorClass(text);
</script>

{#if index > 0}<span class="dim">,</span>{/if}<span class={cls}>{text}</span>

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
