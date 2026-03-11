import type { EntryGenerator, RequestHandler } from "./$types";

import coreFiles from "../../../../../../packages/hmr";
import testFiles from "../../../../../../tests/py";
import concepts from "../../../concepts";
import { error, text } from "@sveltejs/kit";
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
  about: docs,
  "core-files": `# Files under <https://github.com/promplate/pyth-on-line/packages/hmr>:\n\n${packXML(coreFiles)}`,
  "test-files": `# Files under <https://github.com/promplate/pyth-on-line/tests/py>:\n\n${packXML(testFiles)}`,
} as const;

const headers = { "content-type": "text/plain; charset=utf-8" };

export const GET: RequestHandler = ({ params: { name } }) => {
  if (!(name in contents)) {
    error(404, "Not Found");
  }

  return text(contents[name as keyof typeof contents], { headers });
};

export const prerender = true;

export const entries: EntryGenerator = () => {
  return Object.keys(contents).map(name => ({ name }));
};
