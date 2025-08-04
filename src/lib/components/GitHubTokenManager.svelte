<script lang="ts">
  import { clearUserToken, hasUserToken, isValidTokenFormat, userGitHubToken, validateToken } from "$lib/user-token";
  import { toast } from "svelte-sonner";

  let tokenInput = "";
  let isValidating = false;
  let validationResult: { valid: boolean; error?: string; user?: { login: string; name: string } } | null = null;
  let showToken = false;

  // Initialize with current token value
  $: if ($userGitHubToken && !tokenInput) {
    tokenInput = $userGitHubToken;
  }

  async function handleValidateAndSave() {
    if (!tokenInput.trim()) {
      toast.error("Please enter a token");
      return;
    }

    if (!isValidTokenFormat(tokenInput)) {
      toast.error("Invalid token format. Expected ghp_... or github_pat_...");
      return;
    }

    isValidating = true;
    validationResult = null;

    try {
      const result = await validateToken(tokenInput);
      validationResult = result;

      if (result.valid) {
        userGitHubToken.set(tokenInput);
        toast.success(`Token validated and saved! Connected as @${result.user?.login}`);
      }
      else {
        toast.error(result.error || "Token validation failed");
      }
    }
    catch {
      toast.error("Failed to validate token");
      validationResult = { valid: false, error: "Validation failed" };
    }
    finally {
      isValidating = false;
    }
  }

  function handleClear() {
    clearUserToken();
    tokenInput = "";
    validationResult = null;
    toast.info("GitHub token cleared");
  }

  function toggleShowToken() {
    showToken = !showToken;
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between">
    <h3 class="text-lg font-medium">GitHub Personal Access Token</h3>
    {#if $hasUserToken}
      <span class="rounded bg-green-600/20 px-2 py-1 text-xs text-green-300">
        Token configured
      </span>
    {/if}
  </div>

  <div class="text-sm text-neutral-400 space-y-2">
    <p>
      Provide your GitHub personal access token to access private/secret gists.
      This token is stored locally and never sent to our servers.
    </p>
    <p>
      <strong>Required scopes:</strong> <code class="rounded bg-neutral-8 px-1">gist</code>
    </p>
    <p class="text-xs">
      <a
        href="https://github.com/settings/tokens/new?scopes=gist&description=Pyth-on-line%20gist%20access"
        target="_blank"
        rel="noopener noreferrer"
        class="text-blue-400 underline hover:text-blue-300"
      >
        Create a new token →
      </a>
    </p>
  </div>

  <div class="space-y-3">
    <div class="relative">
      {#if showToken}
        <input
          bind:value={tokenInput}
          type="text"
          placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
          class="w-full border border-neutral-7 rounded bg-neutral-8 px-3 py-2 pr-10 text-sm font-mono focus:border-neutral-5 focus:outline-none"
          disabled={isValidating}
        />
      {:else}
        <input
          bind:value={tokenInput}
          type="password"
          placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
          class="w-full border border-neutral-7 rounded bg-neutral-8 px-3 py-2 pr-10 text-sm font-mono focus:border-neutral-5 focus:outline-none"
          disabled={isValidating}
        />
      {/if}
      <button
        type="button"
        on:click={toggleShowToken}
        class="absolute right-2 top-1/2 p-1 text-neutral-400 -translate-y-1/2 hover:text-neutral-200"
        title={showToken ? "Hide token" : "Show token"}
      >
        <div class="h-4 w-4 {showToken ? "i-material-symbols-visibility-off" : "i-material-symbols-visibility"}" />
      </button>
    </div>

    <div class="flex gap-2">
      <button
        on:click={handleValidateAndSave}
        disabled={isValidating || !tokenInput.trim()}
        class="rounded bg-blue-600 px-4 py-2 text-sm text-white transition-colors disabled:cursor-not-allowed disabled:bg-neutral-7 hover:bg-blue-700"
      >
        {#if isValidating}
          <div class="i-material-symbols-progress-activity mr-2 inline-block h-4 w-4 animate-spin" />
          Validating...
        {:else}
          Validate & Save
        {/if}
      </button>

      {#if $hasUserToken}
        <button
          on:click={handleClear}
          class="rounded bg-red-600 px-4 py-2 text-sm text-white transition-colors hover:bg-red-700"
        >
          Clear Token
        </button>
      {/if}
    </div>

    {#if validationResult}
      <div class="text-sm {validationResult.valid ? "text-green-400" : "text-red-400"}">
        {#if validationResult.valid && validationResult.user}
          ✓ Valid token for @{validationResult.user.login}
          {#if validationResult.user.name}
            ({validationResult.user.name})
          {/if}
        {:else if validationResult.error}
          ✗ {validationResult.error}
        {/if}
      </div>
    {/if}
  </div>
</div>
