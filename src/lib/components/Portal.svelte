<script lang="ts">
  import { goto, preloadData } from "$app/navigation";
  import { getPy } from "$lib/pyodide";
  import { type SourceRef, refToSource } from "$lib/utils/source";

  export let source: string;
  export let previous: SourceRef[] = [];

  const url = "/playground";

  function preload() {
    preloadData(url);
    getPy();
  }

  let hovered = false;
  let focused = false;

  async function jump() {
    const sources = [...previous.map(refToSource), { source, wait: true }];
    goto(url, { state: { sources } });
  }
</script>

<button on:click={jump} class="absolute right-4 top-4 grid place-items-center rounded p-1 outline-none [&>div]:(p-2 sm:p-2.5) focus:(ring-1.2 ring-white/20 transition-background-color hover:bg-white/10)" on:mouseenter|once={preload} on:focus|once={preload} on:focus={() => (focused = true)} on:blur={() => (focused = false)} on:mouseenter={() => (hovered = true)} on:mouseleave={() => (hovered = false)}>
  <div class={hovered || focused ? "i-ph-rocket-launch-fill" : "i-ph-rocket-launch"}></div>
</button>
