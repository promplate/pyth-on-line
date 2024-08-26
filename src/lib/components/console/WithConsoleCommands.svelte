<script lang="ts">
  import type { ConsoleAPI } from "$py/console/console";

  import { input, items, placeholder, prefixes, show } from "../command/CmdK.svelte";
  import { registerCommandGroup } from "../command/helper";
  import getPy from "$lib/pyodide";
  import { tick } from "svelte";

  export let pyConsole: ConsoleAPI;

  const installTitle = "Install Packages";

  registerCommandGroup("Console", [
    {
      text: installTitle,
      async handler() {
        $prefixes = [installTitle];
        $placeholder = "<package1> <package2> ...";

        const unsubscribe = input.subscribe(($input) => {
          $items = [{
            async callback() {
              $items = [];
              $prefixes = [];
              $placeholder = "";
              unsubscribe();
              await tick();

              const packages = $input.split(" ").filter(Boolean);
              if (packages?.length) {
                const py = await getPy();
                py.pyimport("micropip.install")(packages);
              }
              else {
                requestAnimationFrame(() => $show = true);
              }
            },
            type: "cmd",
            text: $input ? `pip install ${$input}` : "(cancel)",
            alwaysRender: true,
          }];
        });

        requestAnimationFrame(() => $show = true);
      },
    },
    {
      text: "Clear Console",
      handler() {
        pyConsole.clear();
      },
    },
  ]);
</script>
