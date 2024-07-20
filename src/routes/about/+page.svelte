<script lang="ts">
  import readme from "../../../README.md?raw";
  import Notebook from "$lib/components/Notebook.svelte";
  import { Button } from "bits-ui";
</script>

<div class="m-4 max-w-xl w-auto self-center lg:m-7 md:m-6 sm:m-5 xl:m-8 2xl:max-w-4xl lg:max-w-2xl xl:max-w-3xl [&>article]:(lg:text-3.75 xl:text-base)">

  <nav class="w-full flex flex-row items-center justify-between gap-2 text-sm lg:text-base [&>a:hover]:op-80 [&>a]:(op-50 transition)">
    <Button.Root href="/">Home</Button.Root>
    <Button.Root href="https://github.com/promplate/pyth-on-line"><div class="i-mdi-github text-xl" /></Button.Root>
  </nav>

  <hr class="invisible h-6">

  <Notebook text={readme} />
</div>
