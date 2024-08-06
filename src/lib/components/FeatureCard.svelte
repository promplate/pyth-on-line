<script lang="ts">
  import WithTooltip from "./reusable/WithTooltip.svelte";
  import { Button } from "bits-ui";

  // eslint-disable-next-line no-undef-init
  export let href: string | undefined = undefined;
  export let icon: string;
  export let title: string;
  export let description: string;
</script>

<Button.Root {href} on:click class="max-h-40 w-fit rounded-md bg-white/3 transition active:bg-white/10 hover:bg-white/7">
  <WithTooltip let:builder tips={description}>
    <div class="flex flex-col px-2.5 py-2" {...builder} use:builder.action>
      <div class="flex flex-row items-center gap-1.5">
        <div class="{icon} text-base" />
        <h3 class="text-sm">{title}</h3>
      </div>
    </div>
  </WithTooltip>
</Button.Root>
