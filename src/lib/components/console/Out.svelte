<script lang="ts">
  import ButtonGroup from "./ButtonGroup.svelte";
  import Copy from "./Copy.svelte";
  import MaybeAnsi from "./MaybeANSI.svelte";

  const { text }: { text: string } = $props();
</script>

<div class="group relative whitespace-normal">
  <div class="whitespace-pre-wrap text-yellow-2">
    <MaybeAnsi {text} />
  </div>
  <ButtonGroup>
    <Copy {text} />
  </ButtonGroup>
</div>
