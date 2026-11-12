# 第 5 关测试：电脑来下
# 老师提供，学生不用改。怎么运行见 guide.md。
# 最后一行是 OK：全部通过。最后一行是 FAILED：往上找 FAIL 的那几条，看中文说明和 AssertionError 后面的“你的 != 应该的”。

import unittest
import sys

for stream in (sys.stdout, sys.stderr):  # 有的电脑的控制台显示不了中文，换成 UTF-8；学生不用管
    try:
        "中文".encode(stream.encoding or "ascii")
    except (LookupError, UnicodeEncodeError):
        stream.reconfigure(encoding="utf-8")

from tictactoe import computer_move


class TestStage5(unittest.TestCase):

    def test_01(self):
        """轮到 X：下 2 号格就赢"""
        self.assertEqual(computer_move("XX.OO...."), 2, "轮到 X：下 2 号格就赢")

    def test_02(self):
        """轮到 O：下 2 号格就赢"""
        self.assertEqual(computer_move("OO.XX.X.."), 2, "轮到 O：下 2 号格就赢")

    def test_03(self):
        """轮到 O：X 下 2 号格就赢了，要堵住 2"""
        self.assertEqual(computer_move("XX..O...."), 2, "轮到 O：X 下 2 号格就赢了，要堵住 2")

    def test_04(self):
        """轮到 O：要堵住斜线的 8 号格"""
        self.assertEqual(computer_move("X...X..O."), 8, "轮到 O：要堵住斜线的 8 号格")

    def test_05(self):
        """轮到 O：自己能赢（5 号格）比堵对方（2 号格）更要紧"""
        self.assertEqual(computer_move("XX.OO.X.."), 5, "轮到 O：自己能赢（5 号格）比堵对方（2 号格）更要紧")

    def test_06(self):
        """没有要赢、要堵的：下第一个空格"""
        self.assertEqual(computer_move("X........"), 1, "没有要赢、要堵的：下第一个空格")

    def test_07(self):
        """空棋盘：下 0 号格"""
        self.assertEqual(computer_move("........."), 0, "空棋盘：下 0 号格")

    def test_08(self):
        """轮到 O：X 下 6 或 8 都会赢，先堵编号小的 6"""
        self.assertEqual(computer_move("XOXOX...."), 6, "轮到 O：X 下 6 或 8 都会赢，先堵编号小的 6")


if __name__ == "__main__":
    unittest.main(verbosity=2)
