import type { RequestHandler } from "./$types";

import coreFiles from "../../../../packages/hmr";
import testFiles from "../../../../tests/py";
import concepts from "../concepts";
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

type Entry = {
  content: string;
  uri: string;
  tool: string;
  title: string;
  description: string;
  hint: string;
};

const entrypoints: Entry[] = [
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

const byTool = new Map(entrypoints.map(entry => [entry.tool, entry]));
const byUri = new Map(entrypoints.map(entry => [entry.uri, entry]));

function withCors(response: Response) {
  const headers = new Headers(response.headers);
  headers.set("Access-Control-Allow-Origin", "*");
  headers.set("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS");
  headers.set("Access-Control-Allow-Headers", "Content-Type");
  return new Response(response.body, { status: response.status, headers });
}

function json(id: unknown, result: unknown) {
  return withCors(Response.json({ jsonrpc: "2.0", id, result }));
}

function rpcError(id: unknown, code: number, message: string) {
  return withCors(Response.json({ jsonrpc: "2.0", id, error: { code, message } }));
}

function empty(status = 204) {
  return withCors(new Response(null, { status }));
}

const handler: RequestHandler = async ({ request }) => {
  if (request.method === "OPTIONS") {
    return empty();
  }

  if (request.method === "GET") {
    // Keep a tiny GET response for health checks and browser probing.
    return withCors(Response.json({ name: "hmr-docs", version: "1.0.0" }));
  }

  if (request.method !== "POST") {
    return empty(405);
  }

  const payload = await request.json().catch(() => null) as { id?: unknown; method?: string; params?: any } | null;
  if (!payload?.method) {
    return rpcError(payload?.id, -32600, "Invalid Request");
  }

  switch (payload.method) {
    case "initialize":
      return json(payload.id, {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {}, prompts: {}, resources: {} },
        serverInfo: { name: "hmr-docs", version: "1.0.0" },
      });

    case "tools/list":
      return json(payload.id, {
        tools: entrypoints.map(({ tool, description, hint }) => ({
          name: tool,
          title: tool,
          description: `${description}\n\n${hint}`,
          inputSchema: { type: "object", properties: {}, additionalProperties: false },
          annotations: { readOnlyHint: true },
        })),
      });

    case "tools/call": {
      const entry = byTool.get(payload.params?.name);
      if (!entry) {
        return rpcError(payload.id, -32602, "Unknown tool");
      }
      const resource = { uri: entry.uri, text: entry.content };
      return json(payload.id, { content: [{ type: "resource", resource }] });
    }

    case "resources/list":
      return json(payload.id, {
        resources: entrypoints.map(({ uri, title, description }) => ({
          uri,
          name: title,
          title,
          description,
          mimeType: "text/plain",
        })),
      });

    case "resources/read": {
      const entry = byUri.get(payload.params?.uri);
      if (!entry) {
        return rpcError(payload.id, -32602, "Unknown resource");
      }
      return json(payload.id, { contents: [{ uri: entry.uri, text: entry.content, mimeType: "text/plain" }] });
    }

    case "prompts/list":
      return json(payload.id, {
        prompts: entrypoints.map(({ tool, description }) => ({ name: tool, description })),
      });

    case "prompts/get": {
      const entry = byTool.get(payload.params?.name);
      if (!entry) {
        return rpcError(payload.id, -32602, "Unknown prompt");
      }
      const resource = { uri: entry.uri, text: entry.content };
      return json(payload.id, {
        description: entry.description,
        messages: [{ role: "user", content: { type: "resource", resource } }],
      });
    }

    default:
      return rpcError(payload.id, -32601, "Method not found");
  }
};

export const GET = handler;
export const POST = handler;
export const DELETE = handler;
export const OPTIONS = handler;

export const config = { runtime: "edge" };
