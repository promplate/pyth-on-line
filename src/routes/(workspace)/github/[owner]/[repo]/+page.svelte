<script lang="ts">
  import type { PageServerData } from "./$types";

  import Workspace from "../../../Workspace.svelte";

  interface Props {
    data: PageServerData;
  }

  const { data }: Props = $props();

  const { sources } = data;
</script>

<Workspace {sources} />
