# 井字棋：每一关的函数、说明、占位、参考答案、测试用例、引导文档内容。
# project/tools/build.py 读这个文件，生成发给学生的关卡文件夹、老师的参考答案和课件里的规格页。
# 改内容只改这里（和 slides/、templates/），再运行 build.py。两门课共用这个格式：C++ 的字段 Python 课不用，留着给 C++ 课。

# 每个函数：
#   name     函数名（两门语言一样）
#   py_sig / cpp_sig   函数头
#   doc      中文说明（两门语言共用，生成注释）
#   py_stub / cpp_stub 起始程序里的占位（故意是错的，但不会崩溃）
#   py_body / cpp_body 参考答案
# 每条测试：(函数名, 参数列表, 应该的结果, 中文说明)
#   参数和结果用 Python 写法：字符串 "…"、字符 ('c', 'X')、布尔 True/False、整数

def ch(c):
    return ("c", c)


STAGES = [
    # ------------------------------------------------------------ 第 1 关
    {
        "id": 1,
        "title": "这一格能下吗",
        "minutes": "约 1 节课（45 分钟）：其中 15 分钟认识项目、文件夹和怎么运行测试",
        "needs_py": ["04-conditions 条件判断", "05-logic 逻辑运算", "12-string-basics 字符串基础（下标）", "15-params-return 参数与返回值"],
        "needs_cpp": ["03-if-else 比较与 if/else", "05-logic 逻辑运算与复合条件", "16-string string 字符串入门（下标）", "17-function 函数定义与调用"],
        "goal": "写一个函数，判断棋盘上的某一格现在能不能下棋。",
        "functions": [
            {
                "name": "can_put",
                "py_sig": "def can_put(board, i):",
                "cpp_sig": "bool can_put(string board, int i) {",
                "doc": [
                    "给它：棋盘 board（9 个字符），格子编号 i",
                    "还给你：第 i 格能不能下，能就是 True，不能就是 False",
                    "能下要同时满足两条：i 在 0 到 8 之间；board[i] 是 '.'",
                    "注意：先查 i 在不在 0 到 8，再看 board[i]，不然会超出字符串",
                    "例子：can_put(\".........\", 4) 还 True",
                    "      can_put(\"X........\", 0) 还 False（已经有子了）",
                    "      can_put(\".........\", 9) 还 False（没有第 9 格）",
                ],
                "py_stub": ["    return False"],
                "cpp_stub": ["    return false;"],
                "py_body": [
                    "    if i < 0 or i > 8:",
                    "        return False",
                    "    return board[i] == '.'",
                ],
                "cpp_body": [
                    "    if (i < 0 || i > 8) {",
                    "        return false;",
                    "    }",
                    "    return board[i] == '.';",
                ],
            },
        ],
        "tests": [
            ("can_put", [".........", 4], True, "空棋盘的 4 号格可以下"),
            ("can_put", [".........", 0], True, "空棋盘的 0 号格可以下"),
            ("can_put", [".........", 8], True, "空棋盘的 8 号格可以下"),
            ("can_put", ["X........", 0], False, "0 号格已经有 X，不能下"),
            ("can_put", ["....O....", 4], False, "4 号格已经有 O，不能下"),
            ("can_put", ["XOXOXOXO.", 8], True, "只剩 8 号格是空的，可以下"),
            ("can_put", [".........", 9], False, "没有 9 号格，不能下"),
            ("can_put", [".........", -1], False, "没有 -1 号格，不能下"),
        ],
    },
    # ------------------------------------------------------------ 第 2 关
    {
        "id": 2,
        "title": "下一步棋",
        "minutes": "约半节课",
        "minutes_cpp": "约半节到 1 节课：先讲补页“改 string 的一格”（约 10 分钟），再写函数",
        "needs_py": ["12-string-basics 字符串基础（切片）", "15-params-return 参数与返回值"],
        "needs_cpp": ["16-string string 字符串入门", "17-function 函数定义与调用", "18-scope 函数参数与作用域（参数是副本）"],
        "goal": "写一个函数，在棋盘的某一格放上一个棋子，还回去新的棋盘。",
        "functions": [
            {
                "name": "put",
                "py_sig": "def put(board, i, who):",
                "cpp_sig": "string put(string board, int i, char who) {",
                "doc": [
                    "给它：棋盘 board、格子编号 i（可以放心：0 到 8，而且是空格）、棋子 who（'X' 或 'O'）",
                    "还给你：下完以后的新棋盘，还是 9 个字符",
                    "PY: 提示：字符串不能直接改一个字。用第 12 课的切片，把第 i 格前面的部分、who、第 i 格后面的部分拼起来",
                    "CPP: 提示：先看补页 extra-string-cell.md，string 的一格怎么改；交进来的 board 是副本，改好以后要还回去",
                    "例子：put(\".........\", 4, 'X') 还 \"....X....\"",
                    "      put(\"X........\", 8, 'O') 还 \"X.......O\"",
                ],
                "py_stub": ["    return board"],
                "cpp_stub": ["    return board;"],
                "py_body": [
                    "    return board[:i] + who + board[i + 1:]",
                ],
                "cpp_body": [
                    "    board[i] = who;",
                    "    return board;",
                ],
            },
        ],
        "tests": [
            ("put", [".........", 4, ch("X")], "....X....", "在空棋盘中间下 X"),
            ("put", [".........", 0, ch("O")], "O........", "在 0 号格下 O"),
            ("put", ["X........", 8, ch("O")], "X.......O", "在 8 号格下 O，0 号格的 X 不能动"),
            ("put", ["XO.XO....", 6, ch("X")], "XO.XO.X..", "下完以后其他格子都不变"),
        ],
    },
    # ------------------------------------------------------------ 第 3 关
    {
        "id": 3,
        "title": "谁赢了",
        "minutes": "约 1 节课",
        "needs_py": ["05-logic 逻辑运算（and）", "10-list-basics 列表基础", "11-list-loop 列表遍历", "15-params-return 参数与返回值（函数里调用函数）"],
        "needs_cpp": ["05-logic 逻辑运算与复合条件（&&）", "12-array 一维数组入门", "17-function 函数定义与调用（函数里调用函数）"],
        "goal": "先写一个查“一条线”的小函数，再用它查全部 8 条线，找出赢家。",
        "functions": [
            {
                "name": "line_owner",
                "py_sig": "def line_owner(board, a, b, c):",
                "cpp_sig": "char line_owner(string board, int a, int b, int c) {",
                "doc": [
                    "给它：棋盘，和一条线上的三个格子编号 a、b、c",
                    "还给你：三格都是 'X' 就还 'X'，三格都是 'O' 就还 'O'，不然还 '.'",
                    "例子：line_owner(\"XXX......\", 0, 1, 2) 还 'X'",
                    "      line_owner(\"XXO......\", 0, 1, 2) 还 '.'",
                    "      line_owner(\"O..O..O..\", 0, 3, 6) 还 'O'",
                ],
                "py_stub": ["    return '.'"],
                "cpp_stub": ["    return '.';"],
                "py_body": [
                    "    if board[a] != '.' and board[a] == board[b] and board[b] == board[c]:",
                    "        return board[a]",
                    "    return '.'",
                ],
                "cpp_body": [
                    "    if (board[a] != '.' && board[a] == board[b] && board[b] == board[c]) {",
                    "        return board[a];",
                    "    }",
                    "    return '.';",
                ],
            },
            {
                "name": "winner",
                "py_sig": "def winner(board):",
                "cpp_sig": "char winner(string board) {",
                "doc": [
                    "给它：棋盘",
                    "还给你：赢的一方 'X' 或 'O'；没人赢就还 '.'",
                    "一共 8 条线：横 0 1 2、3 4 5、6 7 8；竖 0 3 6、1 4 7、2 5 8；斜 0 4 8、2 4 6",
                    "PY: 提示：把 8 条线的 line_owner 结果放进一个列表，再找出不是 '.' 的那个",
                    "CPP: 提示：把 8 条线的 line_owner 结果放进一个 char 数组，再找出不是 '.' 的那个",
                    "例子：winner(\"OOO.X.X..\") 还 'O'",
                    "      winner(\"X...X...X\") 还 'X'",
                    "      winner(\"XOXXOOOXX\") 还 '.'（下满了，平局）",
                ],
                "py_stub": ["    return '.'"],
                "cpp_stub": ["    return '.';"],
                "py_body": [
                    "    owners = [line_owner(board, 0, 1, 2), line_owner(board, 3, 4, 5),",
                    "              line_owner(board, 6, 7, 8), line_owner(board, 0, 3, 6),",
                    "              line_owner(board, 1, 4, 7), line_owner(board, 2, 5, 8),",
                    "              line_owner(board, 0, 4, 8), line_owner(board, 2, 4, 6)]",
                    "    result = '.'",
                    "    for w in owners:",
                    "        if w != '.':",
                    "            result = w",
                    "    return result",
                ],
                "cpp_body": [
                    "    char owners[8] = {line_owner(board, 0, 1, 2), line_owner(board, 3, 4, 5),",
                    "                      line_owner(board, 6, 7, 8), line_owner(board, 0, 3, 6),",
                    "                      line_owner(board, 1, 4, 7), line_owner(board, 2, 5, 8),",
                    "                      line_owner(board, 0, 4, 8), line_owner(board, 2, 4, 6)};",
                    "    char result = '.';",
                    "    for (int k = 0; k < 8; k++) {",
                    "        if (owners[k] != '.') {",
                    "            result = owners[k];",
                    "        }",
                    "    }",
                    "    return result;",
                ],
            },
        ],
        "tests": [
            ("line_owner", ["XXX......", 0, 1, 2], ch("X"), "0 1 2 三格都是 X"),
            ("line_owner", ["XXO......", 0, 1, 2], ch("."), "0 1 2 不一样，没人占"),
            ("line_owner", [".........", 0, 1, 2], ch("."), "三格都是空的，不算谁占"),
            ("line_owner", ["O..O..O..", 0, 3, 6], ch("O"), "0 3 6 三格都是 O"),
            ("line_owner", ["X...X...X", 0, 4, 8], ch("X"), "斜线 0 4 8 都是 X"),
            ("winner", ["OOO.X.X.."], ch("O"), "第一横排 O 赢"),
            ("winner", ["...XXX.O."], ch("X"), "第二横排 X 赢"),
            ("winner", ["O.XO.XX.."], ch("."), "差一点但没人赢"),
            ("winner", [".O..O..O."], ch("O"), "中间一竖 O 赢"),
            ("winner", ["X...X...X"], ch("X"), "斜线 0 4 8 X 赢"),
            ("winner", ["..O.O.O.."], ch("O"), "斜线 2 4 6 O 赢"),
            ("winner", ["......XXX"], ch("X"), "最下面一横排 X 赢"),
            ("winner", ["XOXXOOOXX"], ch("."), "下满了也没人赢，是平局"),
            ("winner", ["........."], ch("."), "空棋盘没人赢"),
        ],
    },
    # ------------------------------------------------------------ 第 4 关
    {
        "id": 4,
        "title": "下满没有、轮到谁",
        "minutes": "约半节到 1 节课；做完就能两个人对战",
        "needs_py": ["08-loop-tally 累加和计数", "13-string-methods 字符串常用方法（count）", "15-params-return 参数与返回值"],
        "needs_cpp": ["06-for-loop for 循环", "09-tally 累加和计数", "17-function 函数定义与调用"],
        "goal": "写两个小函数：棋盘下满了没有；现在轮到谁下。",
        "functions": [
            {
                "name": "is_full",
                "py_sig": "def is_full(board):",
                "cpp_sig": "bool is_full(string board) {",
                "doc": [
                    "给它：棋盘",
                    "还给你：9 格都下满了吗（一个 '.' 都没有了）",
                    "例子：is_full(\"XOXXOOOXX\") 还 True",
                    "      is_full(\"XOXXOOOX.\") 还 False",
                ],
                "py_stub": ["    return False"],
                "cpp_stub": ["    return false;"],
                "py_body": [
                    "    return board.count('.') == 0",
                ],
                "cpp_body": [
                    "    int empty = 0;",
                    "    for (int i = 0; i < 9; i++) {",
                    "        if (board[i] == '.') {",
                    "            empty++;",
                    "        }",
                    "    }",
                    "    return empty == 0;",
                ],
            },
            {
                "name": "turn",
                "py_sig": "def turn(board):",
                "cpp_sig": "char turn(string board) {",
                "doc": [
                    "给它：棋盘（可以放心：X 先下，两人轮流）",
                    "还给你：现在轮到谁下，'X' 或 'O'",
                    "X 和 O 一样多，轮到 X；X 比 O 多一个，轮到 O",
                    "例子：turn(\".........\") 还 'X'",
                    "      turn(\"X........\") 还 'O'",
                    "      turn(\"XO.......\") 还 'X'",
                ],
                "py_stub": ["    return 'X'"],
                "cpp_stub": ["    return 'X';"],
                "py_body": [
                    "    if board.count('X') == board.count('O'):",
                    "        return 'X'",
                    "    return 'O'",
                ],
                "cpp_body": [
                    "    int x = 0;",
                    "    int o = 0;",
                    "    for (int i = 0; i < 9; i++) {",
                    "        if (board[i] == 'X') {",
                    "            x++;",
                    "        }",
                    "        if (board[i] == 'O') {",
                    "            o++;",
                    "        }",
                    "    }",
                    "    if (x == o) {",
                    "        return 'X';",
                    "    }",
                    "    return 'O';",
                ],
            },
        ],
        "tests": [
            ("is_full", ["........."], False, "空棋盘没下满"),
            ("is_full", ["XOXXOOOXX"], True, "9 格都有子，下满了"),
            ("is_full", ["XOXXOOOX."], False, "还剩 8 号格，没下满"),
            ("is_full", [".OXXOOOXX"], False, "还剩 0 号格，没下满"),
            ("turn", ["........."], ch("X"), "开局 X 先下"),
            ("turn", ["X........"], ch("O"), "X 下了一步，轮到 O"),
            ("turn", ["XO......."], ch("X"), "一人一步，轮到 X"),
            ("turn", ["X.O.X...."], ch("O"), "X 两步、O 一步，轮到 O"),
            ("turn", ["XOXOXO..."], ch("X"), "各三步，轮到 X"),
        ],
    },
    # ------------------------------------------------------------ 第 5 关
    {
        "id": 5,
        "title": "电脑来下",
        "minutes": "约 1 到 1.5 节课；做完就能和电脑下",
        "needs_py": ["06-for-loop for 循环", "04-conditions 条件判断", "15-params-return 参数与返回值（用前面写好的函数）"],
        "needs_cpp": ["06-for-loop for 循环", "03-if-else 比较与 if/else", "17-function 函数定义与调用（用前面写好的函数）"],
        "goal": "让电脑下棋：能赢就赢，该堵就堵，不然下第一个空格。",
        "functions": [
            {
                "name": "computer_move",
                "py_sig": "def computer_move(board):",
                "cpp_sig": "int computer_move(string board) {",
                "doc": [
                    "给它：还没下完、也还没人赢的棋盘。电脑下的是 turn(board) 那一方",
                    "还给你：电脑要下的格子编号 0 到 8",
                    "按顺序想：",
                    "  1. 有没有一格，我下了就赢？有就下那里（有好几格，选编号最小的）",
                    "  2. 有没有一格，对方下了就赢？有就堵住那里（同样选编号最小的）",
                    "  3. 都没有，就下编号最小的空格",
                    "提示：试一格 = can_put 看能不能下，put 下一下，winner 看看谁赢。试完不用“拿走”，因为 put 还回去的是新棋盘",
                    "提示：没学 break，可以先让答案等于 -1，找到了再改；已经找到就不再改",
                    "例子：computer_move(\"XX.OO....\") 还 2（轮到 X，X 下 2 就赢）",
                    "      computer_move(\"XX..O....\") 还 2（轮到 O，O 要堵住 2）",
                    "      computer_move(\"X........\") 还 1（没有要赢、要堵的，下第一个空格）",
                ],
                "py_stub": ["    return -1"],
                "cpp_stub": ["    return -1;"],
                "py_body": [
                    "    me = turn(board)",
                    "    other = 'X'",
                    "    if me == 'X':",
                    "        other = 'O'",
                    "    move = -1",
                    "    for i in range(9):",
                    "        if move == -1 and can_put(board, i):",
                    "            if winner(put(board, i, me)) == me:",
                    "                move = i",
                    "    for i in range(9):",
                    "        if move == -1 and can_put(board, i):",
                    "            if winner(put(board, i, other)) == other:",
                    "                move = i",
                    "    for i in range(9):",
                    "        if move == -1 and can_put(board, i):",
                    "            move = i",
                    "    return move",
                ],
                "cpp_body": [
                    "    char me = turn(board);",
                    "    char other = 'X';",
                    "    if (me == 'X') {",
                    "        other = 'O';",
                    "    }",
                    "    int move = -1;",
                    "    for (int i = 0; i < 9; i++) {",
                    "        if (move == -1 && can_put(board, i)) {",
                    "            if (winner(put(board, i, me)) == me) {",
                    "                move = i;",
                    "            }",
                    "        }",
                    "    }",
                    "    for (int i = 0; i < 9; i++) {",
                    "        if (move == -1 && can_put(board, i)) {",
                    "            if (winner(put(board, i, other)) == other) {",
                    "                move = i;",
                    "            }",
                    "        }",
                    "    }",
                    "    for (int i = 0; i < 9; i++) {",
                    "        if (move == -1 && can_put(board, i)) {",
                    "            move = i;",
                    "        }",
                    "    }",
                    "    return move;",
                ],
            },
        ],
        "tests": [
            ("computer_move", ["XX.OO...."], 2, "轮到 X：下 2 号格就赢"),
            ("computer_move", ["OO.XX.X.."], 2, "轮到 O：下 2 号格就赢"),
            ("computer_move", ["XX..O...."], 2, "轮到 O：X 下 2 号格就赢了，要堵住 2"),
            ("computer_move", ["X...X..O."], 8, "轮到 O：要堵住斜线的 8 号格"),
            ("computer_move", ["XX.OO.X.."], 5, "轮到 O：自己能赢（5 号格）比堵对方（2 号格）更要紧"),
            ("computer_move", ["X........"], 1, "没有要赢、要堵的：下第一个空格"),
            ("computer_move", ["........."], 0, "空棋盘：下 0 号格"),
            ("computer_move", ["XOXOX...."], 6, "轮到 O：X 下 6 或 8 都会赢，先堵编号小的 6"),
        ],
    },
]


