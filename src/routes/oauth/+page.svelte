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
      登录成功，正在重定向...
    {:else}
      登陆失败，
      <button class="inline underline underline-(white offset-2) not-hover:underline-op-30" on:click={login}>重试</button>?
    {/if}
  </div>
</div>
