<script lang="ts">
  import type { Snippet } from "svelte";

  import { Tooltip } from "bits-ui";
  import { scale } from "svelte/transition";

  // Bits UI 0.22 exposes trigger builders through its legacy slot type.
  type TriggerBuilder = InstanceType<typeof Tooltip.Trigger>["$$slot_def"]["default"]["builder"];

  const { disableHoverableContent = true, tips, children }: { disableHoverableContent?: boolean; tips: string; children: Snippet<[TriggerBuilder]> } = $props();
</script>

<Tooltip.Root openDelay={400} closeDelay={0} {disableHoverableContent}>
  <Tooltip.Trigger asChild let:builder>
    {@render children(builder)}
  </Tooltip.Trigger>
  <Tooltip.Content sideOffset={4} asChild let:builder>
    <div transition:scale={{ start: 0.95, duration: 300 }} class="rounded bg-neutral-2/10 px-0.5em py-0.3em text-xs text-neutral-3 backdrop-blur-sm" {...builder} use:builder.action>
      {tips}
    </div>
  </Tooltip.Content>
</Tooltip.Root>
