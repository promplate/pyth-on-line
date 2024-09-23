<script lang="ts">
  import { Avatar } from "bits-ui";

  export let url: string;
  export let name: string | null = null;
  export let login: string;
</script>

<Avatar.Root {...$$restProps}>
  <div class="grid size-full place-items-center overflow-hidden rounded-1/5 bg-neutral-1/5">
    <Avatar.Image src={url} alt={name ?? `@${login}`} />
    <Avatar.Fallback class="text-sm text-neutral-1/50">
      {name?.includes(" ") ? name.split(" ").slice(0, 2).map(word => word[0]).join("") : (name ?? login).slice(0, 2)}
    </Avatar.Fallback>
  </div>
</Avatar.Root>
