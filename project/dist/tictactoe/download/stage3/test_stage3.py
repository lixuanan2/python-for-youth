# 第 3 关测试：谁赢了
# 老师提供，学生不用改。怎么运行见 guide.md。
# 最后一行是 OK：全部通过。最后一行是 FAILED：往上找 FAIL 的那几条，看中文说明和 AssertionError 后面的“你的 != 应该的”。

import unittest
from tictactoe import line_owner, winner


class TestStage3(unittest.TestCase):

    def test_01(self):
        """0 1 2 三格都是 X"""
        self.assertEqual(line_owner("XXX......", 0, 1, 2), 'X', "0 1 2 三格都是 X")

    def test_02(self):
        """0 1 2 不一样，没人占"""
        self.assertEqual(line_owner("XXO......", 0, 1, 2), '.', "0 1 2 不一样，没人占")

    def test_03(self):
        """三格都是空的，不算谁占"""
        self.assertEqual(line_owner(".........", 0, 1, 2), '.', "三格都是空的，不算谁占")

    def test_04(self):
        """0 3 6 三格都是 O"""
        self.assertEqual(line_owner("O..O..O..", 0, 3, 6), 'O', "0 3 6 三格都是 O")

    def test_05(self):
        """斜线 0 4 8 都是 X"""
        self.assertEqual(line_owner("X...X...X", 0, 4, 8), 'X', "斜线 0 4 8 都是 X")

    def test_06(self):
        """第一横排 O 赢"""
        self.assertEqual(winner("OOO.X.X.."), 'O', "第一横排 O 赢")

    def test_07(self):
        """第二横排 X 赢"""
        self.assertEqual(winner("...XXX.O."), 'X', "第二横排 X 赢")

    def test_08(self):
        """差一点但没人赢"""
        self.assertEqual(winner("O.XO.XX.."), '.', "差一点但没人赢")

    def test_09(self):
        """中间一竖 O 赢"""
        self.assertEqual(winner(".O..O..O."), 'O', "中间一竖 O 赢")

    def test_10(self):
        """斜线 0 4 8 X 赢"""
        self.assertEqual(winner("X...X...X"), 'X', "斜线 0 4 8 X 赢")

    def test_11(self):
        """斜线 2 4 6 O 赢"""
        self.assertEqual(winner("..O.O.O.."), 'O', "斜线 2 4 6 O 赢")

    def test_12(self):
        """最下面一横排 X 赢"""
        self.assertEqual(winner("......XXX"), 'X', "最下面一横排 X 赢")

    def test_13(self):
        """下满了也没人赢，是平局"""
        self.assertEqual(winner("XOXXOOOXX"), '.', "下满了也没人赢，是平局")

    def test_14(self):
        """空棋盘没人赢"""
        self.assertEqual(winner("........."), '.', "空棋盘没人赢")


if __name__ == "__main__":
    unittest.main(verbosity=2)
