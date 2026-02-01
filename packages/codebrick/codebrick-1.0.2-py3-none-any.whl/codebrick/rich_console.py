# coding: utf-8

from rich.console import Console
from rich.table import Table
from typing import Dict, List, Iterable
from rich.style import Style, StyleType
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, track, ProgressType
import json
from contextlib import contextmanager


class RichPlain:
    def __init__(self, console: Console = None):
        self.console = console or Console()

    def print(self, data: any, color: StyleType = "green bold"):
        self.console.print(data, style=color)

    def print_red(self, data: any):
        self.console.print(data, style="red")

    def print_green(self, data: any):
        self.console.print(data, style="green")

    def print_yellow(self, data: any):
        self.console.print(data, style="yellow")

    def print_blue(self, data: any):
        self.console.print(data, style="blue")


class RichPanel:
    def __init__(self, console: Console = None):
        self.console = console or Console()

    def print(self, data: dict, title: str = None, color: StyleType = "green bold", **kwargs):
        try:
            data_str = json.dumps(data, indent=4)
        except:
            data_str = str(data)
        panel = Panel(data_str, title=title, style=color, **kwargs)
        self.console.print(panel)

    def print_red(self, data: dict, title: str = None, **kwargs):
        self.print(data, title=title, color="red bold",
                   justify="center", **kwargs)

    def print_green(self, data: dict, title: str = None, **kwargs):
        self.print(data, title=title, color="green bold", **kwargs)

    def print_yellow(self, data: dict, title: str = None, **kwargs):
        self.print(data, title=title, color="yellow bold", **kwargs)

    def print_blue(self, data: dict, title: str = None, **kwargs):
        self.print(data, title=title, color="blue bold", **kwargs)


class RichTable:
    def __init__(self, console: Console = None):
        self.console = console or Console()

    def print(self, data: List[Dict[str, any]], title: str = None, color: StyleType = "green", **kwargs):
        columns = kwargs.pop("columns", None)
        table = Table(title=title, style=color, **kwargs)

        item0 = data[0]
        if isinstance(item0, dict):
            for key in item0.keys():
                table.add_column(key, overflow="fold")
            for item in data:
                table.add_row(*item.values())
        elif isinstance(item0, list):
            if columns is None:
                columns = [f"col{i}" for i in range(len(item0))]
            for column in columns:
                table.add_column(column, overflow="fold")
            for item in data:
                table.add_row(*item)
        self.console.print(table, style=color)

    def print_red(self, data: List[Dict[str, any]], title: str = None, **kwargs):
        self.print(data, title=title, color="red", **kwargs)

    def print_green(self, data: List[Dict[str, any]], title: str = None, **kwargs):
        self.print(data, title=title, color="green", **kwargs)

    def print_yellow(self, data: List[Dict[str, any]], title: str = None, **kwargs):
        self.print(data, title=title, color="yellow", **kwargs)

    def print_blue(self, data: List[Dict[str, any]], title: str = None, **kwargs):
        self.print(data, title=title, color="blue", **kwargs)


class RichProgress:
    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.progress = None
        self.task = None

    @contextmanager
    def process_with_progress(self, total: int, description: str = "处理中...") -> Progress:
        """带进度条的处理函数
        
        Args:
            total: 总进度
            description: 描述
        Returns:
            Progress: 进度条
        
        示例:
            >>> rich_progress = RichProgress()
            >>> with rich_progress.process_with_progress(total=10) as (progress, task):
            >>>     for i in range(10):
            >>>         time.sleep(0.1)
            >>>         rich_progress.update(task, advance=1, description=f"处理中...{i}")
        """
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        self.progress.start()
        self.task = self.progress.add_task(description, total=total)
        yield self.progress, self.task
        self.progress.stop()

    def update(self, value: int, description: str = None):
        self.progress.update(self.task, advance=value, description=description)


class RichTrack:
    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.track = None

    def __call__(self, total: int, description: str = "处理中...") -> Iterable[ProgressType]:
        return track(range(total), description=description)


class RichConsole:
    def __init__(self):
        self.console = Console()
        self.plain = RichPlain(console=self.console)
        self.panel = RichPanel(console=self.console)
        self.table = RichTable(console=self.console)
        self.progress = RichProgress(console=self.console)
        self.track = RichTrack(console=self.console)


rich_console = RichConsole()


def main():
    import time

    data = [{"key": "1", "url": "2", "etag": "3"},
            {"key": "4", "url": "5", "etag": "6"}]
    # 1. 打印表格
    rich_console.table.print(data, title="Test List[dict] Table")
    data = [["1", "2", "3"], ["4", "5", "6"]]
    rich_console.table.print(data, title="Test List[list] Table")

    # 2. 打印面板
    rich_console.panel.print_green(
        {"key": "1", "url": "2", "etag": "3"}, title="Test Panel")

    # 3. 打印字符串
    rich_console.plain.print_yellow("Hello, World!")

    # 4. 打印进度条
    with rich_console.progress.process_with_progress(total=10) as progress:
        for i in range(10):
            time.sleep(0.1)
            rich_console.progress.update(i, description=f"处理中...{i}")

    # 5. 打印跟踪
    for i in rich_console.track(total=10, description="处理中..."):
        time.sleep(0.1)
        # rich_console.plain.print_green(i)


if __name__ == "__main__":
    main()
