<script lang="ts">
  import { Tooltip } from "bits-ui";
  import { scale } from "svelte/transition";

  interface Props {
    disableHoverableContent?: boolean;
    tips: string;
    children?: import("svelte").Snippet<[any]>;
  }

  const { disableHoverableContent = true, tips, children }: Props = $props();

  const children_render = $derived(children);
</script>

<Tooltip.Root openDelay={400} closeDelay={0} {disableHoverableContent}>
  <Tooltip.Trigger asChild>
    {#snippet children({ builder })}
      {@render children_render?.({ builder })}
    {/snippet}
  </Tooltip.Trigger>
  <Tooltip.Content sideOffset={4} asChild>
    {#snippet children({ builder })}
      <div transition:scale={{ start: 0.95, duration: 300 }} class="rounded bg-neutral-2/10 px-0.5em py-0.3em text-xs text-neutral-3 backdrop-blur-sm" {...builder} use:builder.action>
        {tips}
      </div>
    {/snippet}
  </Tooltip.Content>
</Tooltip.Root>
