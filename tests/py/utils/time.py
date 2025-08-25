from asyncio import Condition, Event
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


class StepController:
    def __init__(self):
        self._step_event = Event()
        self._step_condition = Condition()
        self._current_step = 0
        self._step_event.set()  # Initial state is triggered

    @property
    def current_step(self) -> int:
        return self._current_step

    async def step(self):
        """Advance one time step"""
        async with self._step_condition:
            self._current_step += 1
            self._step_event.set()
            self._step_condition.notify_all()

    async def wait_for_step(self, step: int):
        """Wait until specified time step"""
        async with self._step_condition:
            while self._current_step < step:
                await self._step_condition.wait()
            # Reset the event after waiting to prevent multiple triggers
            self._step_event.clear()

    async def wait_next_step(self):
        """Wait for the next time step"""
        current = self._current_step
        await self.wait_for_step(current + 1)

    @asynccontextmanager
    async def at_step(self, step: int) -> AsyncIterator[None]:
        """Context manager to execute at specified time step"""
        await self.wait_for_step(step)
        yield


class TimeEvent:
    def __init__(self):
        self._event = Event()
        self._triggered = False

    async def wait(self):
        """Wait for the event to be triggered"""
        await self._event.wait()

    def set(self):
        """Trigger the event"""
        if not self._triggered:
            self._triggered = True
            self._event.set()

    def clear(self):
        """Clear the event state"""
        self._triggered = False
        self._event.clear()

    def is_set(self) -> bool:
        return self._triggered
