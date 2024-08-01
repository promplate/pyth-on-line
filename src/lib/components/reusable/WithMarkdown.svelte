<script context="module">
  import "../../md.css";

  import { remark } from "remark";
  import remarkGfm from "remark-gfm";

  const processor = remark().use(remarkGfm);
  const parse = processor.parse.bind(processor);
</script>

<article class="max-w-full text-sm text-neutral-2 font-sans prose [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
  <slot {parse} />
</article>
