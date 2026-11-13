# 井字棋 —— 老师的网页版前端（第 5 关）。学生不用改，也不用看懂。
# 先运行 test_stage5.py，全部通过以后再运行这个文件：它会打开浏览器，在网页上点格子下棋。
# 它和 play.py 用的是同一组函数：can_put、put、winner、is_full、turn、computer_move。
# 画面从终端换成了网页，你写的 tictactoe.py 一行都不用改。
# 网页在 web 文件夹里，图片在 web/assets：board.png 是棋盘，x.png、o.png 是棋子。换成自己画的也行，文件名不变就好。
#
# 网页和这个文件怎么说话（以后别的语言的后端照这一套做）：
#   POST /api/new        发 {}                              回一个空棋盘
#   POST /api/move       发 {"board": "X........", "cell": 4}  轮到谁（turn）就替谁下在 cell
#   POST /api/computer   发 {"board": "X........"}           电脑下一步（computer_move）
#   回的都是 JSON：
#     {"ok": true, "board": "X...O....", "cell": 4, "turn": "X", "winner": ".", "full": false}
#     {"ok": false, "message": "这一格不能下，换一格。", "board": ...}          点了不能下的格
#     {"ok": false, "error": "先让 test_stage5.py 全部通过。", "detail": "...", "board": ...}  你的函数出错了
#   输赢、平局、轮到谁，全由你的函数说了算；网页只负责画出来和收点击。
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

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
HINT = "先让 test_stage5.py 全部通过。"
TYPES = {".html": "text/html; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml", ".css": "text/css", ".js": "text/javascript"}


class Trouble(Exception):
    # 你的函数出错了，或者还回来的东西不对
    pass


def call(function, *args):
    # 调用你写的函数；出错时找出是 tictactoe.py 的哪一行
    try:
        return function(*args)
    except Exception as e:
        where = function.__name__
        for frame in traceback.extract_tb(e.__traceback__):
            if frame.filename.endswith("tictactoe.py"):
                where = "tictactoe.py 第 " + str(frame.lineno) + " 行：" + (frame.line or "")
        raise Trouble(where + "（" + type(e).__name__ + ": " + str(e) + "）")


def check_board(board, name):
    if type(board) != str or len(board) != 9 or any(c not in "XO." for c in board):
        raise Trouble(name + " 还回来的不是 9 个字符的棋盘：" + repr(board))
    return board


def state(board, cell=-1):
    # 下完一步以后的样子：轮到谁、谁赢了、下满没有，都问你的函数
    answer = {"ok": True, "board": board, "cell": cell, "winner": call(t.winner, board), "full": call(t.is_full, board)}
    answer["turn"] = call(t.turn, board)
    return answer


def move(board, cell):
    if not call(t.can_put, board, cell):
        return {"ok": False, "message": "这一格不能下，换一格。", "board": board}
    board = check_board(call(t.put, board, cell, call(t.turn, board)), "put")
    return state(board, cell)


def computer(board):
    cell = call(t.computer_move, board)
    if type(cell) != int or not call(t.can_put, board, cell):
        raise Trouble("computer_move 还了 " + repr(cell) + "，这一格不能下")
    board = check_board(call(t.put, board, cell, call(t.turn, board)), "put")
    return state(board, cell)


def answer(path, asked):
    board = str(asked.get("board", "........."))
    try:
        if path == "/api/new":
            return state(".........")
        if path == "/api/move":
            return move(check_board(board, "网页"), int(asked.get("cell", -1)))
        if path == "/api/computer":
            return computer(check_board(board, "网页"))
        return {"ok": False, "message": "没有这个接口：" + path, "board": board}
    except Trouble as e:
        return {"ok": False, "error": HINT, "detail": str(e), "board": board}


class Handler(BaseHTTPRequestHandler):
    # http.server 要求这样写一个类；里面只有两件事：送网页文件、回答网页的问题
    def do_GET(self):
        name = "index.html" if self.path in ("/", "/index.html") else self.path.lstrip("/")
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
    # 老师检查用：python play_web.py --selftest。不开浏览器，像网页一样按接口下完几局
    import urllib.request

    def ask(path, asked):
        request = urllib.request.Request(url + path, json.dumps(asked).encode("utf-8"), {"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(request, timeout=10).read().decode("utf-8"))

    def fail(name, got):
        print("自检没通过（" + name + "）：" + got.get("error", got.get("message", "")) + " " + got.get("detail", ""))
        sys.exit(1)

    page = urllib.request.urlopen(url + "/", timeout=10).read().decode("utf-8")
    pictures = [urllib.request.urlopen(url + "/assets/" + name, timeout=10).read() for name in ("board.png", "x.png", "o.png")]
    if "井字棋" not in page or any(not p.startswith(b"\x89PNG") for p in pictures):
        print("自检没通过：网页或图片打不开")
        sys.exit(1)
    got = ask("/api/new", {})
    for cell in [0, 3, 1, 4, 2]:
        got = ask("/api/move", {"board": got["board"], "cell": cell})
    if got.get("winner") != 'X':
        fail("两个人下", got)
    if ask("/api/move", {"board": "....X....", "cell": 4}).get("message") != "这一格不能下，换一格。":
        fail("点已经有棋子的格", {})
    for computer_side, name in [('O', "你先下"), ('X', "电脑先下")]:
        got = ask("/api/new", {})
        while got.get("ok") and got["winner"] == '.' and not got["full"]:
            if got["turn"] == computer_side:
                got = ask("/api/computer", {"board": got["board"]})
            else:
                got = ask("/api/move", {"board": got["board"], "cell": got["board"].index('.')})
        if not got.get("ok"):
            fail(name, got)
    print("自检通过：网页、3 张图片，两个人下、点已经有棋子的格、你先下、电脑先下都对。")


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
    print("井字棋网页版：" + url + "/")
    print("浏览器没有自己打开的话，把上面的网址复制到浏览器里。按 Ctrl+C 结束。")
    webbrowser.open(url + "/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("再见！")


main()
