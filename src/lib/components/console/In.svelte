<script lang="ts">
  import ConsolePrompt from "../ConsolePrompt.svelte";
  import InlineCode from "../InlineCode.svelte";
  import ButtonGroup from "./ButtonGroup.svelte";
  import Copy from "./Copy.svelte";

  export let text = "";
</script>

{#if text !== ""}
  <div class="group relative flex flex-row [&_.line]:(min-h-4 lg:min-h-6 sm:min-h-5)">
    <div class="min-h-1 flex flex-shrink-0 flex-col gap-0.7 lg:min-h-1.4 sm:min-h-1.2">
      <ConsolePrompt />
      {#each Array.from({ length: text.match(/\n/g)?.length ?? 0 }) as _}
        <ConsolePrompt prompt="..." />
      {/each}
    </div>
    <InlineCode {text}></InlineCode>
    <ButtonGroup>
      <Copy {text} />
      <button on:click class="i-mingcute-play-fill" />
    </ButtonGroup>
  </div>
{:else}
  <section class="animate-(fade-out duration-300 both)">
    <ConsolePrompt />
  </section>
{/if}
