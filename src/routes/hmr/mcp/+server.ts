import type { RequestHandler } from "./$types";

import coreFiles from "../../../../packages/hmr";
import testFiles from "../../../../tests/py";
import concepts from "../concepts";
import { createMcpHandler } from "mcp-handler";
import { z } from "zod";

function pack(files: Record<string, string>) {
  return Object.entries(files).map(([path, content]) => `<file path="${path}">\n${content.replaceAll("\r", "").trimEnd()}\n</file>`).join("\n\n");
}

const docs = `\
# Hot Module Reload for Python (https://pypi.org/project/hmr/)

${coreFiles["README.md"].replace(/.*<\/div>/s, "").trim()}

---

${concepts}

---

The \`hmr\` library doesn't have a documentation site yet, but the code is high-quality and self-explanatory.
Now you should call the \`view-hmr-sources\` MCP tool to get the source code for more information on how to use it.
`;

const handler = createMcpHandler((server) => {
  server.tool(
    "view-hmr-sources",
    "Get the source code of the `hmr` library, which would be very helpful because good code are self-documented.\nFor a brief and concise explanation, please refer to the `hmr-docs://about` MCP resource. Make sure you've read it before calling this tool.",
    { includeUnitTests: z.boolean().optional().default(false) },
    { readOnlyHint: true },
    ({ includeUnitTests }) => {
      return { content: [{ type: "text", text: pack({ ...coreFiles, ...includeUnitTests && testFiles }) }] };
    },
  );
  server.resource("About HMR", "hmr-docs://about", { description: "A brief and concise of the HMR library. You must read this first to understand how to use reactive programming or use hot module reloading in Python." }, () => {
    return { contents: [{ text: docs, uri: "https://github.com/promplate/pyth-on-line/tree/main/packages/hmr" }] };
  });
}, {}, { basePath: "/hmr", verboseLogs: true });

export const GET: RequestHandler = async ({ request }) => handler(request);
export const POST: RequestHandler = async ({ request }) => handler(request);
export const DELETE: RequestHandler = async ({ request }) => handler(request);
