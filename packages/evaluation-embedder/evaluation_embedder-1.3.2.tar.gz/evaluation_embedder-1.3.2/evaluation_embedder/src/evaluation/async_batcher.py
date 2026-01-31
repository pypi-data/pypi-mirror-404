import asyncio
import time
from typing import Awaitable, Callable, Generic, List, Tuple

from evaluation_embedder.src.constants import InputT, OutputT


class AsyncBatcher(Generic[InputT, OutputT]):

    def __init__(
        self,
        *,
        batch_fn: Callable[[List[InputT]], Awaitable[List[OutputT]]],
        max_batch_size: int,
        batch_timeout_ms: float,
    ) -> None:
        self._batch_fn = batch_fn
        self._max_batch_size = max_batch_size
        self._batch_timeout_ms = batch_timeout_ms

        self._queue: asyncio.Queue[Tuple[InputT, asyncio.Future[OutputT]]] = asyncio.Queue()
        self._task: asyncio.Task | None = None

    # ---------------- internals ----------------

    def _ensure_worker(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._worker())

    async def _worker(self) -> None:
        while True:
            batch: list[Tuple[InputT, asyncio.Future[OutputT]]] = []
            start = time.monotonic()

            while len(batch) < self._max_batch_size:
                timeout = self._batch_timeout_ms / 1000 - (time.monotonic() - start)
                if timeout <= 0:
                    break
                try:
                    item = await asyncio.wait_for(self._queue.get(), timeout)
                    batch.append(item)
                except asyncio.TimeoutError:
                    break

            if not batch:
                continue

            inputs = [x for x, _ in batch]
            futures = [f for _, f in batch]

            try:
                outputs = await self._batch_fn(inputs)
                if len(outputs) != len(futures):
                    raise RuntimeError("Batch function returned wrong size")

                for fut, out in zip(futures, outputs):
                    fut.set_result(out)

            except Exception as e:
                for fut in futures:
                    fut.set_exception(e)

    # ---------------- public API ----------------

    async def submit(self, inputs: List[InputT]) -> List[OutputT]:
        self._ensure_worker()

        loop = asyncio.get_running_loop()
        futures: list[asyncio.Future[OutputT]] = []

        for inp in inputs:
            fut = loop.create_future()
            await self._queue.put((inp, fut))
            futures.append(fut)

        return await asyncio.gather(*futures)

    async def submit_one(self, inp: InputT) -> OutputT:
        return (await self.submit([inp]))[0]
