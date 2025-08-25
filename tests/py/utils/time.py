from asyncio import Condition


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
