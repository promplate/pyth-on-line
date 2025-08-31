from asyncio import Condition


class StepController:
    def __init__(self):
        self._step_condition = Condition()
        self.current_step = 0

    async def step(self):
        async with self._step_condition:
            self.current_step += 1
            self._step_condition.notify_all()

    async def wait_until(self, step: int):
        while self.current_step < step:
            async with self._step_condition:
                await self._step_condition.wait()
