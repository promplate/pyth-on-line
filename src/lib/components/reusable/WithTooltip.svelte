<script lang="ts">
  import { Tooltip } from "bits-ui";
  import { scale } from "svelte/transition";

  const { disableHoverableContent = true, tips, children }: { disableHoverableContent?: boolean; tips: string; children: Tooltip.TriggerProps["child"] } = $props();
</script>

<Tooltip.Provider skipDelayDuration={0}>
  <Tooltip.Root delayDuration={400} {disableHoverableContent}>
    <Tooltip.Trigger child={children} />
    <Tooltip.Portal>
      <Tooltip.Content sideOffset={4} forceMount>
        {#snippet child({ wrapperProps, props, open })}
          {#if open}
            <div {...wrapperProps}>
              <div role="tooltip" transition:scale={{ start: 0.95, duration: 300 }} class="rounded bg-neutral-2/10 px-0.5em py-0.3em text-xs text-neutral-3 backdrop-blur-sm" {...props}>
                {tips}
              </div>
            </div>
          {/if}
        {/snippet}
      </Tooltip.Content>
    </Tooltip.Portal>
  </Tooltip.Root>
</Tooltip.Provider>
