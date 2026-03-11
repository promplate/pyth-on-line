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
] as const;

const icons = [{ mimeType: "image/webp", src: "data:image/webp;base64,UklGRkoAAABXRUJQVlA4TD0AAAAvj8AjEBcgEEjypxlnNAVpGzDd8694IBBIktp22PkP8NsGQg0MJZWU86YAj4j+T4B+ceplERrXhF1vygEGAA==" }];

const resources = entrypoints.map(({ content, title, description, uri }) => ({
  name: title,
  title,
  description,
  uri,
  icons,
  content: { text: content, uri },
}));

const tools = entrypoints.map(({ tool, description, hint, uri }) => ({
  name: tool,
  title: tool,
  description: `${description}\n\n${hint}`,
  icons,
  inputSchema: { type: "object", properties: {} },
  annotations: { readOnlyHint: true },
  resource: resources.find(item => item.uri === uri)!.content,
}));

const prompts = entrypoints.map(({ tool, description, uri }) => ({
  name: tool,
  description,
  icons,
  resource: resources.find(item => item.uri === uri)!.content,
}));

const sessions = new Set<string>();

const CORS_HEADERS = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "*",
  "access-control-allow-methods": "GET, POST, DELETE, OPTIONS",
};

function jsonRpc(id: unknown, result?: unknown, error?: { code: number; message: string }) {
  return { jsonrpc: "2.0", id, ...(error ? { error } : { result }) };
}

function toResponse(payload: unknown, sessionId?: string, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      ...CORS_HEADERS,
      "content-type": "application/json",
      ...(sessionId ? { "mcp-session-id": sessionId } : {}),
    },
  });
}

function getSessionId(request: Request) {
  return request.headers.get("mcp-session-id") ?? undefined;
}

export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json().catch(() => null);

  if (!body || typeof body !== "object") {
    return toResponse(jsonRpc(null, undefined, { code: -32700, message: "Parse error" }), undefined, 400);
  }

  const { id, method, params } = body as { id?: unknown; method?: string; params?: Record<string, unknown> };

  if (!method) {
    return toResponse(jsonRpc(id ?? null, undefined, { code: -32600, message: "Invalid Request" }), undefined, 400);
  }

  if (method === "initialize") {
    const sessionId = crypto.randomUUID();
    sessions.add(sessionId);
    return toResponse(jsonRpc(id ?? null, {
      protocolVersion: "2024-11-05",
      adapter: {},
      capabilities: { tools: {}, prompts: {}, resources: {} },
      serverInfo: {
        name: "hmr-docs",
        version: "1.0.0",
        description: "Docs for the HMR library for Python (python modules `reactivity` and `reactivity.hmr`).",
        websiteUrl: "https://github.com/promplate/hmr",
        icons,
      },
    }), sessionId);
  }

  const sessionId = getSessionId(request);
  if (!sessionId || !sessions.has(sessionId)) {
    return toResponse(jsonRpc(id ?? null, undefined, { code: -32001, message: "Session not found" }), undefined, 400);
  }

  if (id === undefined) {
    // Notifications are acknowledged with no body.
    return new Response(null, { status: 202, headers: { ...CORS_HEADERS, "mcp-session-id": sessionId } });
  }

  switch (method) {
    case "ping":
      return toResponse(jsonRpc(id, {}), sessionId);
    case "tools/list":
      return toResponse(jsonRpc(id, { tools: tools.map(({ resource: _resource, ...tool }) => tool) }), sessionId);
    case "tools/call": {
      const toolName = typeof params?.name === "string" ? params.name : "";
      const tool = tools.find(item => item.name === toolName);
      if (!tool)
        return toResponse(jsonRpc(id, undefined, { code: -32602, message: `Unknown tool: ${toolName}` }), sessionId, 400);
      return toResponse(jsonRpc(id, { content: [{ type: "resource", resource: tool.resource }] }), sessionId);
    }
    case "resources/list":
      return toResponse(jsonRpc(id, { resources: resources.map(({ content: _content, ...resource }) => resource) }), sessionId);
    case "resources/read": {
      const uri = typeof params?.uri === "string" ? params.uri : "";
      const resource = resources.find(item => item.uri === uri)?.content;
      if (!resource)
        return toResponse(jsonRpc(id, undefined, { code: -32602, message: `Unknown resource: ${uri}` }), sessionId, 400);
      return toResponse(jsonRpc(id, { contents: [resource] }), sessionId);
    }
    case "prompts/list":
      return toResponse(jsonRpc(id, { prompts: prompts.map(({ resource: _resource, ...prompt }) => prompt) }), sessionId);
    case "prompts/get": {
      const promptName = typeof params?.name === "string" ? params.name : "";
      const prompt = prompts.find(item => item.name === promptName);
      if (!prompt)
        return toResponse(jsonRpc(id, undefined, { code: -32602, message: `Unknown prompt: ${promptName}` }), sessionId, 400);
      return toResponse(jsonRpc(id, { description: prompt.description, messages: [{ role: "user", content: { type: "resource", resource: prompt.resource } }] }), sessionId);
    }
    default:
      return toResponse(jsonRpc(id, undefined, { code: -32601, message: `Method not found: ${method}` }), sessionId, 404);
  }
};

export const GET: RequestHandler = async () => {
  return new Response(null, {
    status: 405,
    headers: {
      ...CORS_HEADERS,
      allow: "POST, DELETE, OPTIONS",
      vary: "Accept",
    },
  });
};

export const DELETE: RequestHandler = async ({ request }) => {
  const sessionId = getSessionId(request);
  if (sessionId)
    sessions.delete(sessionId);

  return new Response(null, {
    status: 204,
    headers: {
      ...CORS_HEADERS,
    },
  });
};

export const OPTIONS: RequestHandler = async () => {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
};

export const config = { runtime: "edge" };
