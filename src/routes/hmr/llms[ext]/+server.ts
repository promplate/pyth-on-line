import type { EntryGenerator, RequestHandler } from "./$types";

import coreFiles from "../../../../packages/hmr";
import testFiles from "../../../../tests/py";
import concepts from "../concepts";
import { redirect, text } from "@sveltejs/kit";
import { packMarkdown, packXML } from "$lib/utils/pack";

const { "README.md": readme, ...rest } = coreFiles;

const overview = `\
# Hot Module Reload for Python <https://pypi.org/project/hmr/>

${readme.replace(/.*<\/div>/s, "").trim()}

---

${concepts}

---

The \`hmr\` library doesn't have a documentation site yet, but the code is high-quality and self-explanatory.
`;

const coreFilesMarkdown = `\

---

## Core files

${packMarkdown(rest)}
`;

const testFilesMarkdown = `\

---

## Unit test files

${packMarkdown(testFiles)}
`;

export const GET: RequestHandler = ({ params: { ext = "" } }) => {
  switch (ext) {
    case ".txt":
    case ".md":
      return text(overview + coreFilesMarkdown, { headers: { "content-type": "text/markdown" } });
    case "-full.txt":
    case "-full.md":
      return text(overview + coreFilesMarkdown + testFilesMarkdown, { headers: { "content-type": "text/markdown" } });
    case ".xml":
      return text(`<overview>\n${overview}</overview>\n\n<files description="core files">\n${packXML(rest)}\n</files>\n`, { headers: { "content-type": "application/xml" } });
    case "-full.xml":
      return text(`<overview>\n${overview}</overview>\n\n<files description="core files">\n${packXML(rest)}\n</files>\n\n<files description="unit test files">\n${packXML(testFiles)}\n</files>\n`, { headers: { "content-type": "application/xml" } });
    default:
      redirect(308, "/hmr/llms.txt");
  }
};

export const prerender = true;

export const entries: EntryGenerator = () => {
  return [".md", ".txt", ".xml", "-full.md", "-full.txt", "-full.xml"].map(ext => ({ ext }));
};
