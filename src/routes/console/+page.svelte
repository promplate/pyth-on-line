<script lang="ts">
  import Console from "$lib/components/Console.svelte";
  import Modal from "$lib/components/Modal.svelte";
  import { pyodideReady } from "$lib/stores";
  import { cubicIn, cubicOut } from "svelte/easing";
  import { scale } from "svelte/transition";
</script>

<Console let:ready>

  <Modal show={!$pyodideReady || !ready}>
    <svelte:fragment slot="content">
      {#await Promise.resolve() then _}
        <div in:scale={{ easing: cubicOut, start: 0.8 }} out:scale|global={{ easing: cubicIn, start: 0.9 }} class="rounded-lg bg-white/3 p-4 text-white/70">
          <div class="i-svg-spinners-90-ring-with-bg text-xl" />
        </div>
      {/await}
    </svelte:fragment>
  </Modal>

</Console>
