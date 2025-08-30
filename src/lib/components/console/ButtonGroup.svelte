<script lang="ts">
  interface Props {
    children?: import("svelte").Snippet;
  }

  const { children }: Props = $props();
</script>

<div class="absolute bottom-0.4em right-0.4em flex flex-row-reverse items-center gap-1.5 text-1em op-0 [&>button:active]:scale-85 [&>button:hover]:op-70 group-hover:(op-100 transition-opacity duration-300)">
  {@render children?.()}
</div>
