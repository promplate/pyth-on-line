<script lang="ts">
  import type { Node, Table } from "mdast";

  export let node: Node;

  $: table = node as Table;
</script>

<table>

  <thead>
    <tr>
      {#each table.children[0].children as cell}
        <th>
          {#each cell.children as child}
            <slot {child} />
          {/each}
        </th>
      {/each}
    </tr>
  </thead>

  <tbody>
    {#each table.children.slice(1) as row}
      <tr>
        {#each row.children as cell}
          <td>
            {#each cell.children as child}
              <slot {child} />
            {/each}
          </td>
        {/each}
      </tr>
    {/each}
  </tbody>

</table>
