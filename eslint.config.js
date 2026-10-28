import antfu from "@antfu/eslint-config";

export default antfu({
  toml: false,
  svelte: true,
  typescript: true,
  stylistic: {
    quotes: "double",
    semi: true,
  },
  formatters: true,
  unocss: true,
  rules: {
    "perfectionist/sort-imports": ["error", {
      groups: ["type", ["side-effect", "side-effect-style"]],
    }],
    "import/order": "off",
    "node/prefer-global/process": "off",
    "svelte/no-at-html-tags": "off",
    "svelte/no-navigation-without-resolve": "off",
    "svelte/require-each-key": "off",
    "svelte/prefer-svelte-reactivity": "off",
    "antfu/reasonable-newline": "off",
    "no-console": "warn",
  },
  overrides: {
    svelte: {
      "import/no-mutable-exports": "off",
    },
  },
});
