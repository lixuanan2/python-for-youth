# 第 4 关测试：下满没有、轮到谁
# 老师提供，学生不用改。怎么运行见 guide.md。
# 最后一行是 OK：全部通过。最后一行是 FAILED：往上找 FAIL 的那几条，看中文说明和 AssertionError 后面的“你的 != 应该的”。

import unittest
import sys

for stream in (sys.stdout, sys.stderr):  # 有的电脑的控制台显示不了中文，换成 UTF-8；学生不用管
    try:
        "中文".encode(stream.encoding or "ascii")
    except (LookupError, UnicodeEncodeError):
        stream.reconfigure(encoding="utf-8")

from tictactoe import is_full, turn


class TestStage4(unittest.TestCase):

    def test_01(self):
        """空棋盘没下满"""
        self.assertEqual(is_full("........."), False, "空棋盘没下满")

    def test_02(self):
        """9 格都有子，下满了"""
        self.assertEqual(is_full("XOXXOOOXX"), True, "9 格都有子，下满了")

    def test_03(self):
        """还剩 8 号格，没下满"""
        self.assertEqual(is_full("XOXXOOOX."), False, "还剩 8 号格，没下满")

    def test_04(self):
        """还剩 0 号格，没下满"""
        self.assertEqual(is_full(".OXXOOOXX"), False, "还剩 0 号格，没下满")

    def test_05(self):
        """开局 X 先下"""
        self.assertEqual(turn("........."), 'X', "开局 X 先下")

    def test_06(self):
        """X 下了一步，轮到 O"""
        self.assertEqual(turn("X........"), 'O', "X 下了一步，轮到 O")

    def test_07(self):
        """一人一步，轮到 X"""
        self.assertEqual(turn("XO......."), 'X', "一人一步，轮到 X")

    def test_08(self):
        """X 两步、O 一步，轮到 O"""
        self.assertEqual(turn("X.O.X...."), 'O', "X 两步、O 一步，轮到 O")

    def test_09(self):
        """各三步，轮到 X"""
        self.assertEqual(turn("XOXOXO..."), 'X', "各三步，轮到 X")


if __name__ == "__main__":
    unittest.main(verbosity=2)
