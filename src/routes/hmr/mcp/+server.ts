import type { RequestHandler } from "./$types";

import coreFiles from "../../../../packages/hmr";
import testFiles from "../../../../tests/py";
import concepts from "../concepts";
import { packXML } from "$lib/utils/pack";
import { createMcpHandler } from "mcp-handler";

const docs = `\
# Hot Module Reload for Python (https://pypi.org/project/hmr/)

${coreFiles["README.md"].replace(/.*<\/div>/s, "").trim()}

---

${concepts}

---

The \`hmr\` library doesn't have a documentation site yet, but the code is high-quality and self-explanatory.
Now you should read the source code (using the other two MCP tools) for more information on how to use it.
`;

const entrypoints = [
  {
    content: docs,
    uri: "hmr-docs://about",
    tool: "learn-hmr-basics",
    title: "About HMR",
    description: "A brief and concise explanation of the `hmr` library.",
    hint: [
      "This tool provides information on how to use reactive programming or use hot module reloading in Python.",
      "As long as the user mentions HMR / Reactive Programming, this tool must be called first!",
      "Don't manually view the resource, call this tool instead.",
    ].join(" "),
  },
  {
    content: `# Files under <https://github.com/promplate/pyth-on-line/packages/hmr>:\n\n${packXML(coreFiles)}`,
    uri: "hmr-docs://core-files",
    tool: "view-hmr-core-sources",
    title: "HMR Sources",
    description: "The full source code (core only) of the HMR library.",
    hint: [
      "Always call `learn-hmr-concepts` to learn the core concepts before calling this tool.",
      "These files are the full source code of the HMR library, which would be very helpful because good code are self-documented.",
      "For a brief and concise explanation, please refer to the `hmr-docs://about` MCP resource. Make sure you've read it before calling this tool.",
      "To learn how to use HMR for reactive programming, read the unit tests later.",
      "The response is identical to the MCP resource with the same name. Only use it once and prefer this tool to that resource if you can choose.",
    ].join(" "),
  },
  {
    content: `# Files under <https://github.com/promplate/pyth-on-line/tests/py>:\n\n${packXML(testFiles)}`,
    uri: "hmr-docs://test-files",
    tool: "view-hmr-unit-tests",
    title: "HMR Unit Tests",
    description: "The unit tests (code examples) for HMR.",
    hint: [
      "Always call `learn-hmr-basics` and `view-hmr-core-sources` to learn the core functionality before calling this tool.",
      "These files are the unit tests for the HMR library, which demonstrate the best practices and common coding patterns of using the library.",
      "You should use this tool when you need to write some code using the HMR library (maybe for reactive programming or implementing some integration).",
      "The response is identical to the MCP resource with the same name. Only use it once and prefer this tool to that resource if you can choose.",
    ].join(" "),
  },
];

const handler = createMcpHandler((server) => {
  for (const { content, uri, tool, title, description, hint } of entrypoints) {
    const resource = { text: content, uri };
    server.tool(tool, `${description}\n\n${hint}`, { readonlyHint: true }, () => ({ content: [{ type: "resource", resource }] }));
    server.resource(title, uri, { description }, () => ({ contents: [resource] }));
    server.prompt(tool, () => ({ description, messages: [{ role: "user", content: { type: "resource", resource } }] }));
  }
}, {}, { basePath: "/hmr", verboseLogs: true });

export const POST: RequestHandler = async ({ request }) => handler(request);

export const GET: RequestHandler = async ({ request, fetch }) => {
  request.headers.set("Accept", "text/html");
  return await fetch(request);
};
