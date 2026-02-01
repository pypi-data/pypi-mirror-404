from typing import overload

ICECREAM: int
ICON: str

class IceCreamDebugger:
    @overload
    def __call__(self, **kwargs) -> None: ...
    @overload
    def __call__[T](self, arg: T, **kwargs) -> T: ...
    @overload
    def __call__[T1, T2, *Ts](
        self, arg1: T1, arg2: T2, *args: *Ts, **kwargs
    ) -> tuple[T1, T2, *Ts]: ...

ic: IceCreamDebugger
