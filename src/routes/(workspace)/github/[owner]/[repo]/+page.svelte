<script lang="ts">
  import type { PageServerData } from "./$types";

  import Workspace from "../../../Workspace.svelte";

  export let data: PageServerData;

  const { sources } = data;
</script>

<Workspace {sources} />
