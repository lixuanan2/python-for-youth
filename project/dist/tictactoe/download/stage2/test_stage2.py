# 第 2 关测试：下一步棋
# 老师提供，学生不用改。怎么运行见 guide.md。
# 最后一行是 OK：全部通过。最后一行是 FAILED：往上找 FAIL 的那几条，看中文说明和 AssertionError 后面的“你的 != 应该的”。

import unittest
import sys

for stream in (sys.stdout, sys.stderr):  # 有的电脑的控制台显示不了中文，换成 UTF-8；学生不用管
    try:
        "中文".encode(stream.encoding or "ascii")
    except (LookupError, UnicodeEncodeError):
        stream.reconfigure(encoding="utf-8")

from tictactoe import put


class TestStage2(unittest.TestCase):

    def test_01(self):
        """在空棋盘中间下 X"""
        self.assertEqual(put(".........", 4, 'X'), "....X....", "在空棋盘中间下 X")

    def test_02(self):
        """在 0 号格下 O"""
        self.assertEqual(put(".........", 0, 'O'), "O........", "在 0 号格下 O")

    def test_03(self):
        """在 8 号格下 O，0 号格的 X 不能动"""
        self.assertEqual(put("X........", 8, 'O'), "X.......O", "在 8 号格下 O，0 号格的 X 不能动")

    def test_04(self):
        """下完以后其他格子都不变"""
        self.assertEqual(put("XO.XO....", 6, 'X'), "XO.XO.X..", "下完以后其他格子都不变")


if __name__ == "__main__":
    unittest.main(verbosity=2)
