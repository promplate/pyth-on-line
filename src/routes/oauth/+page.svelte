<script lang="ts">
  import type { PageServerData } from "./$types";

  import { goto } from "$app/navigation";
  import { accessToken, login } from "$lib/oauth";
  import { onMount } from "svelte";

  export let data: PageServerData;

  const success = Boolean(data.access_token);

  success && onMount(() => {
    $accessToken = data.access_token;
    goto(sessionStorage.getItem("continue") ?? "/github");
    sessionStorage.removeItem("continue");
  });
</script>

<div class="fixed inset-0 grid place-items-center">
  <div>
    {#if success}
      Login successful, redirecting...
    {:else}
      Failed to login,
      <button class="inline underline underline-(white offset-2) not-hover:underline-op-30" on:click={login}>retry</button>?
    {/if}
  </div>
</div>
