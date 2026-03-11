import type { EntryGenerator, RequestHandler } from "./$types";

import coreFiles from "../../../../../packages/hmr";
import testFiles from "../../../../../tests/py";
import concepts from "../../../concepts";
import { json } from "@sveltejs/kit";
import { packXML } from "$lib/utils/pack";

const docs = `\
# Hot Module Reload for Python (https://pypi.org/project/hmr/)

${coreFiles["README.md"].replace(/.*<\/div>/s, "").trim()}

---

${concepts}

---

The \`hmr\` library doesn't have a documentation site yet, but the code is high-quality and self-explanatory.
Now you should read the source code (using the other two MCP tools) for more information on how to use it.
`;

const contents = {
  "about": docs,
  "core-files": `# Files under <https://github.com/promplate/pyth-on-line/packages/hmr>:\n\n${packXML(coreFiles)}`,
  "test-files": `# Files under <https://github.com/promplate/pyth-on-line/tests/py>:\n\n${packXML(testFiles)}`,
} as const;

export const GET: RequestHandler = ({ params: { kind } }) => {
  const content = contents[kind as keyof typeof contents];

  if (!content) {
    return new Response("Not Found", { status: 404 });
  }

  return json({ content });
};

export const prerender = true;

export const entries: EntryGenerator = () => {
  return Object.keys(contents).map(kind => ({ kind }));
};