# ---------------------------------------------------------------- 整个项目

PROJECT = {
    "title": "井字棋",
    "module": "tictactoe",  # 学生改的文件：tictactoe.py / tictactoe.h
    "lead": "两个人轮流在 3×3 的格子里下 X 和 O，先连成一条线的赢。分 5 关，一关写一两个函数，最后能和电脑下。",
    "start": {"python": "15-params-return", "cpp": "17-function"},
}

BOARD_PICTURE = [
    "棋盘是 9 个字符的字符串，格子编号 0 到 8：",
    "",
    "     0 | 1 | 2",
    "    ---+---+---",
    "     3 | 4 | 5",
    "    ---+---+---",
    "     6 | 7 | 8",
    "",
    "'X' 和 'O' 是棋子，'.' 是空格。例如 \"X...O....\" 是 X 在 0 号格、O 在 4 号格。",
]

# 测试全过以后，前端能玩什么
PLAY_NOTES = {
    1: "第 1 关能做的不多：输入格子编号，看你的 `can_put` 怎么说。",
    2: "两个人可以轮流下了，但程序还不会判断输赢。",
    3: "两个人可以对战了，有人连成一条线就结束。",
    4: "轮到谁、下满没有，都用你自己写的函数来管了。",
    5: "选 2 或 3 就可以和电脑下！试试能不能赢它。",
}

