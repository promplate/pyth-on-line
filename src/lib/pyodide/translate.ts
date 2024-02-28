import type * as Core from "openai/core";
import type { PyProxy } from "pyodide/ffi";

import { env } from "$env/dynamic/public";
import { type ClientOptions, OpenAI } from "openai";

interface PyClientOptions {
  api_key?: string;
  base_url?: string;
  organization?: string;
  timeout?: number;
  max_retries?: number;
  defaultHeaders?: PyProxy;
  defaultQuery?: PyProxy;
}

export function toJs(obj: PyProxy) {
  return obj.toJs({ dict_converter: Object.fromEntries });
}

export async function toPyOptions(options: ClientOptions) {
  const { getPy: initPy } = await import("./init");

  const py = await initPy();

  return {
    api_key: options.apiKey,
    base_url: options.baseURL,
    organization: options.organization,
    timeout: options.timeout,
    max_retries: py.toPy(options.maxRetries),
    defaultHeaders: py.toPy(options.defaultHeaders),
    http_client: null,
  } as PyClientOptions;
}

export function toJsOptions(options: PyClientOptions) {
  return {
    baseURL: options.base_url ?? env.PUBLIC_OPENAI_BASE_URL,
    apiKey: options.api_key ?? env.PUBLIC_OPENAI_API_KEY ?? "",
    organization: options.organization,
    timeout: options.timeout,
    maxRetries: options.max_retries,
    defaultQuery: options.defaultQuery?.toJs() as Core.DefaultQuery,
    defaultHeaders: options.defaultHeaders?.toJs() as Core.Headers,
    dangerouslyAllowBrowser: true,
  } as ClientOptions;
}

export function AsyncClient(options: PyClientOptions) {
  return new OpenAI(toJsOptions(options));
}

export function toAsync(source: string) {
  return source
    .replaceAll(/(\S+|\(.*\))\.invoke/g, "await $1.ainvoke")
    .replaceAll("ChatComplete", "AsyncChatComplete")
    .replaceAll("complete(", "await complete(")
    .replaceAll(/for (\w+) in generate/g, "async for $1 in generate");
}

export function patchSource(source: string) {
  const shouldStrip = source.includes(">>> ");

  return (
    shouldStrip
      ? source.split("\n").filter(line => line.startsWith(">>>") || line.startsWith("...")).map(line => toAsync(line.slice(4)))
      : source.split("\n").map(toAsync)
  ).join("\n");
}

export function reformatInputSource(source: string) {
  return source.split("\n").map((value, index) => (index ? "... " : ">>> ") + value).join("\n");
}
