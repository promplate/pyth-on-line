<script lang="ts">
  import Console from "$lib/components/Console.svelte";
  import Modal from "$lib/components/Modal.svelte";
  import { pyodideReady } from "$lib/stores";
  import { cubicIn, cubicOut } from "svelte/easing";
  import { scale } from "svelte/transition";
</script>

<div class="m-4 w-auto flex flex-row gap-4 p-3 <lg:(m-3 gap-3 p-2 text-sm) <sm:(m-2 gap-2 p-1 text-xs)">

  <Console class="rounded bg-white/3 p-5 <lg:(p-4 text-sm) <sm:(p-3 text-xs)">

    {#snippet children({ ready })}
      <Modal show={!$pyodideReady || !ready}>
        <div in:scale|global={{ easing: cubicOut, start: 0.8 }} out:scale|global={{ easing: cubicIn, start: 0.9 }} class="rounded-lg bg-white/3 p-4 text-white/70">
          <div class="i-svg-spinners-90-ring-with-bg text-xl"></div>
        </div>
      </Modal>

    {/snippet}
  </Console>

</div>
