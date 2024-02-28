<script lang="ts">
  import ButtonGroup from "./ButtonGroup.svelte";
  import Copy from "./Copy.svelte";

  export let text: string;
</script>

<div class="group relative whitespace-normal">
  <div class="whitespace-pre-wrap text-red-4">{text}</div>

  <ButtonGroup>
    <Copy {text} />
    <button on:click class="i-majesticons-lightbulb-shine" />
  </ButtonGroup>

</div>
