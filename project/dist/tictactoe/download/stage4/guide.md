# 第 4 关：下满没有、轮到谁（Python）

## 这一关做什么

写两个小函数：棋盘下满了没有；现在轮到谁下。

## 要先学完

- 08-loop-tally 累加和计数
- 13-string-methods 字符串常用方法（count）
- 15-params-return 参数与返回值

## 大约要多久

约半节到 1 节课；做完就能两个人对战

## 要写的函数（名字、参数必须照写）

### `is_full`

```python
def is_full(board):
```

- 给它：棋盘
- 还给你：9 格都下满了吗（一个 '.' 都没有了）

例子：

- `is_full("XOXXOOOXX") 还 True`
- `is_full("XOXXOOOX.") 还 False`

### `turn`

```python
def turn(board):
```

- 给它：棋盘（可以放心：X 先下，两人轮流）
- 还给你：现在轮到谁下，'X' 或 'O'
- X 和 O 一样多，轮到 X；X 比 O 多一个，轮到 O

例子：

- `turn(".........") 还 'X'`
- `turn("X........") 还 'O'`
- `turn("XO.......") 还 'X'`

## 文件夹里有什么

| 文件 | 谁写 | 做什么 |
| --- | --- | --- |
| `tictactoe.py` | **你** | 只改最下面“第 4 关：你来写”的部分；上面是前几关的参考答案，可以看、不用改 |
| `test_stage4.py` | 老师 | 检查你写对没有 |
| `play.py` | 老师 | 测试全过以后用来玩 |
| `guide.md` | 老师 | 就是这一页 |

## 怎么运行测试

任选一种：

- **PyCharm**：File → Open，选这个 `stage4` 文件夹。左边右键 `test_stage4.py` → Run。
- **VS Code**：File → Open Folder，选这个文件夹。打开 `test_stage4.py`，点右上角的 ▶（Run Python File）。要先装好 Python 扩展。
- **IDLE**：打开 `test_stage4.py`，按 F5。
- **命令行**：在这个文件夹的地址栏里输入 `cmd` 回车，再输入 `python test_stage4.py`（不行就试 `py test_stage4.py`）。

怎么看结果：每条测试一行，后面是 `ok` 或 `FAIL`。最后一行是 `OK` 就是全部通过；是 `FAILED (failures=3)` 就是有 3 条没通过，往上找 `FAIL`，看中文说明和 `AssertionError` 后面“你的 != 应该的”。

如果出现 `ImportError` 或 `NameError`：多半是函数名写错了，或者 `tictactoe.py` 不在同一个文件夹里。

不要在文件夹窗口里双击 `.py` 文件：窗口会一闪就关，看不到结果。用编辑器打开再运行。

## 测试全过以后

运行 `play.py`（和运行测试的方法一样）。
轮到谁、下满没有，都用你自己写的函数来管了。

## 做完了？想一想

如果有人偷偷连下两步，X 比 O 多两个，你的 turn 会还什么？要不要管这种情况？
