<script lang="ts">
  import UseCopy from "./UseCopy.svelte";

  export let text: string;
</script>

<UseCopy {text} let:handleClick>
  <button on:click={handleClick} class="i-icon-park-twotone-copy" />
</UseCopy>
