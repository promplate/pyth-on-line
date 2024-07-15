<script lang="ts">
  import Console from "$lib/components/Console.svelte";
  import Modal from "$lib/components/Modal.svelte";
  import { pyodideReady } from "$lib/stores";
  import { cubicIn, cubicOut } from "svelte/easing";
  import { scale } from "svelte/transition";
</script>

<div class="my-4 w-[calc(100vw-2rem)] flex flex-row gap-4 break-all p-3 text-neutral-3 <lg:(my-3 w-[calc(100vw-1.5rem)] gap-3 p-2 text-sm) <sm:(my-2 w-[calc(100vw-1rem)] gap-2 p-1 text-xs)">

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

</div>
