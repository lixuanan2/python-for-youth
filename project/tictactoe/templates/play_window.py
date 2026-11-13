# 井字棋 —— 老师的窗口版前端（第 @STAGE@ 关）。学生不用改，也不用看懂。
# 先运行 test_stage@STAGE@.py，全部通过以后再运行这个文件。
# 它和 play.py 用的是同一组函数：can_put、put、winner、is_full、turn、computer_move。
# 画面从终端换成了窗口，你写的 tictactoe.py 一行都不用改。
# 图片在 assets 文件夹里：board.png 是棋盘，x.png、o.png 是棋子。换成自己画的也行，文件名不变就好。

import os
import sys
import tkinter as tk

import tictactoe as t

for stream in (sys.stdout, sys.stderr):  # 有的电脑的控制台显示不了中文，换成 UTF-8；学生不用管
    try:
        "中文".encode(stream.encoding or "ascii")
    except (LookupError, UnicodeEncodeError):
        stream.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
HINT = "先让 test_stage@STAGE@.py 全部通过。"

# board 是现在的棋盘；computer 是电脑下的那一方，'.' 表示两个人下；over 为 True 时点格子没反应
game = {"board": ".........", "computer": ".", "over": False, "delay": 500}
score = {'X': 0, 'O': 0, '.': 0}


def ask(function, *args):
    # 调用你写的函数。出错了就在窗口里提示，不让程序崩掉
    try:
        return function(*args)
    except Exception as e:
        stop("你的 " + function.__name__ + " 出错了（" + type(e).__name__ + "）。" + HINT)
        return None


def say(text):
    status["text"] = text


def stop(text):
    game["over"] = True
    say(text)


def draw():
    canvas.delete("piece")
    for k in range(9):
        c = game["board"][k]
        if c == 'X' or c == 'O':
            x = (k % 3) * cell + cell // 2
            y = (k // 3) * cell + cell // 2
            canvas.create_image(x, y, image=pieces[c], tags="piece")


def new_game(computer):
    game["board"] = "........."
    game["computer"] = computer
    game["over"] = False
    draw()
    next_turn()


def next_turn():
    # 下完了吗？没下完就说该谁下；轮到电脑，就让电脑下
    board = game["board"]
    w = ask(t.winner, board)
    if game["over"]:
        return
    if w == 'X' or w == 'O':
        score[w] = score[w] + 1
        stop(w + " 赢了！点上面的按钮再来一局。")
        show_score()
        return
    full = ask(t.is_full, board)
    if game["over"]:
        return
    if full:
        score['.'] = score['.'] + 1
        stop("平局！点上面的按钮再来一局。")
        show_score()
        return
    who = ask(t.turn, board)
    if game["over"]:
        return
    if who == game["computer"]:
        say("电脑在想……")
        if game["delay"] == 0:
            computer_moves()
        else:
            window.after(game["delay"], computer_moves)
    else:
        say("轮到 " + str(who) + "：点一个空格")


def computer_moves():
    board = game["board"]
    i = ask(t.computer_move, board)
    if game["over"]:
        return
    ok = ask(t.can_put, board, i)
    if game["over"]:
        return
    if ok != True:
        stop("computer_move 还了 " + str(i) + "，这一格不能下。" + HINT)
        return
    move(i, game["computer"])


def click_cell(i):
    if game["over"]:
        return
    who = ask(t.turn, game["board"])
    if game["over"] or who == game["computer"]:
        return
    ok = ask(t.can_put, game["board"], i)
    if game["over"]:
        return
    if ok != True:
        say("这一格不能下，换一格。")
        return
    move(i, who)


def move(i, who):
    board = ask(t.put, game["board"], i, who)
    if game["over"]:
        return
    if type(board) != str or len(board) != 9:
        stop("put 还回来的不是 9 个字符的棋盘。" + HINT)
        return
    game["board"] = board
    draw()
    next_turn()


def show_score():
    scores["text"] = "比分　X " + str(score['X']) + "　O " + str(score['O']) + "　平局 " + str(score['.'])


def self_test():
    # 老师检查用：python play_window.py --selftest。不开窗口，按顺序点格子，看结果对不对
    game["delay"] = 0
    tries = []
    new_game('.')
    for i in [0, 3, 1, 4, 2]:
        click_cell(i)
    tries.append(("两个人下", status["text"].startswith("X 赢了")))
    new_game('.')
    click_cell(4)
    click_cell(4)
    tries.append(("点已经有棋子的格", status["text"] == "这一格不能下，换一格。"))
    for computer, name in [('O', "你先下"), ('X', "电脑先下")]:
        new_game(computer)
        for move_number in range(9):
            for k in range(9):
                if not game["over"] and game["board"][k] == '.':
                    click_cell(k)
                    break
        tries.append((name, "赢了" in status["text"] or "平局" in status["text"]))
    for name, ok in tries:
        if not ok:
            print("自检没通过（" + name + "）：" + status["text"])
            sys.exit(1)
    print("自检通过：图片 " + str(board_picture.width()) + "×" + str(board_picture.height()) + "，" + "、".join(n for n, ok in tries) + "都对。")


window = tk.Tk()
window.title("井字棋")
board_picture = tk.PhotoImage(file=os.path.join(HERE, "assets", "board.png"))
pieces = {'X': tk.PhotoImage(file=os.path.join(HERE, "assets", "x.png")),
          'O': tk.PhotoImage(file=os.path.join(HERE, "assets", "o.png"))}
cell = board_picture.width() // 3

buttons = tk.Frame(window)
buttons.pack(padx=12, pady=10)
tk.Button(buttons, text="两个人下", command=lambda: new_game('.')).pack(side="left", padx=4)
tk.Button(buttons, text="你先下（X）", command=lambda: new_game('O')).pack(side="left", padx=4)
tk.Button(buttons, text="电脑先下", command=lambda: new_game('X')).pack(side="left", padx=4)

canvas = tk.Canvas(window, width=board_picture.width(), height=board_picture.height(), highlightthickness=0)
canvas.create_image(0, 0, image=board_picture, anchor="nw")
canvas.bind("<Button-1>", lambda e: click_cell(min(e.y // cell, 2) * 3 + min(e.x // cell, 2)))
canvas.pack(padx=12)

status = tk.Label(window, font=("", 16))
status.pack(pady=(10, 2))
scores = tk.Label(window, font=("", 13))
scores.pack(pady=(0, 12))
show_score()

if "--selftest" in sys.argv:
    window.withdraw()
    self_test()
    window.destroy()
else:
    new_game('.')
    window.mainloop()
