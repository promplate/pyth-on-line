<script>
  import Modal from "$lib/components/Modal.svelte";
  import { onMount } from "svelte";

  let show = false;

  onMount(() => {
    setTimeout(() => {
      show = true;
    }, 100);
  });
</script>

<Modal {show}>
  <div slot="content" class="h-30 w-70 bg-cyan" />
</Modal>

<Modal show>
  <div slot="content" class="h-60 w-60 bg-red">
</Modal>

<div class="fixed bottom-20 self-center">the cyan square should be on top of the red one</div>
