<script lang="ts">
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import ButtonGroup from "./ButtonGroup.svelte";
  import Copy from "./Copy.svelte";
  import MaybeAnsi from "./MaybeANSI.svelte";
  import { mergeProps } from "bits-ui";

  const { text, onclick }: { text: string; onclick?: (event: MouseEvent) => void } = $props();
</script>

<div class="group relative whitespace-normal">
  <div class="whitespace-pre-wrap text-red-4">
    <MaybeAnsi {text} />
  </div>

  <ButtonGroup>
    <Copy {text} />
    <WithTooltip tips="Ask AI">
      {#snippet children({ props })}
        <button class="i-majesticons-lightbulb-shine" {...mergeProps(props, { onclick })}></button>
      {/snippet}
    </WithTooltip>
  </ButtonGroup>

</div>
