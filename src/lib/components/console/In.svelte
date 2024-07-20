<script lang="ts">
  import ConsolePrompt from "../ConsolePrompt.svelte";
  import InlineCode from "../InlineCode.svelte";
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import ButtonGroup from "./ButtonGroup.svelte";
  import Copy from "./Copy.svelte";

  export let text = "";
</script>

{#if text !== ""}
  <div class="group relative flex flex-row">
    <div class="flex flex-col gap-0.2em">
      <ConsolePrompt />
      {#each Array.from({ length: text.match(/\n/g)?.length ?? 0 }) as _}
        <ConsolePrompt prompt="..." />
      {/each}
    </div>
    <InlineCode {text}></InlineCode>
    <ButtonGroup>
      <Copy {text} />
      <WithTooltip tips="Run" let:builder>
        <button on:click class="i-mingcute-play-fill" {...builder} use:builder.action />
      </WithTooltip>
    </ButtonGroup>
  </div>
{:else}
  <section class="animate-(fade-out duration-300 both)">
    <ConsolePrompt />
  </section>
{/if}
