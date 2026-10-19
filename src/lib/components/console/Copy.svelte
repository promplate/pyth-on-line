<script lang="ts">
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import UseCopy from "./UseCopy.svelte";

  export let text: string;
</script>

<UseCopy {text}>
  {#snippet children(handleClick)}
    <WithTooltip tips="Copy">
      {#snippet children(builder)}
        <button onclick={handleClick} class="i-icon-park-twotone-copy" {...builder} use:builder.action />
      {/snippet}
    </WithTooltip>
  {/snippet}
</UseCopy>
