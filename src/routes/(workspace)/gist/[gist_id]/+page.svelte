<script lang="ts">
  import type { PageData } from "./$types";

  import Workspace from "../../Workspace.svelte";

  interface Props {
    data: PageData;
  }

  const { data }: Props = $props();

  const { sources } = data;
</script>

<Workspace {sources} />
