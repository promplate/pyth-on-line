import type { RequestHandler } from "./$types";
import type { JSONSchema7 } from "json-schema";

import coreFiles from "../../../../packages/hmr";
import testFiles from "../../../../tests/py";
import concepts from "../concepts";
import { HttpTransport } from "@tmcp/transport-http";
import { packXML } from "$lib/utils/pack";
import { McpServer } from "tmcp";

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

// a minimal icon using python's color scheme
const icons = [{ mimeType: "image/webp", src: "data:image/webp;base64,UklGRkoAAABXRUJQVlA4TD0AAAAvj8AjEBcgEEjypxlnNAVpGzDd8694IBBIktp22PkP8NsGQg0MJZWU86YAj4j+T4B+ceplERrXhF1vygEGAA==" }];

const server = new McpServer(
  {
    name: "hmr-docs",
    version: "1.0.0",
    description: "Docs for the HMR library for Python (python modules `reactivity` and `reactivity.hmr`).",
    websiteUrl: "https://github.com/promplate/hmr",
    icons,
  },
  {
    adapter: {
      async toJsonSchema() {
        return {} as JSONSchema7; // minimal adapter since we don't use any schemas
      },
    },
    capabilities: {
      tools: {},
      prompts: {},
      resources: {},
    },
  },
);

for (const { content, uri, tool, title, description, hint } of entrypoints) {
  const resource = { text: content, uri };
  server.tool({ name: tool, title: tool, description: `${description}\n\n${hint}`, annotations: { readOnlyHint: true }, icons }, () => ({ content: [{ type: "resource", resource }] }));
  server.resource({ name: title, title, description, uri, icons }, () => ({ contents: [resource] }));
  server.prompt({ name: tool, description, icons }, () => ({ description, messages: [{ role: "user", content: { type: "resource", resource } }] }));
}

const transport = new HttpTransport(server, {
  path: "/hmr/mcp",
  cors: true,
});

const handler: RequestHandler = async ({ request }) => {
  const response = await transport.respond(request);
  return response ?? new Response("Not Found", { status: 404 });
};

export const GET = handler;
export const POST = handler;
export const DELETE = handler;
export const OPTIONS = handler;
