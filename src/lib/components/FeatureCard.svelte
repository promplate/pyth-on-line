<script lang="ts">
  import WithTooltip from "./reusable/WithTooltip.svelte";
  import { Button, mergeProps } from "bits-ui";

  const { href, icon, title, description, onclick }: { href?: string; icon: string; title: string; description: string; onclick?: (event: MouseEvent) => void } = $props();
</script>

<WithTooltip tips={description}>
  {#snippet children({ props })}
    <Button.Root {href} {...mergeProps(props, { onclick })} class="max-h-40 w-fit rounded-md bg-white/3 transition active:bg-white/10 hover:bg-white/7">
      <div class="flex flex-col px-2.5 py-2">
        <div class="flex flex-row items-center gap-1.5">
          <div class="{icon} text-base"></div>
          <h3 class="text-sm">{title}</h3>
        </div>
      </div>
    </Button.Root>
  {/snippet}
</WithTooltip>
