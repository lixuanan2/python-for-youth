# 第 3 关：谁赢了（Python）

## 这一关做什么

先写一个查“一条线”的小函数，再用它查全部 8 条线，找出赢家。

## 要先学完

- 05-logic 逻辑运算（and）
- 10-list-basics 列表基础
- 11-list-loop 列表遍历
- 15-params-return 参数与返回值（函数里调用函数）

## 大约要多久

约 1 节课

## 要写的函数（名字、参数必须照写）

### `line_owner`

```python
def line_owner(board, a, b, c):
```

- 给它：棋盘，和一条线上的三个格子编号 a、b、c
- 还给你：三格都是 'X' 就还 'X'，三格都是 'O' 就还 'O'，不然还 '.'

例子：

- `line_owner("XXX......", 0, 1, 2) 还 'X'`
- `line_owner("XXO......", 0, 1, 2) 还 '.'`
- `line_owner("O..O..O..", 0, 3, 6) 还 'O'`

### `winner`

```python
def winner(board):
```

- 给它：棋盘
- 还给你：赢的一方 'X' 或 'O'；没人赢就还 '.'
- 一共 8 条线：横 0 1 2、3 4 5、6 7 8；竖 0 3 6、1 4 7、2 5 8；斜 0 4 8、2 4 6
- 提示：把 8 条线的 line_owner 结果放进一个列表，再找出不是 '.' 的那个

例子：

- `winner("OOO.X.X..") 还 'O'`
- `winner("X...X...X") 还 'X'`
- `winner("XOXXOOOXX") 还 '.'`：下满了，平局

## 文件夹里有什么

| 文件 | 谁写 | 做什么 |
| --- | --- | --- |
| `tictactoe.py` | **你** | 只改最下面“第 3 关：你来写”的部分；上面是前几关的参考答案，可以看、不用改 |
| `test_stage3.py` | 老师 | 检查你写对没有 |
| `play.py` | 老师 | 测试全过以后用来玩 |
| `guide.md` | 老师 | 就是这一页 |

## 怎么运行测试

任选一种：

- **PyCharm**：File → Open，选这个 `stage3` 文件夹。左边右键 `test_stage3.py` → Run。
- **VS Code**：File → Open Folder，选这个文件夹。打开 `test_stage3.py`，点右上角的 ▶（Run Python File）。要先装好 Python 扩展。
- **IDLE**：打开 `test_stage3.py`，按 F5。
- **命令行**：在这个文件夹的地址栏里输入 `cmd` 回车，再输入 `python test_stage3.py`（不行就试 `py test_stage3.py`）。

怎么看结果：每条测试一行，后面是 `ok` 或 `FAIL`。最后一行是 `OK` 就是全部通过；是 `FAILED (failures=3)` 就是有 3 条没通过，往上找 `FAIL`，看中文说明和 `AssertionError` 后面“你的 != 应该的”。

如果出现 `ImportError` 或 `NameError`：多半是函数名写错了，或者 `tictactoe.py` 不在同一个文件夹里。

不要在文件夹窗口里双击 `.py` 文件：窗口会一闪就关，看不到结果。用编辑器打开再运行。

## 测试全过以后

运行 `play.py`（和运行测试的方法一样）。
两个人可以对战了，有人连成一条线就结束。

## 做完了？想一想

如果棋盘上 X 和 O 都连成了一条线（真实对局不会这样），你的 winner 会还谁？为什么？
