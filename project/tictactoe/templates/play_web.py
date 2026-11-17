# 井字棋 —— 老师的网页版前端（第 @STAGE@ 关）。学生不用改，也不用看懂。
# 先运行 test_stage@STAGE@.py，全部通过以后再运行这个文件：它会打开浏览器，在网页上看你的函数做了什么。
# 每做完一关，网页上就多一样东西：
#   第 1 关：每一格能不能下（can_put）
#   第 2 关：点格子下棋，两个人轮流（put）
#   第 3 关：连成一条线就赢，那条线会亮起来（line_owner、winner）
#   第 4 关：轮到谁、平局，由你的函数说了算（turn、is_full）
#   第 5 关：可以和电脑下（computer_move）
# 后面几关的东西在网页上是灰的，写着“第 N 关解锁”。它和 play.py 用的是同一组函数，你写的 tictactoe.py 一行都不用改。
# 网页在 web 文件夹里，图片在 web/assets：board.png 是棋盘，x.png、o.png 是棋子。换成自己画的也行，文件名不变就好。
#
# 网页和这个文件怎么说话（以后别的语言的后端照这一套做）：
#   POST /api/check      发 {"board": "X...O....", "cell": 4}             问 can_put 这一格能不能下
#   POST /api/new        发 {}                                             回一个空棋盘
#   POST /api/move       发 {"board": "X........", "cell": 4, "who": "O"}  下在 cell；第 4 关起由 turn 决定谁下，不看 who
#   POST /api/computer   发 {"board": "X........"}                         电脑下一步（computer_move）
#   回的都是 JSON，calls 是这一步调用了你的哪些函数、还了什么：
#     {"ok": true, "board": "X...O....", "cell": 4, "turn": "X", "winner": ".", "line": [], "full": false, "calls": [...]}
#     {"ok": true, "cell": 4, "can": false, "calls": [...]}                                     /api/check 的回答
#     {"ok": false, "message": "这一格不能下，换一格。", "board": ...}                           点了不能下的格
#     {"ok": false, "error": "先让 test_stage5.py 全部通过。", "detail": "...", "board": ...}  你的函数出错了
#   第 3 关以前还不会判断输赢，winner 是 null；第 4 关以前“下满了”由这个文件自己数。
# 只在这台电脑上打开（127.0.0.1），别的电脑连不进来。按 Ctrl+C 结束。

import json
import os
import sys
import threading
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import tictactoe as t

for stream in (sys.stdout, sys.stderr):  # 有的电脑的控制台显示不了中文，换成 UTF-8；学生不用管
    try:
        "中文".encode(stream.encoding or "ascii")
    except (LookupError, UnicodeEncodeError):
        stream.reconfigure(encoding="utf-8")

STAGE = @STAGE@
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
HINT = "先让 test_stage@STAGE@.py 全部通过。"
TYPES = {".html": "text/html; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml", ".css": "text/css", ".js": "text/javascript"}
LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
TRY_BOARD = "X...O...."  # 第 1 关拿来试 can_put 的棋盘
calls = []  # 这一步调用了你的哪些函数；网页右边列出来


class Trouble(Exception):
    # 你的函数出错了，或者还回来的东西不对
    pass


def shown(value):
    # 照开发文档的写法：棋盘用双引号，棋子用单引号
    if type(value) == str:
        return '"' + value + '"' if len(value) == 9 else "'" + value + "'"
    return repr(value)


def call(function, *args):
    # 调用你写的函数，记下它还了什么；出错时找出是 tictactoe.py 的哪一行
    try:
        got = function(*args)
    except Exception as e:
        where = function.__name__
        for frame in traceback.extract_tb(e.__traceback__):
            if frame.filename.endswith("tictactoe.py"):
                where = "tictactoe.py 第 " + str(frame.lineno) + " 行：" + (frame.line or "")
        raise Trouble(where + "（" + type(e).__name__ + ": " + str(e) + "）")
    calls.append(function.__name__ + "(" + ", ".join(shown(a) for a in args) + ") 还 " + shown(got))
    return got


def check_board(board, name):
    if type(board) != str or len(board) != 9 or any(c not in "XO." for c in board):
        raise Trouble(name + " 还回来的不是 9 个字符的棋盘：" + repr(board))
    return board


def other(who):
    if who == 'X':
        return 'O'
    return 'X'


