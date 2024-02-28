<script lang="ts">
  import ButtonGroup from "./ButtonGroup.svelte";
  import Copy from "./Copy.svelte";

  export let text: string;
</script>

<div class="group relative whitespace-normal">
  <div class="whitespace-pre-wrap text-cyan-2">{text}</div>
  <ButtonGroup>
    <Copy {text} />
  </ButtonGroup>
</div>
