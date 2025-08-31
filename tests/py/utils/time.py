from asyncio import Event, Task, TaskGroup, current_task, sleep
from collections import defaultdict
from contextvars import ContextVar
from functools import partial

from reactivity.async_primitives import AsyncDerived, AsyncFunction


class Clock(TaskGroup):
    def __init__(self):
        super().__init__()
        self.tasks: list[Task] = []
        self.steps: dict[int, Event] = defaultdict(Event)
        self.now = 0
        self.used = ContextVar("used-time", default=0)

    def task_factory[T](self, func: AsyncFunction[T]):
        self.tasks.append(task := self.create_task(func()))
        return task

    @property
    def async_derived(self):
        return partial(AsyncDerived, task_factory=self.task_factory)

    # timer helpers

    async def sleep(self, duration: int):
        now = self.used.get()
        self.used.set(now + duration)
        await self.steps[now + duration].wait()

    async def wait_all_tasks_blocked(self):
        last = None
        while True:
            current = current_task()
            if last is current:
                break
            last = current

            if all(t.done() for t in self.tasks if t is not current):
                break

            # Disclaimer: I'm not sure whether this implementation is correct at all, it just works for now

            for _ in range(10):
                await sleep(0)

    async def tick(self):
        await self.wait_all_tasks_blocked()
        self.now += 1
        self.steps[self.now].set()
        await self.wait_all_tasks_blocked()

    async def fast_forward_to(self, step: int):
        while self.now < step:
            await self.tick()
