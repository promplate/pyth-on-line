<script lang="ts">
  import type { PageProps } from "./$types";

  import { goto } from "$app/navigation";
  import { accessToken, login } from "$lib/oauth";
  import { untrack } from "svelte";

  const { data }: PageProps = $props();
  const token = $derived(data.access_token);

  $effect(() => {
    if (!token)
      return;

    // Only a new callback token should redirect, not state read by auth or navigation.
    untrack(() => {
      $accessToken = token;
      goto(sessionStorage.getItem("continue") ?? "/github");
      sessionStorage.removeItem("continue");
    });
  });
</script>

<div class="fixed inset-0 grid place-items-center">
  <div>
    {#if token}
      Login successful, redirecting...
    {:else}
      Failed to login,
      <button class="inline underline underline-(white offset-2) not-hover:underline-op-30" onclick={login}>retry</button>?
    {/if}
  </div>
</div>
