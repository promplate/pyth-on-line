<script lang="ts">
  import type { PageData } from "./$types";

  import GitHubTokenManager from "$lib/components/GitHubTokenManager.svelte";
  import GitHubUser from "$lib/components/GitHubUser.svelte";
  import { fromNow } from "$lib/date";
  import { hasUserToken } from "$lib/user-token";

  export let data: PageData;

  const { avatarUrl, name, login, total, gists } = data;

  let showTokenManager = false;
</script>

<div class="m-4 flex flex-col gap-3 sm:m-3vw sm:gap-4">
  <div class="flex flex-row items-center justify-between gap-2 ws-nowrap text-xl sm:(text-3xl font-250)">
    <h1>
      <span class="text-neutral-2">{total}</span>
      <span class="text-neutral-5">Gists from</span>
      <span class="text-neutral-3">{name ?? `@${login}`}</span>
    </h1>
    <div class="flex items-center gap-3">
      <button
        on:click={() => showTokenManager = !showTokenManager}
        class="flex items-center gap-1.5 rounded bg-neutral-8/50 px-3 py-1.5 text-sm transition-colors hover:bg-neutral-8"
        title="Manage GitHub token for private gists"
      >
        <div class="i-material-symbols-key h-4 w-4" />
        {#if $hasUserToken}
          <span class="text-green-400">Token set</span>
        {:else}
          <span>Set token</span>
        {/if}
      </button>
      <GitHubUser url={avatarUrl} {name} {login} class="size-7 shrink-0 sm:size-10" />
    </div>
  </div>

  {#if showTokenManager}
    <div class="border border-neutral-7 rounded bg-neutral-9/50 p-4">
      <GitHubTokenManager />
    </div>
  {/if}

  {#if !$hasUserToken && gists.some(g => !g.isPublic)}
    <div class="border border-yellow-600/30 rounded bg-yellow-600/20 p-3 text-sm text-yellow-100">
      <h3 class="mb-1 font-medium">Private Gists Detected</h3>
      <p>
        Some of your gists are private. You may need to
        <button
          on:click={() => showTokenManager = true}
          class="text-yellow-200 underline hover:text-yellow-100"
        >
          set up a GitHub token
        </button>
        to access them from this application.
      </p>
    </div>
  {/if}

  <ul class="flex flex-row flex-wrap gap-3 text-sm">
    {#each gists as { name, description, updatedAt, isPublic, stargazerCount, viewerHasStarred }}
      <li class="contents">
        <a href="/gist/{name}" class="max-w-full flex flex-col gap-1.5 ws-nowrap rounded bg-neutral-8/30 px-2.5 py-2 outline-none ring-(1 neutral-7/30) transition hover:bg-neutral-8/80 focus:ring-(1.5 neutral-5) hover:ring-neutral-7/80">
          <div class="flex flex-row items-center justify-between gap-2">
            <h2 class="overflow-hidden text-ellipsis">{description || name.slice(0, 8)}</h2>
            {#if isPublic}
              <div class="i-material-symbols-public shrink-0 op-50" />
            {/if}
          </div>
          <div class="flex flex-row items-center gap-2 op-50">
            {#if stargazerCount}
              <div class="flex flex-row items-center gap-0.5">
                {stargazerCount}
                <div class={viewerHasStarred ? "i-material-symbols-kid-star" : "i-material-symbols-kid-star-outline"} />
              </div>
            {/if}
            <div class="ml-auto">
              {fromNow(updatedAt)}
            </div>
          </div>
        </a>
      </li>
    {/each}
  </ul>
</div>
