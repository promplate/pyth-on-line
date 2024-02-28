import type { ClientOptions } from "openai";
import type { ChatCompletionCreateParams, CompletionCreateParams } from "openai/src/resources/index.js";
import type { PyCallable, PyProxy } from "pyodide/ffi";

import { getPy } from "./init";
import { toJs, toPyOptions } from "./translate";

export type ChatCompletionParams = Omit<ChatCompletionCreateParams, "messages" | "stream">;
export type TextCompletionParams = Omit<CompletionCreateParams, "prompt" | "stream">;
export type Role = "system" | "user" | "assistant";
export interface Message { role: Role; content: string; name?: string }

export default async () => {
  const py = await getPy();

  class Template {
    proxy: PyProxy;

    constructor(text: string);
    constructor(input: string | PyProxy) {
      if (typeof input === "string")
        this.proxy = py.runPython(`Template(${JSON.stringify(input)})`);
      else
        this.proxy = input;
    }

    static fetch(url: string | URL) {
      return new Template(py.runPython(`Template.fetch(${JSON.stringify(String(url))})`));
    }

    static async afetch(url: string | URL) {
      return new Template(py.runPython(`await Template.afetch(${JSON.stringify(String(url))})`));
    }

    render(context?: Record<string, unknown> | Map<string, unknown>) {
      return this.proxy.render(context && py.toPy(context)) as string;
    }

    async arender(context?: Record<string, unknown> | Map<string, unknown>) {
      return (await this.proxy.arender(context && py.toPy(context))) as string;
    }
  }

  return {
    Template,
    Node: py.runPython("Node"),
    AsyncChatGenerate(clientOptions: ClientOptions) {
      return async function* (input: string, options?: ChatCompletionParams) {
        const generate: PyCallable = (py.runPython("AsyncChatGenerate") as PyCallable).callKwargs(await toPyOptions(clientOptions));
        yield * generate.callKwargs(input, { ...options });
        generate.destroy();
      };
    },
    AsyncTextGenerate(clientOptions: ClientOptions) {
      return async function* (input: string, options?: TextCompletionParams) {
        const generate: PyCallable = (py.runPython("AsyncTextGenerate") as PyCallable).callKwargs(await toPyOptions(clientOptions));
        yield * generate.callKwargs(input, { ...options });
        generate.destroy();
      };
    },
    parse_chat_markup(text: string) {
      return toJs(py.runPython("parse_chat_markup")(text)) as Message[];
    },
    promplate: py.pyimport("promplate"),
  };
};
