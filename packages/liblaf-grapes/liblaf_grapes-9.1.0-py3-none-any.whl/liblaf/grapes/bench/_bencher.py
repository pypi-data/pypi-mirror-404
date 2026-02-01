import functools
import logging
import math
import multiprocessing
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, overload

import attrs

from ._results import BenchResults

logger: logging.Logger = logging.getLogger(__name__)


def _default_setup() -> Iterable[tuple[Sequence, Mapping]]:
    yield (), {}


def _default_size_fn(*_args, **_kwargs) -> int:
    return 1


@attrs.define
class Bencher:
    min_time: float = 0.2
    timeout: float = 10.0
    warmup: int = 1
    _registry: dict[str, Callable] = attrs.field(init=False, factory=dict)
    _setup: Callable[..., Iterable[tuple[Sequence, Mapping]]] = attrs.field(
        default=_default_setup, init=False
    )
    _size_fn: Callable[..., float] = attrs.field(default=_default_size_fn, init=False)

    @overload
    def bench[C: Callable](self, func: C, /, *, label: str | None = None) -> C: ...
    @overload
    def bench[C: Callable](self, *, label: str | None = None) -> Callable[[C], C]: ...
    def bench(
        self, func: Callable | None = None, *, label: str | None = None
    ) -> Callable:
        if func is None:
            return functools.partial(self.bench, label=label)
        if label is None:
            label = func.__name__
        self._registry[label] = func
        return func

    def setup[C: Callable[..., Iterable[tuple[Sequence, Mapping]]]](self, func: C) -> C:
        self._setup = func
        return func

    def size[C: Callable[..., float]](self, func: C) -> C:
        self._size_fn = func
        return func

    def run(self) -> BenchResults:
        inputs: Sequence[tuple[Sequence, Mapping]] = list(self._setup())
        sizes_and_inputs: list[tuple[float, tuple[Sequence, Mapping]]] = [
            (self._size_fn(*args, **kwargs), (args, kwargs)) for args, kwargs in inputs
        ]
        sizes_and_inputs.sort(key=lambda x: x[0])
        sizes: Sequence[float] = [size for size, _ in sizes_and_inputs]
        inputs = [(args, kwargs) for _, (args, kwargs) in sizes_and_inputs]
        outputs: dict[str, list[Any]] = {}
        timings: dict[str, list[float]] = {}
        for label, func in self._registry.items():
            outputs_name: list[Any] = []
            timings_name: list[float] = []
            for size, (args, kwargs) in zip(sizes, inputs, strict=True):
                output: Any
                elapsed: float
                output, elapsed = self._bench(func, args, kwargs)
                outputs_name.append(output)
                timings_name.append(elapsed)
                logger.debug("Bench %s(%g) took %g sec", label, size, elapsed)
                if elapsed > self.timeout:
                    logger.warning("Bench %s(%g) timed out", label, size)
                    break
            if len(timings_name) < len(sizes):
                n_remain: int = len(sizes) - len(timings_name)
                outputs_name.extend([None] * n_remain)
                timings_name.extend([math.inf] * n_remain)
            timings[label] = timings_name
            outputs[label] = outputs_name
        return BenchResults(outputs=outputs, sizes=list(sizes), timings=timings)

    def _bench[T](
        self, func: Callable[..., T], args: Sequence, kwargs: Mapping
    ) -> tuple[T | None, float]:
        result: T | None = None
        for _ in range(self.warmup):
            result = func(*args, **kwargs)
        count: int = 0
        total_elapsed: float = 0.0
        while total_elapsed < self.min_time:
            start: float = time.perf_counter()
            result = func(*args, **kwargs)
            end: float = time.perf_counter()
            count += 1
            total_elapsed += end - start
        return result, total_elapsed / count

    def _bench_process[T](
        self, func: Callable[..., T], args: Sequence, kwargs: Mapping
    ) -> tuple[T | None, float]:
        def wrapper(
            queue: multiprocessing.Queue, *args: Sequence, **kwargs: Mapping
        ) -> None:
            result: T | None = None
            for _ in range(self.warmup):
                result = func(*args, **kwargs)
            count: int = 0
            total_elapsed: float = 0.0
            while total_elapsed < self.min_time:
                start: float = time.perf_counter()
                result = func(*args, **kwargs)
                end: float = time.perf_counter()
                count += 1
                total_elapsed += end - start
            queue.put((result, total_elapsed / count))

        queue: multiprocessing.Queue[tuple[T, float]] = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=wrapper, args=(queue, *args), kwargs=kwargs
        )
        process.start()
        process.join(self.timeout)
        if process.is_alive():
            process.kill()
            return None, math.inf
        result: T
        elapsed: float
        result, elapsed = queue.get()
        return result, elapsed
