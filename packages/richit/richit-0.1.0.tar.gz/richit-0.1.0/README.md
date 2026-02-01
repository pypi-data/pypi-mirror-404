# Richit

Richit 是用于在终端中输出富文本和美化的 Python 库，提供彩色、样式、表格、进度条、Markdown、语法高亮、追踪信息等功能。

## 兼容性

支持 Linux、macOS 和 Windows。新版 Windows 终端支持真彩色与 emoji，经典终端为 16 色。需要 Python 3.8 及以上。

可在 [Jupyter notebooks](https://jupyter.org/) 中直接使用，无需额外配置。

## 安装

使用 pip 或你常用的包管理器安装：

```sh
python -m pip install richit
```

在终端中运行以下命令查看效果：

```sh
python -m richit
```

## Print

为应用添加富文本输出，可导入与内置 `print` 签名相同的 `print`：

```python
from richit import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

## REPL

在 Python REPL 中安装后，数据结构会以高亮和美化形式输出：

```python
>>> from richit import pretty
>>> pretty.install()
```

## 使用 Console

需要更细粒度控制时，可创建 `Console` 对象：

```python
from richit.console import Console

console = Console()
```

`Console` 的 `print` 与内置 `print` 用法相近：

```python
console.print("Hello", "World!")
```

输出会按终端宽度自动换行。

可通过 `style` 参数为整段输出设置样式：

```python
console.print("Hello", "World!", style="bold red")
```

也可在文本内使用类 bbcode 的标记做细粒度样式：

```python
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

## Inspect

`inspect` 可对任意 Python 对象（类、实例、内置类型等）生成报告：

```python
>>> my_list = ["foo", "bar"]
>>> from richit import inspect
>>> inspect(my_list, methods=True)
```

## 内置组件

Richit 提供多种可渲染对象，用于在 CLI 中输出和调试。

### Log

`Console` 的 `log()` 与 `print()` 类似，但会多出一列显示当前时间和调用位置。默认会对 Python 结构和 repr 做语法高亮；对字典、列表等会做美化输出。例如：

```python
from richit.console import Console
console = Console()

test_data = [
    {"jsonrpc": "2.0", "method": "sum", "params": [None, 1, 2, 4, False, True], "id": "1",},
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"},
]

def test_log():
    enabled = False
    context = {"foo": "bar"}
    movies = ["Deadpool", "Rise of the Skywalker"]
    console.log("Hello from", console, "!")
    console.log(test_data, log_locals=True)

test_log()
```

`log_locals` 会输出调用处的局部变量表，适合长时间运行的程序或调试。

### Logging Handler

内置的 Handler 可与 Python 的 `logging` 模块配合，对日志进行格式化和着色。

### 日志内容加密

`Panel` 的日志内容会使用固定密码 `richit` 进行加密后输出。

### Emoji

在输出中用两个冒号包裹名称即可插入 emoji：

```python
>>> console.print(":smiley: :vampire: :pile_of_poo: :thumbs_up: :raccoon:")
😃 🧛 💩 👍 🦝
```

### Tables

支持用 Unicode 框线绘制表格，可配置边框、样式、对齐等。示例：

```python
from richit.console import Console
from richit.table import Table

console = Console()

table = Table(show_header=True, header_style="bold magenta")
table.add_column("Date", style="dim", width=12)
table.add_column("Title")
table.add_column("Production Budget", justify="right")
table.add_column("Box Office", justify="right")
table.add_row(
    "Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$275,000,000", "$375,126,118"
)
table.add_row(
    "May 25, 2018",
    "[red]Solo[/red]: A Star Wars Story",
    "$275,000,000",
    "$393,151,347",
)
table.add_row(
    "Dec 15, 2017",
    "Star Wars Ep. VIII: The Last Jedi",
    "$262,000,000",
    "[bold]$1,332,539,889[/bold]",
)

console.print(table)
```

表格会随终端宽度自动调整列宽并换行。表头/单元格中可使用与 `print()`、`log()` 相同的标记，也可放入其他可渲染对象（包括嵌套表格）。

### Progress Bars

支持无闪烁的多进度条，用于长时间任务。基本用法：用 `track` 包装序列后遍历：

```python
from richit.progress import track

for step in track(range(100)):
    do_step(step)
```

可配置列以显示完成百分比、文件大小、速度、剩余时间等。

### Status

无法计算进度时，可用 `status()` 显示旋转动画和消息，同时仍可正常使用 console：

```python
from time import sleep
from richit.console import Console

console = Console()
tasks = [f"task {n}" for n in range(1, 11)]

with console.status("[bold green]Working on tasks...") as status:
    while tasks:
        task = tasks.pop(0)
        sleep(1)
        console.log(f"{task} complete")
```

通过 `spinner` 参数选择动画。查看可用值：

```sh
python -m richit.spinner
```

### Tree

可渲染带引导线的树形结构，适合目录或层级数据。演示：

```sh
python -m richit.tree
```

### Columns

支持等宽或最优宽度的多列布局，例如仿 `ls` 的目录列表：

```python
import os
import sys
from richit import print
from richit.columns import Columns

directory = os.listdir(sys.argv[1])
print(Columns(directory))
```

### Markdown

可将 Markdown 字符串渲染到终端。使用 `Markdown` 类并打印到 console：

```python
from richit.console import Console
from richit.markdown import Markdown

console = Console()
with open("README.md") as readme:
    markdown = Markdown(readme.read())
console.print(markdown)
```

### Syntax Highlighting

基于 pygments 做语法高亮。构造 `Syntax` 对象后打印：

```python
from richit.console import Console
from richit.syntax import Syntax

my_code = '''
def iter_first_last(values: Iterable[T]) -> Iterable[Tuple[bool, bool, T]]:
    """Iterate and generate a tuple with a flag for first and last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    first = True
    for value in iter_values:
        yield first, False, previous_value
        first = False
        previous_value = value
    yield first, True, previous_value
'''
syntax = Syntax(my_code, "python", theme="monokai", line_numbers=True)
console = Console()
console.print(syntax)
```

### Tracebacks

可渲染更易读、代码上下文更多的追踪信息，并设为默认的未捕获异常展示方式。

---

所有可渲染对象都遵循统一的 Console 协议，你也可以实现自己的可渲染内容。
