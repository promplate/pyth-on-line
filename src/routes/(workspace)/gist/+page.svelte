<script lang="ts">
  import type { PageData } from "./$types";

  import GitHubUser from "$lib/components/GitHubUser.svelte";
  import { fromNow } from "$lib/date";

  export let data: PageData;

  const { avatarUrl, name, login, total, gists } = data;
</script>

<div class="m-4 flex flex-col gap-3 sm:m-3vw sm:gap-4">
  <div class="flex flex-row items-center justify-between gap-2 ws-nowrap text-xl sm:(text-3xl font-250)">
    <h1>
      <span class="text-neutral-5">来自</span>
      <span class="text-neutral-3">{name ?? `@${login}`}</span>
      <span class="text-neutral-5">的</span>
      <span class="text-neutral-2">{total}</span>
      <span class="text-neutral-5">个代码片段</span>
    </h1>
    <GitHubUser url={avatarUrl} {name} {login} class="size-7 shrink-0 sm:size-10" />
  </div>
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