def state(board, cell, after):
    # 下完一步以后的样子。after 是下一步该谁（第 4 关以前由这个文件轮流）
    answer = {"ok": True, "board": board, "cell": cell, "winner": None, "line": [], "turn": after, "full": '.' not in board}
    if STAGE >= 3:
        w = call(t.winner, board)
        if w not in ('X', 'O', '.'):
            raise Trouble("winner 还了 " + shown(w) + "，应该是 'X'、'O' 或 '.'")
        answer["winner"] = w
        mark = len(calls)  # 8 条线都问一遍 line_owner，只把连成的那条留在 calls 里
        for a, b, c in LINES:
            if w != '.' and not answer["line"] and call(t.line_owner, board, a, b, c) == w:
                answer["line"] = [a, b, c]
                found = calls[-1]
        del calls[mark:]
        if answer["line"]:
            calls.append(found)
    if STAGE >= 4:
        full = call(t.is_full, board)
        if full != ('.' not in board):
            raise Trouble("is_full 还了 " + shown(full) + "，可是棋盘" + ("还有空格" if '.' in board else "已经没有空格了"))
        who = call(t.turn, board)
        should = 'X' if board.count('X') == board.count('O') else 'O'
        if who != should:
            raise Trouble("turn 还了 " + shown(who) + "，可是棋盘上有 " + str(board.count('X')) + " 个 X、" + str(board.count('O')) + " 个 O")
        answer["full"] = full
        answer["turn"] = who
    return answer


def place(board, cell, who):
    # 用你的 put 下一步，看看还回来的棋盘对不对
    new = check_board(call(t.put, board, cell, who), "put")
    if new[cell] != who or new[:cell] != board[:cell] or new[cell + 1:] != board[cell + 1:]:
        raise Trouble("put 还了 " + shown(new) + "，第 " + str(cell) + " 格应该变成 " + shown(who) + "，别的格不变")
    return new


def check(board, cell):
    can = call(t.can_put, board, cell)
    if type(can) != bool:
        raise Trouble("can_put 还了 " + shown(can) + "，应该是 True 或 False")
    return {"ok": True, "cell": cell, "can": can}


def move(board, cell, who):
    if STAGE < 2:
        return {"ok": False, "message": "下棋要等第 2 关解锁。", "board": board}
    if not check(board, cell)["can"]:
        return {"ok": False, "message": "这一格不能下，换一格。", "board": board}
    if STAGE >= 4:
        who = call(t.turn, board)
    elif who not in ('X', 'O'):
        who = 'X'
    return state(place(board, cell, who), cell, other(who))


def computer(board):
    if STAGE < 5:
        return {"ok": False, "message": "和电脑下要等第 5 关解锁。", "board": board}
    cell = call(t.computer_move, board)
    if type(cell) != int or not call(t.can_put, board, cell):
        raise Trouble("computer_move 还了 " + repr(cell) + "，这一格不能下")
    return state(place(board, cell, call(t.turn, board)), cell, '.')


def answer(path, asked):
    del calls[:]
    board = str(asked.get("board", "........."))
    try:
        if path == "/api/check":
            got = check(check_board(board, "网页"), int(asked.get("cell", -1)))
        elif path == "/api/new":
            got = state(".........", -1, 'X')
        elif path == "/api/move":
            got = move(check_board(board, "网页"), int(asked.get("cell", -1)), str(asked.get("who", "X")))
        elif path == "/api/computer":
            got = computer(check_board(board, "网页"))
        else:
            got = {"ok": False, "message": "没有这个接口：" + path, "board": board}
    except Trouble as e:
        got = {"ok": False, "error": HINT, "detail": str(e), "board": board}
    got["calls"] = list(calls)
    return got


