# 井字棋 —— 第 4 关：下满没有、轮到谁
# 你只改最下面“第 4 关：你来写”里的函数。
# 函数名和参数不能改：老师的测试按这些名字检查。
# 写完运行 test_stage4.py 检查；全部通过再运行 play.py 玩。
#
# 棋盘是 9 个字符的字符串，格子编号 0 到 8：
#
#      0 | 1 | 2
#     ---+---+---
#      3 | 4 | 5
#     ---+---+---
#      6 | 7 | 8
#
# 'X' 和 'O' 是棋子，'.' 是空格。例如 "X...O...." 是 X 在 0 号格、O 在 4 号格。


# ===== 老师写好的：前几关的参考答案，不用改 =====

def can_put(board, i):
    # 给它：棋盘 board（9 个字符），格子编号 i
    # 还给你：第 i 格能不能下，能就是 True，不能就是 False
    # 能下要同时满足两条：i 在 0 到 8 之间；board[i] 是 '.'
    # 注意：先查 i 在不在 0 到 8，再看 board[i]，不然会超出字符串
    # 例子：can_put(".........", 4) 还 True
    #       can_put("X........", 0) 还 False（已经有子了）
    #       can_put(".........", 9) 还 False（没有第 9 格）
    if i < 0 or i > 8:
        return False
    return board[i] == '.'


def put(board, i, who):
    # 给它：棋盘 board、格子编号 i（可以放心：0 到 8，而且是空格）、棋子 who（'X' 或 'O'）
    # 还给你：下完以后的新棋盘，还是 9 个字符
    # 提示：字符串不能直接改一个字。用第 12 课的切片，把第 i 格前面的部分、who、第 i 格后面的部分拼起来
    # 例子：put(".........", 4, 'X') 还 "....X...."
    #       put("X........", 8, 'O') 还 "X.......O"
    return board[:i] + who + board[i + 1:]


def line_owner(board, a, b, c):
    # 给它：棋盘，和一条线上的三个格子编号 a、b、c
    # 还给你：三格都是 'X' 就还 'X'，三格都是 'O' 就还 'O'，不然还 '.'
    # 例子：line_owner("XXX......", 0, 1, 2) 还 'X'
    #       line_owner("XXO......", 0, 1, 2) 还 '.'
    #       line_owner("O..O..O..", 0, 3, 6) 还 'O'
    if board[a] != '.' and board[a] == board[b] and board[b] == board[c]:
        return board[a]
    return '.'


def winner(board):
    # 给它：棋盘
    # 还给你：赢的一方 'X' 或 'O'；没人赢就还 '.'
    # 一共 8 条线：横 0 1 2、3 4 5、6 7 8；竖 0 3 6、1 4 7、2 5 8；斜 0 4 8、2 4 6
    # 提示：把 8 条线的 line_owner 结果放进一个列表，再找出不是 '.' 的那个
    # 例子：winner("OOO.X.X..") 还 'O'
    #       winner("X...X...X") 还 'X'
    #       winner("XOXXOOOXX") 还 '.'（下满了，平局）
    owners = [line_owner(board, 0, 1, 2), line_owner(board, 3, 4, 5),
              line_owner(board, 6, 7, 8), line_owner(board, 0, 3, 6),
              line_owner(board, 1, 4, 7), line_owner(board, 2, 5, 8),
              line_owner(board, 0, 4, 8), line_owner(board, 2, 4, 6)]
    result = '.'
    for w in owners:
        if w != '.':
            result = w
    return result


# ===== 第 4 关：你来写 =====
# 把下面函数里的 return 换成你的代码。现在的 return 只是占位，测试会不通过。

def is_full(board):
    # 给它：棋盘
    # 还给你：9 格都下满了吗（一个 '.' 都没有了）
    # 例子：is_full("XOXXOOOXX") 还 True
    #       is_full("XOXXOOOX.") 还 False
    return False


def turn(board):
    # 给它：棋盘（可以放心：X 先下，两人轮流）
    # 还给你：现在轮到谁下，'X' 或 'O'
    # X 和 O 一样多，轮到 X；X 比 O 多一个，轮到 O
    # 例子：turn(".........") 还 'X'
    #       turn("X........") 还 'O'
    #       turn("XO.......") 还 'X'
    return 'X'
