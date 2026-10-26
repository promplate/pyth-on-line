<script lang="ts">
  import { Avatar } from "bits-ui";

  const { url, name = null, login, ...props }: Omit<Avatar.Props, "name" | "children"> & { url: string; name?: string | null; login: string } = $props();
</script>

<Avatar.Root {...props}>
  <div class="grid size-full place-items-center overflow-hidden rounded-1/5 bg-neutral-1/5">
    <Avatar.Image src={url} alt={name ?? `@${login}`} />
    <Avatar.Fallback class="text-sm text-neutral-1/50">
      {name?.includes(" ") ? name.split(" ").slice(0, 2).map(word => word[0]).join("") : (name ?? login).slice(0, 2)}
    </Avatar.Fallback>
  </div>
</Avatar.Root>
