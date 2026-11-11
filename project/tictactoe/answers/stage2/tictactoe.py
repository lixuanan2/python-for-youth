# 井字棋 —— 第 1 到 2 关的参考答案（老师用，不要发给学生）


# ===== 参考答案 =====

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
