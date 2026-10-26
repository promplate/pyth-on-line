<script lang="ts">
  import WithTooltip from "./reusable/WithTooltip.svelte";
  import { Button } from "bits-ui";
  import { fromAction } from "svelte/attachments";

  const { href, icon, title, description, onclick }: { href?: string; icon: string; title: string; description: string; onclick?: (event: MouseEvent) => void } = $props();
</script>

<!-- Bits UI 0.22 still exposes click through its component event API. -->
<Button.Root {href} on:click={event => onclick?.(event)} class="max-h-40 w-fit rounded-md bg-white/3 transition active:bg-white/10 hover:bg-white/7">
  <WithTooltip tips={description}>
    {#snippet children(builder)}
      <div class="flex flex-col px-2.5 py-2" {...builder} {@attach fromAction((node: HTMLElement) => builder.action(node), () => undefined)}>
        <div class="flex flex-row items-center gap-1.5">
          <div class="{icon} text-base" />
          <h3 class="text-sm">{title}</h3>
        </div>
      </div>
    {/snippet}
  </WithTooltip>
</Button.Root>
