from os import getenv

from promplate.llm.openai import AsyncChatGenerate

from .templates import explain_error


async def explain(traceback: str, code: str):
    generate = AsyncChatGenerate().bind(temperature=0, model=getenv("LLM_MODEL", "gpt-4o-mini"))

    async for i in generate(await explain_error.arender({"traceback": traceback, "code": code})):
        assert isinstance(i, str)
        yield i
