# 第 1 关测试：这一格能下吗
# 老师提供，学生不用改。怎么运行见 guide.md。
# 最后一行是 OK：全部通过。最后一行是 FAILED：往上找 FAIL 的那几条，看中文说明和 AssertionError 后面的“你的 != 应该的”。

import unittest
from tictactoe import can_put


class TestStage1(unittest.TestCase):

    def test_01(self):
        """空棋盘的 4 号格可以下"""
        self.assertEqual(can_put(".........", 4), True, "空棋盘的 4 号格可以下")

    def test_02(self):
        """空棋盘的 0 号格可以下"""
        self.assertEqual(can_put(".........", 0), True, "空棋盘的 0 号格可以下")

    def test_03(self):
        """空棋盘的 8 号格可以下"""
        self.assertEqual(can_put(".........", 8), True, "空棋盘的 8 号格可以下")

    def test_04(self):
        """0 号格已经有 X，不能下"""
        self.assertEqual(can_put("X........", 0), False, "0 号格已经有 X，不能下")

    def test_05(self):
        """4 号格已经有 O，不能下"""
        self.assertEqual(can_put("....O....", 4), False, "4 号格已经有 O，不能下")

    def test_06(self):
        """只剩 8 号格是空的，可以下"""
        self.assertEqual(can_put("XOXOXOXO.", 8), True, "只剩 8 号格是空的，可以下")

    def test_07(self):
        """没有 9 号格，不能下"""
        self.assertEqual(can_put(".........", 9), False, "没有 9 号格，不能下")

    def test_08(self):
        """没有 -1 号格，不能下"""
        self.assertEqual(can_put(".........", -1), False, "没有 -1 号格，不能下")


if __name__ == "__main__":
    unittest.main(verbosity=2)
