<script lang="ts">
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import UseCopy from "./UseCopy.svelte";
  import { mergeProps } from "bits-ui";

  const { text }: { text: string } = $props();
</script>

<UseCopy {text}>
  {#snippet children(handleClick)}
    <WithTooltip tips="Copy">
      {#snippet children({ props })}
        <button aria-label="Copy text" class="i-icon-park-twotone-copy" {...mergeProps(props, { onclick: handleClick })}></button>
      {/snippet}
    </WithTooltip>
  {/snippet}
</UseCopy>
