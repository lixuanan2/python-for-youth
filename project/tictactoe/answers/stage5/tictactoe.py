# 井字棋 —— 第 1 到 5 关的参考答案（老师用，不要发给学生）


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


def is_full(board):
    # 给它：棋盘
    # 还给你：9 格都下满了吗（一个 '.' 都没有了）
    # 例子：is_full("XOXXOOOXX") 还 True
    #       is_full("XOXXOOOX.") 还 False
    return board.count('.') == 0


def turn(board):
    # 给它：棋盘（可以放心：X 先下，两人轮流）
    # 还给你：现在轮到谁下，'X' 或 'O'
    # X 和 O 一样多，轮到 X；X 比 O 多一个，轮到 O
    # 例子：turn(".........") 还 'X'
    #       turn("X........") 还 'O'
    #       turn("XO.......") 还 'X'
    if board.count('X') == board.count('O'):
        return 'X'
    return 'O'


def computer_move(board):
    # 给它：还没下完、也还没人赢的棋盘。电脑下的是 turn(board) 那一方
    # 还给你：电脑要下的格子编号 0 到 8
    # 按顺序想：
    #   1. 有没有一格，我下了就赢？有就下那里（有好几格，选编号最小的）
    #   2. 有没有一格，对方下了就赢？有就堵住那里（同样选编号最小的）
    #   3. 都没有，就下编号最小的空格
    # 提示：试一格 = can_put 看能不能下，put 下一下，winner 看看谁赢。试完不用“拿走”，因为 put 还回去的是新棋盘
    # 提示：没学 break，可以先让答案等于 -1，找到了再改；已经找到就不再改
    # 例子：computer_move("XX.OO....") 还 2（轮到 X，X 下 2 就赢）
    #       computer_move("XX..O....") 还 2（轮到 O，O 要堵住 2）
    #       computer_move("X........") 还 1（没有要赢、要堵的，下第一个空格）
    me = turn(board)
    other = 'X'
    if me == 'X':
        other = 'O'
    move = -1
    for i in range(9):
        if move == -1 and can_put(board, i):
            if winner(put(board, i, me)) == me:
                move = i
    for i in range(9):
        if move == -1 and can_put(board, i):
            if winner(put(board, i, other)) == other:
                move = i
    for i in range(9):
        if move == -1 and can_put(board, i):
            move = i
    return move
