# Python 青少年编程

给小学高年级和初中生的 Python 课。课件是可以离线双击打开的网页：学生看着能自学，老师照着能讲课，代码能一键带到在线 IDE 里运行。

在线看：<https://lixuanan2.github.io/python-for-youth/>

## 上课

双击 `dist/index.html`，选一节课。

| 按键 | 作用 |
| --- | --- |
| `→` `空格` | 下一步，有分步的页面先走完步骤 |
| `←` | 上一步 |
| `T` | 显示或收起左侧缩略图 |
| `G` | 输入页码跳转 |
| `R` | 带着本页代码打开 IDE |
| `I` | IDE 设置：主题、布局、打开后是否自动运行 |
| `F` | 全屏，全屏时动一下鼠标显示控制条 |
| `B` | 黑屏，按任意键回来 |
| `1`–`4` | 小测选答案 |
| `?` | 查看快捷键 |

底部时间轴一格一页，颜色表示这页的任务，可以拖动，旁边是章节跳转。

上课时把整个 `dist/` 复制到教室电脑，里面有课件和起始程序，没有答案。IDE 按钮要联网，第一次打开要等十几秒，其余功能离线可用。

## 课程

| 课 | 主题 | 页数 | 状态 |
| --- | --- | --- | --- |
| [01](dist/01-input-output/index.html) | 输入输出 | 28 | macOS Chrome 已验证，Windows 教室待试讲 |
| [02](dist/02-variables/index.html) | 变量与数据类型 | 28 | macOS Chrome 已验证，Windows 教室待试讲 |
| [03](dist/03-arithmetic/index.html) | 算术运算 | 28 | macOS Chrome 已验证，Windows 教室待试讲 |
| [04](dist/04-conditions/index.html) | 条件判断 | 25 | macOS Chrome 已验证，Windows 教室待试讲 |
| [05](dist/05-logic/index.html) | 逻辑运算 | 28 | macOS Chrome 已验证，Windows 教室待试讲 |
| [06](dist/06-for-loop/index.html) | for 循环 | 29 | macOS Chrome 已验证，Windows 教室待试讲 |
| [07](dist/07-while-loop/index.html) | while 循环 | 24 | macOS Chrome 已验证，Windows 教室待试讲 |
| [08](dist/08-loop-tally/index.html) | 累加和计数 | 24 | macOS Chrome 已验证，Windows 教室待试讲 |
| [09](dist/09-max-min/index.html) | 最大值和最小值 | 21 | macOS Chrome 已验证，Windows 教室待试讲 |
| [10](dist/10-list-basics/index.html) | 列表基础 | 24 | macOS Chrome 已验证，Windows 教室待试讲 |
| [11](dist/11-list-loop/index.html) | 列表遍历 | 21 | macOS Chrome 已验证，Windows 教室待试讲 |
| [12](dist/12-string-basics/index.html) | 字符串基础 | 24 | macOS Chrome 已验证，Windows 教室待试讲 |
| [13](dist/13-string-methods/index.html) | 字符串常用方法 | 22 | macOS Chrome 已验证，Windows 教室待试讲 |
| [14](dist/14-functions/index.html) | 函数定义与调用 | 21 | macOS Chrome 已验证，Windows 教室待试讲 |
| [15](dist/15-params-return/index.html) | 参数与返回值 | 22 | macOS Chrome 已验证，Windows 教室待试讲 |
| [16](dist/16-math-functions/index.html) | 常用数学函数 | 21 | macOS Chrome 已验证，Windows 教室待试讲 |
| [17](dist/17-dict-basics/index.html) | 字典基础 | 21 | macOS Chrome 已验证，Windows 教室待试讲 |
| [18](dist/18-nested-loops/index.html) | 嵌套循环与图形 | 22 | macOS Chrome 已验证，Windows 教室待试讲 |
| [19](dist/19-list-tools/index.html) | 列表常用操作 | 21 | macOS Chrome 已验证，Windows 教室待试讲 |
| [20](dist/20-2d-lists/index.html) | 二维列表 | 20 | macOS Chrome 已验证，Windows 教室待试讲 |
| [21](dist/21-random-games/index.html) | 随机数与小游戏 | 19 | macOS Chrome 已验证，Windows 教室待试讲 |
| [22](dist/22-try-except/index.html) | 接住报错：try 和 except | 20 | macOS Chrome 已验证，Windows 教室待试讲 |
| [23](dist/23-recursion/index.html) | 递归入门 | 18 | macOS Chrome 已验证，Windows 教室待试讲 |
| [24](dist/24-bubble-sort/index.html) | 冒泡排序 | 19 | macOS Chrome 已验证，Windows 教室待试讲 |
| [25](dist/25-enumeration/index.html) | 枚举：把可能都试一遍 | 18 | macOS Chrome 已验证，Windows 教室待试讲 |
| [26](dist/26-binary-search/index.html) | 二分查找 | 17 | macOS Chrome 已验证，Windows 教室待试讲 |

## 做新课

在 Claude Code 里说“做下一课：if 判断”，会走 [python-lesson](.claude/skills/python-lesson/SKILL.md) 流程。用别的 AI 时，把 [PROMPT.md](PROMPT.md) 发过去。

一节课页面太多时分成上下集，规则见 [PROMPT.md](PROMPT.md)。手动改课后，在仓库根目录运行：

```sh
python3 tools/build.py
python3 tools/check.py
node tools/check_browser.mjs
```

打印 PDF 用 `python3 tools/build.py --pdf`，需要装 Chrome。

## 目录

```text
lessons/    每节课的页面、题目和测试，唯一内容源
template/   所有课共用的外壳、样式和脚本
tools/      构建和检查
dist/       生成结果，复制它去上课
vendor/     字体和舞台样式，含许可
site.json   网站名称、语言和 IDE 平台
PROMPT.md   做课提示词和教学要求
AGENTS.md   项目规则
```

## 教学设计

每节课按“讲一点、练一点”推进，最后留一个没有标准答案的小项目，再和同桌互相试玩、改一版。课堂结构以 [PROMPT.md](PROMPT.md) 为准；设计时参考过 MIT Media Lab 的[创意学习](https://www.media.mit.edu/groups/lifelong-kindergarten/overview/)。

## 参与

欢迎提意见和改进，怎么提看 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可

课件内容用 CC BY-NC-SA 4.0，代码用 MIT，详见 [LICENSE.md](LICENSE.md)。

## 致谢

- 固定舞台样式来自 [Frontend Slides](https://github.com/zarazhangrui/frontend-slides)（MIT）。
- 字体 [JetBrains Mono](https://www.jetbrains.com/lp/mono/)（SIL OFL 1.1）。
- 在线 IDE 使用 [JupyterLite](https://jupyterlite.readthedocs.io/) 的公开演示站，学生代码在浏览器里运行，但会放在打开的链接地址中。
