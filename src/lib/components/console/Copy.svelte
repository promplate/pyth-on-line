<script lang="ts">
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import UseCopy from "./UseCopy.svelte";

  interface Props {
    text: string;
  }

  const { text }: Props = $props();
</script>

<UseCopy {text}>
  {#snippet children({ handleClick })}
    <WithTooltip tips="Copy">
      {#snippet children({ builder })}
        <button onclick={handleClick} class="i-icon-park-twotone-copy" {...builder} use:builder.action></button>
      {/snippet}
    </WithTooltip>
  {/snippet}
</UseCopy>