# 做完了想一想（PY: 和 CPP: 用 | 分开时，两门语言各一句）
CHALLENGES = {
    1: "如果不先查 i 在不在 0 到 8，直接看 board[i]，输入 9 会发生什么？在 play 里试试（Python 会报错，C++ 结果是乱的）。",
    2: "PY: 不用切片，能不能用一个 for 循环，一格一格拼出新棋盘？|CPP: 不直接改 board[i]，能不能用一个 for 循环，一格一格拼出一个新的 string？",
    3: "如果棋盘上 X 和 O 都连成了一条线（真实对局不会这样），你的 winner 会还谁？为什么？",
    4: "如果有人偷偷连下两步，X 比 O 多两个，你的 turn 会还什么？要不要管这种情况？",
    5: "让电脑在“要赢”“要堵”都没有的时候，先抢中间的 4 号格。电脑会不会更难打败？（改完以后测试最后几条会不通过，这是正常的，想完改回来。）",
}

# verify：每关配参考答案，按这些按键玩一遍，输出里要有这些字
PLAYS = {
    1: [("1\n0\n4\n9\n-1\nabc\nq\n", ["还 True", "还 False"])],
    2: [("0\n1\n2\n3\n4\n5\n6\n7\n8\nn\n", ["下满了", "再见"])],
    3: [("0\n3\n1\n4\n2\nn\n", ["X 赢了", "再见"])],
    4: [("0\n1\n2\n4\n3\n5\n7\n6\n8\nn\n", ["平局", "再见"]),
        ("0\n3\n1\n4\n2\ny\n4\n0\n8\n1\n2\n6\n3\nn\n", ["X 赢了", "比分", "再见"])],
    5: [("1\n0\n3\n1\n4\n2\nn\n", ["X 赢了", "再见"]),
        ("2\n" + "0\n1\n2\n3\n4\n5\n6\n7\n8\n" * 3 + "n\n", ["电脑下在", "再见"]),
        ("3\n" + "0\n1\n2\n3\n4\n5\n6\n7\n8\n" * 3 + "n\n", ["电脑下在", "再见"])],
}
# 最后一关配起始程序（电脑还不会下）玩：按这些键，要有这句提示，不能崩溃
PLAY_UNFINISHED = ("3\nn\n", "这一格不能下")
