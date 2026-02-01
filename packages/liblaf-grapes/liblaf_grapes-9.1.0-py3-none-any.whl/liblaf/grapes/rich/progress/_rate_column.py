from rich.console import RenderableType
from rich.progress import ProgressColumn, Task
from rich.table import Column
from rich.text import Text

from liblaf.grapes import pretty


class RateColumn(ProgressColumn):
    unit: str = "it"

    def __init__(self, unit: str = "it", table_column: Column | None = None) -> None:
        super().__init__(table_column)
        self.unit = unit

    def render(self, task: Task) -> RenderableType:
        if not task.speed:
            return Text(f"?{self.unit}/s", style="progress.data.speed")
        throughput: str = pretty.pretty_throughput(task.speed, self.unit)
        return Text(throughput, style="progress.data.speed")
