export interface McpIcon {
  mimeType: string;
  src: string;
}

export interface McpEntrypoint {
  content: string;
  uri: string;
  tool: string;
  title: string;
  description: string;
  hint: string;
}

interface JsonRpcRequest {
  jsonrpc?: string;
  id?: string | number | null;
  method?: string;
  params?: Record<string, unknown>;
}

const JSONRPC_VERSION = "2.0";
const ALLOW_METHODS = "POST, DELETE, OPTIONS";

const withCors = (response: Response) => {
  response.headers.set("Access-Control-Allow-Origin", "*");
  response.headers.set("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS");
  response.headers.set("Access-Control-Allow-Headers", "*");
  return response;
};

const toSseResponse = (payload: unknown, sessionId: string) => withCors(new Response(`event: message\ndata: ${JSON.stringify(payload)}\n\n`, {
  status: 200,
  headers: {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    connection: "keep-alive",
    "mcp-session-id": sessionId,
  },
}));

const toJsonRpcError = (id: JsonRpcRequest["id"], code: number, message: string, sessionId: string) =>
  toSseResponse({ jsonrpc: JSONRPC_VERSION, id: id ?? null, error: { code, message } }, sessionId);

export class MinimalMcpHttpServer {
  private readonly serverInfo: {
    name: string;
    version: string;
    description: string;
    websiteUrl: string;
    icons: McpIcon[];
  };

  private readonly entrypoints: readonly McpEntrypoint[];

  constructor(
    serverInfo: {
      name: string;
      version: string;
      description: string;
      websiteUrl: string;
      icons: McpIcon[];
    },
    entrypoints: readonly McpEntrypoint[],
  ) {
    this.serverInfo = serverInfo;
    this.entrypoints = entrypoints;
  }

  async respond(request: Request): Promise<Response> {
    const sessionId = request.headers.get("mcp-session-id") ?? crypto.randomUUID();

    if (request.method === "OPTIONS") {
      return withCors(new Response(null, { status: 204, headers: { "Content-Type": "application/json" } }));
    }

    if (request.method === "DELETE") {
      return withCors(new Response(null, { status: 200, headers: { "mcp-session-id": sessionId } }));
    }

    if (request.method === "GET") {
      return withCors(new Response(null, { status: 405, headers: { Allow: ALLOW_METHODS } }));
    }

    if (request.method !== "POST") {
      return withCors(new Response(JSON.stringify({ jsonrpc: JSONRPC_VERSION, error: { code: -32601, message: "Method not found" } }), {
        status: 405,
        headers: { "Content-Type": "application/json", Allow: "GET, POST, DELETE, OPTIONS" },
      }));
    }

    if (!request.headers.get("content-type")?.includes("application/json")) {
      return withCors(new Response(JSON.stringify({ jsonrpc: JSONRPC_VERSION, error: { code: -32600, message: "Invalid Request" } }), {
        status: 415,
        headers: { "Content-Type": "application/json", "mcp-session-id": sessionId },
      }));
    }

    let rpcRequest: JsonRpcRequest;
    try {
      rpcRequest = await request.json();
    }
    catch {
      return withCors(new Response(JSON.stringify({ jsonrpc: JSONRPC_VERSION, error: { code: -32700, message: "Parse error" } }), {
        status: 400,
        headers: { "Content-Type": "application/json", "mcp-session-id": sessionId },
      }));
    }

    return this.handleRpcRequest(rpcRequest, sessionId);
  }

  private handleRpcRequest(request: JsonRpcRequest, sessionId: string): Response {
    const id = request.id ?? null;

    switch (request.method) {
      case "initialize": {
        const protocolVersion = typeof request.params?.protocolVersion === "string" ? request.params.protocolVersion : "2025-03-26";
        return toSseResponse({
          jsonrpc: JSONRPC_VERSION,
          id,
          result: {
            protocolVersion,
            adapter: {},
            capabilities: {
              tools: {},
              prompts: {},
              resources: {},
            },
            serverInfo: this.serverInfo,
          },
        }, sessionId);
      }

      case "ping": {
        return toSseResponse({ jsonrpc: JSONRPC_VERSION, id, result: {} }, sessionId);
      }

      case "tools/list": {
        return toSseResponse({
          jsonrpc: JSONRPC_VERSION,
          id,
          result: {
            tools: this.entrypoints.map(entrypoint => ({
              name: entrypoint.tool,
              title: entrypoint.tool,
              description: `${entrypoint.description}\n\n${entrypoint.hint}`,
              icons: this.serverInfo.icons,
              inputSchema: {
                type: "object",
                properties: {},
              },
              annotations: {
                readOnlyHint: true,
              },
            })),
          },
        }, sessionId);
      }

      case "tools/call": {
        const name = request.params?.name;
        const entrypoint = typeof name === "string" ? this.entrypoints.find(item => item.tool === name) : undefined;
        if (!entrypoint) {
          return toJsonRpcError(id, -32602, "Invalid params", sessionId);
        }

        return toSseResponse({
          jsonrpc: JSONRPC_VERSION,
          id,
          result: {
            content: [
              {
                type: "resource",
                resource: {
                  uri: entrypoint.uri,
                  text: entrypoint.content,
                },
              },
            ],
          },
        }, sessionId);
      }

      case "resources/list": {
        return toSseResponse({
          jsonrpc: JSONRPC_VERSION,
          id,
          result: {
            resources: this.entrypoints.map(entrypoint => ({
              name: entrypoint.title,
              title: entrypoint.title,
              description: entrypoint.description,
              uri: entrypoint.uri,
              icons: this.serverInfo.icons,
            })),
          },
        }, sessionId);
      }

      case "resources/read": {
        const uri = request.params?.uri;
        const entrypoint = typeof uri === "string" ? this.entrypoints.find(item => item.uri === uri) : undefined;
        if (!entrypoint) {
          return toJsonRpcError(id, -32602, "Invalid params", sessionId);
        }

        return toSseResponse({
          jsonrpc: JSONRPC_VERSION,
          id,
          result: {
            contents: [
              {
                uri: entrypoint.uri,
                text: entrypoint.content,
              },
            ],
          },
        }, sessionId);
      }

      case "prompts/list": {
        return toSseResponse({
          jsonrpc: JSONRPC_VERSION,
          id,
          result: {
            prompts: this.entrypoints.map(entrypoint => ({
              name: entrypoint.tool,
              title: entrypoint.description,
              icons: this.serverInfo.icons,
              description: entrypoint.description,
              arguments: [],
            })),
          },
        }, sessionId);
      }

      case "prompts/get": {
        const name = request.params?.name;
        const entrypoint = typeof name === "string" ? this.entrypoints.find(item => item.tool === name) : undefined;
        if (!entrypoint) {
          return toJsonRpcError(id, -32602, "Invalid params", sessionId);
        }

        const resource = { uri: entrypoint.uri, text: entrypoint.content };
        return toSseResponse({
          jsonrpc: JSONRPC_VERSION,
          id,
          result: {
            description: entrypoint.description,
            messages: [{ role: "user", content: { type: "resource", resource } }],
          },
        }, sessionId);
      }

      default:
        return toJsonRpcError(id, -32601, "Method not found", sessionId);
    }
  }
}
