type JsonRpcId = string | number;

type JsonRpcRequest = {
  jsonrpc: "2.0";
  id?: JsonRpcId;
  method: string;
  params?: Record<string, unknown>;
};

type EntryPoint = {
  content: string;
  uri: string;
  tool: string;
  title: string;
  description: string;
  hint: string;
};

type HandlerResult =
  | { value: unknown }
  | { error: { code: number; message: string } };

const MCP_PROTOCOL_VERSION = "2025-03-26";

const json = (body: unknown, status = 200, headers?: HeadersInit) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json",
      "access-control-allow-origin": "*",
      "access-control-allow-headers": "*",
      "access-control-allow-methods": "GET, POST, DELETE, OPTIONS",
      ...headers,
    },
  });

const jsonRpcResult = (id: JsonRpcId, result: unknown) => ({ jsonrpc: "2.0", id, result });

const jsonRpcError = (id: JsonRpcId | null, code: number, message: string) => ({
  jsonrpc: "2.0",
  id,
  error: { code, message },
});

export class MinimalMcpHttpServer {
  constructor(
    private readonly entrypoints: EntryPoint[],
    private readonly serverInfo: {
      name: string;
      version: string;
      description: string;
      websiteUrl: string;
      icons: Array<{ mimeType: string; src: string }>;
    },
  ) {}

  async respond(request: Request) {
    if (request.method === "OPTIONS") {
      return json({}, 204);
    }

    if (request.method !== "POST") {
      return new Response("Not Found", { status: 404 });
    }

    let payload: JsonRpcRequest;
    try {
      payload = await request.json();
    }
    catch {
      return json(jsonRpcError(null, -32700, "Parse error"), 400);
    }

    if (payload.jsonrpc !== "2.0" || !payload.method) {
      return json(jsonRpcError(payload.id ?? null, -32600, "Invalid Request"), 400);
    }

    if (payload.id === undefined) {
      // Notifications do not require responses.
      return new Response(null, {
        status: 202,
        headers: {
          "access-control-allow-origin": "*",
          "access-control-allow-headers": "*",
          "access-control-allow-methods": "GET, POST, DELETE, OPTIONS",
        },
      });
    }

    const result = this.handle(payload.method, payload.params ?? {});
    if ("error" in result) {
      return json(jsonRpcError(payload.id, result.error.code, result.error.message), 400);
    }

    return json(jsonRpcResult(payload.id, result.value));
  }

  private handle(method: string, params: Record<string, unknown>): HandlerResult {
    switch (method) {
      case "initialize":
        return {
          value: {
            protocolVersion: MCP_PROTOCOL_VERSION,
            capabilities: { tools: {}, prompts: {}, resources: {} },
            serverInfo: this.serverInfo,
          },
        };

      case "ping":
        return { value: {} };

      case "tools/list":
        return {
          value: {
            tools: this.entrypoints.map(({ tool, description, hint }) => ({
              name: tool,
              title: tool,
              description: `${description}\n\n${hint}`,
              inputSchema: { type: "object", properties: {} },
              annotations: { readOnlyHint: true },
              icons: this.serverInfo.icons,
            })),
          },
        };

      case "tools/call": {
        const name = params.name;
        if (typeof name !== "string") {
          return { error: { code: -32602, message: "Invalid params: name is required" } };
        }

        const entry = this.entrypoints.find(item => item.tool === name);
        if (!entry) {
          return { error: { code: -32602, message: `Unknown tool: ${name}` } };
        }

        const resource = { uri: entry.uri, text: entry.content };
        return { value: { content: [{ type: "resource", resource }] } };
      }

      case "resources/list":
        return {
          value: {
            resources: this.entrypoints.map(({ uri, title, description }) => ({
              name: title,
              title,
              description,
              uri,
              icons: this.serverInfo.icons,
            })),
          },
        };

      case "resources/read": {
        const uri = params.uri;
        if (typeof uri !== "string") {
          return { error: { code: -32602, message: "Invalid params: uri is required" } };
        }

        const entry = this.entrypoints.find(item => item.uri === uri);
        if (!entry) {
          return { error: { code: -32602, message: `Unknown resource: ${uri}` } };
        }

        return { value: { contents: [{ uri: entry.uri, text: entry.content }] } };
      }

      case "prompts/list":
        return {
          value: {
            prompts: this.entrypoints.map(({ tool, description }) => ({
              name: tool,
              description,
              icons: this.serverInfo.icons,
            })),
          },
        };

      case "prompts/get": {
        const name = params.name;
        if (typeof name !== "string") {
          return { error: { code: -32602, message: "Invalid params: name is required" } };
        }

        const entry = this.entrypoints.find(item => item.tool === name);
        if (!entry) {
          return { error: { code: -32602, message: `Unknown prompt: ${name}` } };
        }

        const resource = { uri: entry.uri, text: entry.content };
        return {
          value: {
            description: entry.description,
            messages: [{ role: "user", content: { type: "resource", resource } }],
          },
        };
      }

      default:
        return { error: { code: -32601, message: `Method not found: ${method}` } };
    }
  }
}
