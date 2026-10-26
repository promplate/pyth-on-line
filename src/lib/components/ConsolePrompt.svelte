<script lang="ts">
  const { prompt = ">>>" }: { prompt?: string } = $props();
</script>

<span class="flex-shrink-0 select-none op-25 group-hover:op-100">{`${prompt} `}</span>

<style>
  span {
    font-feature-settings: "calt" 0;
  }
</style>
