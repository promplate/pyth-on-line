<script lang="ts">
  import { createBubbler } from "svelte/legacy";

  const bubble = createBubbler();
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import ButtonGroup from "./ButtonGroup.svelte";
  import Copy from "./Copy.svelte";
  import MaybeAnsi from "./MaybeANSI.svelte";

  interface Props {
    text: string;
    onclick?: () => void;
  }

  const { text }: Props = $props();
</script>

<div class="group relative whitespace-normal">
  <div class="whitespace-pre-wrap text-red-4">
    <MaybeAnsi {text} />
  </div>

  <ButtonGroup>
    <Copy {text} />
    <WithTooltip tips="Ask AI">
      {#snippet children({ builder })}
        <button onclick={bubble("click")} class="i-majesticons-lightbulb-shine" {...builder} use:builder.action></button>
      {/snippet}
    </WithTooltip>
  </ButtonGroup>

</div>
