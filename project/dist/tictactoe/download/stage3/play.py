# 井字棋 —— 老师的文字版前端（第 3 关）。学生不用改，也不用看懂。
# 先运行 test_stage3.py，全部通过以后再运行这个文件。
# 关卡越往后，这里能玩的就越多：
#   第 1 关：试试 can_put
#   第 2 关：两个人随便下（还不会判断输赢）
#   第 3 关：两个人对战，能判断输赢
#   第 4 关：用你的 turn、is_full 管轮流和平局
#   第 5 关：可以和电脑下

import tictactoe as t

STAGE = 3


def read_line(prompt):
    # 读一行；没有输入了就当作 q
    try:
        return input(prompt).strip()
    except EOFError:
        return "q"


def show(board):
    for r in range(3):
        cells = []
        for c in range(3):
            i = r * 3 + c
            if board[i] == '.':
                cells.append(str(i))
            else:
                cells.append(board[i])
        print(" " + " | ".join(cells))
        if r < 2:
            print("---+---+---")
    print()


def ask(board, who):
    # 问人下哪一格；输入 q 退出，返回 -1
    while True:
        s = read_line(who + " 下哪一格（0-8，q 退出）：")
        if s == "q":
            return -1
        if s.isdigit() and t.can_put(board, int(s)):
            return int(s)
        print("这一格不能下，换一格。")


def stage1():
    board = "X...O...."
    show(board)
    print("第 1 关：输入格子编号，看看你的 can_put 怎么说。输入 q 退出。")
    while True:
        s = read_line("格子编号：")
        if s == "q":
            return
        try:
            n = int(s)
        except ValueError:
            print("请输入一个整数。")
            continue
        print("can_put(\"" + board + "\", " + str(n) + ") 还", t.can_put(board, n))


def one_game(computer):
    # computer 是电脑下的那一方 'X' 或 'O'；'.' 表示两个人对战
    # 返回赢家 'X'、'O'，平局 '.'，中途退出 'q'
    board = "........."
    moves = 0
    who = 'X'
    while True:
        show(board)
        if STAGE >= 4:
            who = t.turn(board)
        if who == computer:
            i = t.computer_move(board)
            if not t.can_put(board, i):
                print("computer_move 还了", i, "，这一格不能下。先让 test_stage5.py 全部通过。")
                return 'q'
            print("电脑下在", i)
        else:
            i = ask(board, who)
            if i == -1:
                return 'q'
        board = t.put(board, i, who)
        moves = moves + 1
        if STAGE >= 3 and t.winner(board) != '.':
            show(board)
            return t.winner(board)
        if STAGE >= 4:
            full = t.is_full(board)
        else:
            full = moves == 9
        if full:
            show(board)
            return '.'
        if STAGE < 4:
            if who == 'X':
                who = 'O'
            else:
                who = 'X'


def main():
    if STAGE == 1:
        stage1()
        return
    if STAGE == 2:
        print("第 2 关：两个人轮流下，还不会判断输赢（第 3 关做完就会了）。")
    computer = '.'
    if STAGE >= 5:
        s = read_line("1 = 两个人下，2 = 你先下（X）和电脑下，3 = 电脑先下：")
        if s == "2":
            computer = 'O'
        if s == "3":
            computer = 'X'
    score = {'X': 0, 'O': 0, '.': 0}
    again = True
    while again:
        result = one_game(computer)
        if result == 'q':
            again = False
        else:
            if STAGE == 2:
                print("下满了。")
            elif result == '.':
                print("平局！")
            else:
                print(result, "赢了！")
            score[result] = score[result] + 1
            print("比分：X", score['X'], "  O", score['O'], "  平局", score['.'])
            again = read_line("再来一局？（y/n）：") == "y"
    print("再见！")


main()
