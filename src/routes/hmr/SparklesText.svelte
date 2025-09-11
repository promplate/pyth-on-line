<script lang="ts">
  import { cn } from "$lib/utils/clsx";
  import { onDestroy, onMount } from "svelte";

  type Timeout = ReturnType<typeof setTimeout>;

  interface Sparkle {
    id: number;
    x: number;
    y: number;
    color: string;
    scale: number;
    zIndex: number;
  }

  const timeouts: Set<Timeout> = new Set();

  function schedule(callback: () => void, delay: number): Timeout {
    const timer = setTimeout(callback, delay);
    timeouts.add(timer);
    return timer;
  }

  function clearTimeouts() {
    timeouts.forEach(timer => clearTimeout(timer));
    timeouts.clear();
  }

  export let text: string;

  let additionalClasses = "";
  export { additionalClasses as class };

  const PALETTE = ["#cb7676", "#bd976a", "#b8a965", "#c98a7d", "#5da994", "#80a665"] as const;
  const MAX_ATTEMPTS = 50;
  const POTENTIAL_THRESHOLD = 0.0005;

  let sparkles: Sparkle[] = [];
  let id = 0;

  function generateStar(): Sparkle | null {
    for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
      const newX = Math.random() * 100;
      const newY = Math.random() * 100;

      let sum = 0;

      for (const star of sparkles) {
        sum += 1 / ((newX - star.x) ** 4 + (newY - star.y) ** 2); // emphasize horizontal distance

        if (sum >= POTENTIAL_THRESHOLD) {
          break;
        }
      }

      if (sum < POTENTIAL_THRESHOLD || sparkles.length === 0) {
        const color = PALETTE[Math.floor(Math.random() * PALETTE.length)];
        const scale = Math.random() * 0.7 + 0.3;
        const zIndex = Math.random() < 0.4 ? -1 : 1;
        return { id: id++, x: newX, y: newY, color, scale, zIndex };
      }
    }

    return null;
  }

  function addNewStar() {
    const star = generateStar();
    if (star) {
      sparkles = [...sparkles, star];
    }

    // 1s / 10 stars = 100ms per star on average
    schedule(addNewStar, 100 + Math.random() * 100);
  }

  function removeStar(id: number) {
    sparkles = sparkles.filter(star => star.id !== id);
  }

  onMount(addNewStar);
  onDestroy(clearTimeouts);
</script>

<div class={cn("relative inline-block", additionalClasses)} {...$$restProps}>
  <span class="relative inline-block">
    {#each sparkles as { id, x, y, color, scale, zIndex } (id)}
      <div style:left="{x}%" style:top="{y}%" style:--sparkle-scale={scale} style:z-index={zIndex} on:animationend={() => removeStar(id)} class="pointer-events-none absolute -translate-1/2">
        <svg width="21" height="21" viewBox="0 0 21 21" style:color={color} style:--glow-color="color-mix(in srgb, {color} 60%, transparent)">
          <path fill={color} d="M9.82531 0.843845C10.0553 0.215178 10.9446 0.215178 11.1746 0.843845L11.8618 2.72026C12.4006 4.19229 12.3916 6.39157 13.5 7.5C14.6084 8.60843 16.8077 8.59935 18.2797 9.13822L20.1561 9.82534C20.7858 10.0553 20.7858 10.9447 20.1561 11.1747L18.2797 11.8618C16.8077 12.4007 14.6084 12.3916 13.5 13.5C12.3916 14.6084 12.4006 16.8077 11.8618 18.2798L11.1746 20.1562C10.9446 20.7858 10.9553 20.7858 9.82531 20.1562L9.13819 18.2798C8.59932 16.8077 8.60843 14.6084 7.5 13.5C6.39157 12.3916 4.19225 12.4007 2.72023 11.8618L0.843814 11.1747C0.215148 10.9447 0.215148 10.0553 0.843814 9.82534L2.72023 9.13822C4.19225 8.59935 6.39157 8.60843 7.5 7.5C8.60843 6.39157 8.59932 4.19229 9.13819 2.72026L9.82531 0.843845Z" />
        </svg>
      </div>
    {/each}
    <strong class="relative">{text}</strong>
  </span>
</div>

<style>
  svg {
    animation: sparkle-pulse 1s ease-in-out;
    animation-fill-mode: both;
    filter: drop-shadow(0 0 5px var(--glow-color));
  }

  @keyframes sparkle-pulse {
    0% {
      opacity: 0;
      transform: scale(0.2) rotate(75deg);
    }
    50% {
      opacity: 1;
      transform: scale(var(--sparkle-scale, 1)) rotate(120deg);
    }
    100% {
      opacity: 0;
      transform: scale(0.2) rotate(150deg);
    }
  }
</style>
