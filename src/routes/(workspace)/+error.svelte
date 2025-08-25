<script lang="ts">
  import { page } from "$app/stores";
  import GitHubTokenManager from "$lib/components/GitHubTokenManager.svelte";
  import { hasUserToken } from "$lib/user-token";

  let showTokenManager = false;

  $: isPrivateGistError = $page.status === 403 && $page.error?.message?.includes("private gist");
</script>

<div class="grid h-95vh place-items-center p-4">
  <div class="max-w-2xl flex flex-col gap-6">
    <h1 class="text-5xl font-200 tracking-widest">{$page.status}</h1>
    <h2 class="min-w-sm overflow-x-scroll whitespace-pre rounded bg-white/5 p-5 font-mono -mx-1">{$page.error?.message}</h2>

    {#if isPrivateGistError}
      <div class="space-y-4">
        <div class="border border-yellow-600/30 rounded bg-yellow-600/20 p-4 text-yellow-100">
          <h3 class="mb-2 font-medium">This appears to be a private gist</h3>
          <p class="text-sm">
            To access private or secret gists, you need to provide your own GitHub personal access token
            with the <code class="rounded bg-yellow-800/50 px-1">gist</code> scope.
          </p>
        </div>

        {#if !$hasUserToken}
          <div class="flex flex-col gap-3">
            <button
              on:click={() => showTokenManager = !showTokenManager}
              class="rounded bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
            >
              {showTokenManager ? "Hide" : "Set up"} GitHub Token
            </button>

            {#if showTokenManager}
              <div class="border border-neutral-7 rounded bg-neutral-9/50 p-4">
                <GitHubTokenManager />
              </div>
            {/if}
          </div>
        {:else}
          <div class="space-y-3">
            <p class="text-sm text-green-400">
              ✓ You have a GitHub token configured. Try refreshing the page.
            </p>
            <button
              on:click={() => location.reload()}
              class="rounded bg-green-600 px-4 py-2 text-white transition-colors hover:bg-green-700"
            >
              Refresh Page
            </button>
          </div>
        {/if}
      </div>
    {:else}
      <div class="flex gap-3">
        <button
          on:click={() => history.back()}
          class="rounded bg-neutral-600 px-4 py-2 text-white transition-colors hover:bg-neutral-700"
        >
          Go Back
        </button>
        <button
          on:click={() => location.reload()}
          class="rounded bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    {/if}
  </div>
</div>
