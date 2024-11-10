<script lang="ts">
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import ButtonGroup from "./ButtonGroup.svelte";
  import Copy from "./Copy.svelte";
  import MaybeAnsi from "./MaybeANSI.svelte";

  export let text: string;
</script>

<div class="group relative whitespace-normal">
  <div class="whitespace-pre-wrap text-red-4">
    <MaybeAnsi {text} />
  </div>

  <ButtonGroup>
    <Copy {text} />
    <WithTooltip tips="AI 解释" let:builder>
      <button on:click class="i-majesticons-lightbulb-shine" {...builder} use:builder.action />
    </WithTooltip>
  </ButtonGroup>

</div>
