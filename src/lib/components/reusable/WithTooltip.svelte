<script lang="ts">
  import { Tooltip } from "bits-ui";
  import { scale } from "svelte/transition";

  export let disableHoverableContent = true;
  export let tips: string;
</script>

<Tooltip.Root openDelay={400} closeDelay={0} {disableHoverableContent}>
  <Tooltip.Trigger asChild let:builder>
    <slot {builder} />
  </Tooltip.Trigger>
  <Tooltip.Content sideOffset={4} asChild let:builder>
    <div transition:scale={{ start: 0.95, duration: 300 }} class="rounded bg-neutral-2/10 px-0.5em py-0.3em text-xs text-neutral-3 backdrop-blur-sm" {...builder} use:builder.action>
      {tips}
    </div>
  </Tooltip.Content>
</Tooltip.Root>
