<script lang="ts">
  import { evalPython } from "$lib/pyodide/worker/workerApi";

  let input = "";
  let output: any;
  let error: any;

  $: if (input) {
    evalPython(input)
      .then((res) => {
        output = res;
        error = "";
      })
      .catch((err) => {
        error = err;
        output = "";
      });
  }
  else {
    output = "";
    error = "";
  }
</script>

<div class="m-10 flex flex-col gap-2.5 font-mono [&>*]:(px-2.5 py-2)">

  <input type="text" bind:value={input} class="bg-neutral-8 outline-none ring-(1.2 neutral-4)">

  {#if error}
    <div class="ws-pre-wrap text-sm text-red">{error}</div>
  {/if}

  {#if output}
    <div class="ws-pre-wrap text-sm text-teal">{output}</div>
  {/if}

</div>
