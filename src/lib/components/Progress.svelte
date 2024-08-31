<script context="module" lang="ts">
  import { spring } from "svelte/motion";

  export const progress = spring(0, {
    stiffness: 0.1,
    damping: 1,
    precision: 0.001,
  });
</script>

<slot value={$progress} />
