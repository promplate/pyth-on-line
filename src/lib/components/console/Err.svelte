<script lang="ts">
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import ButtonGroup from "./ButtonGroup.svelte";
  import Copy from "./Copy.svelte";
  import MaybeAnsi from "./MaybeANSI.svelte";
  import { fromAction } from "svelte/attachments";

  const { text, onclick }: { text: string; onclick?: (event: MouseEvent) => void } = $props();
</script>

<div class="group relative whitespace-normal">
  <div class="whitespace-pre-wrap text-red-4">
    <MaybeAnsi {text} />
  </div>

  <ButtonGroup>
    <Copy {text} />
    <WithTooltip tips="Ask AI">
      {#snippet children(builder)}
        <button class="i-majesticons-lightbulb-shine" {...builder} {onclick} {@attach fromAction((node: HTMLElement) => builder.action(node), () => undefined)} />
      {/snippet}
    </WithTooltip>
  </ButtonGroup>

</div>
