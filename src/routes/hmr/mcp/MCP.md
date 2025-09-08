# HMR Docs MCP Server

> Access our documentation through the Model Context Protocol.

A [Model Context Protocol (MCP) server](https://modelcontextprotocol.io/docs/learn/architecture#concepts-of-mcp) implementation that provides documentation for reactive programming and hot reloading in python.

## Features

- Fetch guides and examples of reactive programming and hot reloading
- Read detailed conceptual explanations and architecture overview
- Retrieve complete HMR library source code
- Get docs for integration libraries (like uvicorn) (coming soon)
- Ask our built-in AI assistant for help with HMR concepts and usage (coming soon)

---

## Installation

We only support the [Streamable HTTP](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#streamable-http) protocol, which is the latest and recommended way. The MCP server endpoint is:

```sh
{HOST}/hmr/mcp
```

In most MCP clients, your configuration will look like this:

```json
{
  "mcpServers": {
    "hmr-docs": {
      "type": "http",
      "url": "{HOST}/hmr/mcp"
    }
  }
}
```

You can also use the [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) CLI to proxy the connection:

```sh
npx mcp-remote {HOST}/hmr/mcp
```

The config file would like this:

```json
{
  "mcpServers": {
    "hmr-docs": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "mcp-remote",
        "{HOST}/hmr/mcp"
      ]
    }
  }
}
```

---

### Application specific shortcuts

For convenience, here are some shortcuts for popular MCP clients.

#### Cursor

Directly use the remote server [![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=hmr-docs&config={cursor-http} "Open in Cursor") or use the stdio proxy [![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=hmr-docs&config={cursor-stdio} "Open in Cursor").

#### Claude Code

```sh
claude mcp add --transport http hmr-docs {HOST}/hmr/mcp
```

or

```sh
claude mcp add --transport stdio hmr-docs npx mcp-remote {HOST}/hmr/mcp
```

#### VS Code (GitHub Copilot)

Direct links: [Install the remote server](vscode:mcp/install?{vscode-http}) or [Install the stdio proxy](vscode:mcp/install?{vscode-stdio}).

---

### Available tools

> Under construction...

---

## Troubleshooting

- Test the endpoint directly: `curl {HOST}/hmr/mcp`
- Verify the config matches the expected schema (each client may have slightly different config flavors)
