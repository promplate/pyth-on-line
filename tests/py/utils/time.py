from asyncio import Condition, Event


class StepController:
    def __init__(self):
        self._step_condition = Condition()
        self.current_step = 0

    async def step(self):
        """Advance one time step"""
        async with self._step_condition:
            self.current_step += 1
            self._step_condition.notify_all()

    async def wait_for_step(self, step: int):
        """Wait until specified time step"""
        async with self._step_condition:
            while self.current_step < step:
                await self._step_condition.wait()


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
