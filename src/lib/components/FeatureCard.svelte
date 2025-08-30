<script lang="ts">
  import WithTooltip from "./reusable/WithTooltip.svelte";
  import { Button } from "bits-ui";

  interface Props {

    href?: string | undefined;
    icon: string;
    title: string;
    description: string;
  }

  const {
    href = undefined,
    icon,
    title,
    description,
  }: Props = $props();
</script>

<Button.Root {href} on:click class="max-h-40 w-fit rounded-md bg-white/3 transition active:bg-white/10 hover:bg-white/7">
  <WithTooltip tips={description}>
    {#snippet children({ builder })}
      <div class="flex flex-col px-2.5 py-2" {...builder} use:builder.action>
        <div class="flex flex-row items-center gap-1.5">
          <div class="{icon} text-base"></div>
          <h3 class="text-sm">{title}</h3>
        </div>
      </div>
    {/snippet}
  </WithTooltip>
</Button.Root>
