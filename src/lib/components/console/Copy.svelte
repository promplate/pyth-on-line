<script lang="ts">
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import UseCopy from "./UseCopy.svelte";
  import { fromAction } from "svelte/attachments";

  export let text: string;
</script>

<UseCopy {text}>
  {#snippet children(handleClick)}
    <WithTooltip tips="Copy">
      {#snippet children(builder)}
        <button onclick={handleClick} class="i-icon-park-twotone-copy" {...builder} {@attach fromAction((node: HTMLElement) => builder.action(node), () => undefined)} />
      {/snippet}
    </WithTooltip>
  {/snippet}
</UseCopy>
