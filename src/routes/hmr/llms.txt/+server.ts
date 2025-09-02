import type { RequestHandler } from "./$types";

import coreFiles from "../../../../packages/hmr";
import concepts from "../concepts";
import { text } from "@sveltejs/kit";

const content = `\
# Hot Module Reload for Python (https://pypi.org/project/hmr/)

${coreFiles["README.md"].replace(/.*<\/div>/s, "").trim()}

---

${concepts}

---

The \`hmr\` library doesn't have a documentation site yet, but the code is high-quality and self-explanatory.

## Core files

${Object.entries(coreFiles).map(([path, text]) => `\`${path}\`\n\n\`\`\`${path.split(".").at(-1) ?? ""}\n${text.replaceAll("\r", "").trimEnd()}\n\`\`\``).join("\n\n---\n\n")}
`;

export const GET: RequestHandler = async () => {
  return text(content, { headers: { "content-type": "text/markdown" } });
};

export const prerender = true;
