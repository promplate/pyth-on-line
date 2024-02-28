<script lang="ts">
  export let href: string;
  export let title: string;
  export let subtitle: string;
</script>

<section
  style="
    background-color: white;
    background-image: linear-gradient(-20deg, #cdcabe28 10px, white 0px);
    background-size: 40px 40px;
  "
  class="h-full w-full flex p-32"
>
  <div class="flex flex-col justify-between">
    <div class="flex flex-col">
      <h1 class="m-0 rounded-lg bg-neutral-800 px-6 py-4 text-12 text-neutral-200 font-bold tracking-wide capitalize">{title ?? "promplate docs"}</h1>
      <h2 class="mb-0 text-8 text-neutral-900/25 tracking-widest uppercase">{subtitle ?? "the prompting framework"}</h2>
    </div>
    <a class="border-l-8 border-[#1e754fa8] pl-4 text-7 text-[#4d9375]" {href}>{href}</a>
  </div>
  <div class="absolute bottom-32 right-32 flex items-center justify-center rounded-full bg-[#bd976a] px-5 pb-2 pt-1.5 text-6 text-white -m-1.5">python</div>
</section>
