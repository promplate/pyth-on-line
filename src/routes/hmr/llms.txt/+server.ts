import type { RequestHandler } from "./$types";

import coreFiles from "../../../../packages/hmr";
import testFiles from "../../../../tests/py";
import concepts from "../concepts";
import { text } from "@sveltejs/kit";

const { "README.md": readme, ...rest } = coreFiles;

function formatMarkdown(files: Record<string, string>) {
  return Object.entries(files).map(([path, text]) => `\`${path}\`\n\n\`\`\`${path.split(".").at(-1) ?? ""}\n${text.replaceAll("\r", "").trimEnd()}\n\`\`\``).join("\n\n---\n\n");
}

const corePart = `\
# Hot Module Reload for Python <https://pypi.org/project/hmr/>

${readme.replace(/.*<\/div>/s, "").trim()}

---

${concepts}

---

The \`hmr\` library doesn't have a documentation site yet, but the code is high-quality and self-explanatory.

## Core files

${formatMarkdown(rest)}
`;

const unitTestSection = `\
## Unit test files

${formatMarkdown(testFiles)}
`;

export const GET: RequestHandler = async ({ url: { searchParams } }) => {
  const content = searchParams.get("tests") ? `${corePart}\n${unitTestSection}` : corePart;
  return text(content, { headers: { "content-type": "text/markdown" } });
};