class Handler(BaseHTTPRequestHandler):
    # http.server 要求这样写一个类；里面只有两件事：送网页文件、回答网页的问题
    def do_GET(self):
        path = self.path.split("?")[0]  # 网址后面的 ?… 不管
        name = "index.html" if path in ("/", "/index.html") else path.lstrip("/")
        file = os.path.normpath(os.path.join(WEB, name))
        if not file.startswith(WEB) or not os.path.isfile(file):
            self.send_error(404)
            return
        with open(file, "rb") as f:
            self.send(f.read(), TYPES.get(os.path.splitext(file)[1], "application/octet-stream"))

    def do_POST(self):
        size = int(self.headers.get("Content-Length", 0))
        try:
            asked = json.loads(self.rfile.read(size) or b"{}")
        except ValueError:
            asked = {}
        self.send(json.dumps(answer(self.path, asked), ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def send(self, data, kind):
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass  # 不在终端里刷屏


def self_test(url):
    # 老师检查用：python play_web.py --selftest。不开浏览器，像网页一样按接口试这一关有的东西
    import urllib.request

    def ask(path, asked):
        request = urllib.request.Request(url + path, json.dumps(asked).encode("utf-8"), {"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(request, timeout=10).read().decode("utf-8"))

    def fail(name, got):
        print("自检没通过（" + name + "）：" + got.get("error", got.get("message", "")) + " " + got.get("detail", ""))
        sys.exit(1)

    def wrong(name, detail):
        fail(name, {"error": HINT, "detail": detail})

    def play(cells):
        got = ask("/api/new", {})
        for cell in cells:
            if not got.get("ok"):
                break
            got = ask("/api/move", {"board": got["board"], "cell": cell, "who": got["turn"]})
        return got

    page = urllib.request.urlopen(url + "/", timeout=10).read().decode("utf-8")
    pictures = [urllib.request.urlopen(url + "/assets/" + name, timeout=10).read() for name in ("board.png", "x.png", "o.png")]
    if "井字棋" not in page or any(not p.startswith(b"\x89PNG") for p in pictures):
        print("自检没通过：网页或图片打不开")
        sys.exit(1)
    done = ["网页", "3 张图片", "每一格能不能下"]
    for cell in range(-1, 10):
        got = ask("/api/check", {"board": TRY_BOARD, "cell": cell})
        if not got.get("ok"):
            fail("can_put", got)
        if got["can"] != (0 <= cell <= 8 and TRY_BOARD[cell] == '.'):
            wrong("can_put", got["calls"][-1] + "，不对")
    if STAGE >= 2:
        got = play([0, 3, 1, 4, 2])
        if not got.get("ok"):
            fail("两个人下", got)
        if got["board"] != "XXXOO....":
            wrong("两个人下", "轮流下 0、3、1、4、2，棋盘应该是 \"XXXOO....\"，网页收到的是 " + shown(got["board"]))
        if STAGE >= 3 and (got["winner"] != 'X' or got["line"] != [0, 1, 2]):
            wrong("谁赢了", "X 连成 0 1 2，网页收到的赢家是 " + shown(got["winner"]) + "，亮的线是 " + str(got["line"]))
        if ask("/api/move", {"board": "....X....", "cell": 4, "who": 'O'}).get("message") != "这一格不能下，换一格。":
            fail("点已经有棋子的格", {})
        got = play([0, 1, 2, 4, 3, 5, 7, 6, 8])
        if not got.get("ok"):
            fail("下满", got)
        if not got["full"] or (STAGE >= 3 and got["winner"] != '.'):
            wrong("下满", "9 格下满、没人赢，网页收到的是 full=" + str(got["full"]) + "，赢家 " + shown(got["winner"]))
        done += ["两个人下", "点已经有棋子的格", "下满"]
    if STAGE >= 3:
        done.append("谁赢了")
    if STAGE >= 4:
        done.append("轮到谁")
    if STAGE >= 5:
        for computer_side, name in [('O', "你先下"), ('X', "电脑先下")]:
            got = ask("/api/new", {})
            while got.get("ok") and got["winner"] == '.' and not got["full"]:
                if got["turn"] == computer_side:
                    got = ask("/api/computer", {"board": got["board"]})
                else:
                    got = ask("/api/move", {"board": got["board"], "cell": got["board"].index('.')})
            if not got.get("ok"):
                fail(name, got)
        done += ["你先下", "电脑先下"]
    print("自检通过（第 " + str(STAGE) + " 关）：" + "、".join(done) + "都对。")


def main():
    server = HTTPServer(("127.0.0.1", 0), Handler)  # 端口写 0：让电脑自己挑一个空着的
    url = "http://127.0.0.1:" + str(server.server_address[1])
    if "--selftest" in sys.argv:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            self_test(url)
        finally:
            server.shutdown()
        return
    print("井字棋网页版（第 " + str(STAGE) + " 关）：" + url + "/")
    print("浏览器没有自己打开的话，把上面的网址复制到浏览器里。按 Ctrl+C 结束。")
    webbrowser.open(url + "/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("再见！")


main()
