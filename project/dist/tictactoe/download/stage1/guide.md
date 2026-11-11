# 第 1 关：这一格能下吗（Python）

## 这一关做什么

写一个函数，判断棋盘上的某一格现在能不能下棋。

## 要先学完

- 04-conditions 条件判断
- 05-logic 逻辑运算
- 12-string-basics 字符串基础（下标）
- 15-params-return 参数与返回值

## 大约要多久

约 1 节课（45 分钟）：其中 15 分钟认识项目、文件夹和怎么运行测试

## 要写的函数（名字、参数必须照写）

### `can_put`

```python
def can_put(board, i):
```

- 给它：棋盘 board（9 个字符），格子编号 i
- 还给你：第 i 格能不能下，能就是 True，不能就是 False
- 能下要同时满足两条：i 在 0 到 8 之间；board[i] 是 '.'
- 注意：先查 i 在不在 0 到 8，再看 board[i]，不然会超出字符串

例子：

- `can_put(".........", 4) 还 True`
- `can_put("X........", 0) 还 False`：已经有子了
- `can_put(".........", 9) 还 False`：没有第 9 格

## 文件夹里有什么

| 文件 | 谁写 | 做什么 |
| --- | --- | --- |
| `tictactoe.py` | **你** | 只改最下面“第 1 关：你来写”的部分 |
| `test_stage1.py` | 老师 | 检查你写对没有 |
| `play.py` | 老师 | 测试全过以后用来玩 |
| `guide.md` | 老师 | 就是这一页 |

## 怎么运行测试

任选一种：

- **PyCharm**：File → Open，选这个 `stage1` 文件夹。左边右键 `test_stage1.py` → Run。
- **VS Code**：File → Open Folder，选这个文件夹。打开 `test_stage1.py`，点右上角的 ▶（Run Python File）。要先装好 Python 扩展。
- **IDLE**：打开 `test_stage1.py`，按 F5。
- **命令行**：在这个文件夹的地址栏里输入 `cmd` 回车，再输入 `python test_stage1.py`（不行就试 `py test_stage1.py`）。

怎么看结果：每条测试一行，后面是 `ok` 或 `FAIL`。最后一行是 `OK` 就是全部通过；是 `FAILED (failures=3)` 就是有 3 条没通过，往上找 `FAIL`，看中文说明和 `AssertionError` 后面“你的 != 应该的”。

如果出现 `ImportError` 或 `NameError`：多半是函数名写错了，或者 `tictactoe.py` 不在同一个文件夹里。

不要在文件夹窗口里双击 `.py` 文件：窗口会一闪就关，看不到结果。用编辑器打开再运行。

## 测试全过以后

运行 `play.py`（和运行测试的方法一样）。
第 1 关能做的不多：输入格子编号，看你的 `can_put` 怎么说。

## 做完了？想一想

如果不先查 i 在不在 0 到 8，直接看 board[i]，输入 9 会发生什么？在 play 里试试（Python 会报错，C++ 结果是乱的）。
