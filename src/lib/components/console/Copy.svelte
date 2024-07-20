<script lang="ts">
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import UseCopy from "./UseCopy.svelte";

  export let text: string;
</script>

<UseCopy {text} let:handleClick>
  <WithTooltip tips="Copy" let:builder>
    <button on:click={handleClick} class="i-icon-park-twotone-copy" {...builder} use:builder.action />
  </WithTooltip>
</UseCopy>
