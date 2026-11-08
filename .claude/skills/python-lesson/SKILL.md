---
name: python-lesson
description: 做或修改 Python 少儿编程课件。老师说“做下一课”“做一节 XX 课”“改第几页”“迁移旧模块”时使用。
---

# 做一节 Python 课

先读 [PROMPT.md](../../../basics/PROMPT.md)，那里是全部教学要求。这里只规定操作顺序。一次只做一节课。

课都在“基础课件”模块 `basics/` 里。下面的路径都从 `basics/` 算起，命令也都在 `basics/` 里运行（从仓库最外层先 `cd basics`）。模块规则见 [basics/AGENTS.md](../../../basics/AGENTS.md)。

## 1. 定设计，等老师确认

读 `course.json` 和上一节课的 `slides.html`，确认学生已经学过什么。给老师一份大纲：每页一句话，标出小测、预测、追踪、找错和项目放在哪里。再读 [模块内容摘要](../../../basics/docs/module-baseline.md) 里这一节，需要细节时只读旧仓库的这一个模块。

大纲超过约 30 页时，主动提出在哪里分上下集。

**老师确认前不写文件。** 只改错字或单页时跳过这步。

## 2. 写程序和测试

新建 `lessons/<编号-英文名>/`，复制上一节的结构，在 `course.json` 给这节课补上 `id`、`tag` 和 `file`。分集时用 `05a-loops`、`05b-loops` 这样的文件夹，标题写“for 循环（上集）”，每集占一行。

- `solutions/`：答案，每个都要有测试。
- `starter/`：起始程序。小改写放例题代码，挑战只放注释。
- `tests/contracts.json`：普通和边界数据。
- `tests/claims.json`：页面上说过的输出和报错，含小测的每个选项。
- `tasks.json`：题目、角色（语法小演示、基础例题、学生小改写、独立迁移、创作项目）和页码。

## 3. 写页面

只在 `slides.html` 写 `<section class="slide">`。先从 `lessons/01-input-output/slides.html` 找现成写法，组件都在那里：

| 需要 | 写法 |
| --- | --- |
| 编辑器 | `.editor` + `.tab` + `pre.code data-file` + `.ln` |
| 语法高亮 | `.f` 函数，`.k` 关键字，`.s` 字符串，`.m` 数字 |
| 分步揭晓 | 页面加 `data-steps="3" data-at="3"`，元素加 `.step .s2`、`.only1`，行加 `.l1` |
| 选择小测 | `.quiz data-right="序号"`，选项加 `data-fb`，后面放 `.fb` |
| 点行找错 | `pre.code.pick data-bug data-yes data-no`，后面放 `.fb` |
| 拨开关 | `.gate data-op="and/or/not"`，里面放 `button`（写 True 或 False）和 `b`，结果由脚本算 |
| 黄色框 | 代码行里放 `input.slot data-var="名字" value="默认值"`，数字框加 `inputmode="numeric"`，不加 `maxlength`，填多了才看得到提示，文字框加 `data-kind="text"`，放在代码里写好的两个英文引号中间（`<span class="s">"</span><input …><span class="s">"</span>`），引号是页面代码的一部分，学生只填字。结果放 `.live-out` 里的 `b data-eval`，写好默认结果：`a // b` 这样的运算，或者只写一个名字。几次运算从左往右算，页面代码要用括号写成同样的顺序，比如 `lo + hi // 2` 对应 `(lo + hi) // 2`。数字是 0 到 9999 的整数，运算有 `+ - * / // %` 和六种比较；文字最多 12 个字，不能有引号（英文、中文都不行）和反斜杠。填了范围外的值（负数、小数、字母、超过 9999、引号、太长），页面不会偷偷改成别的数：框变红、结果变成“？”、编辑器下面出一句红色提示，按原因说一句孩子看得懂的话，框里打了引号就说“两边的引号已经写好了，框里只填字”，不教学生用中文引号；框清空时结果也是“？”，提示变成黄色的“框里空着”，IDE 按钮带的仍是学生填的原文，只有文字里的英文引号和反斜杠会按语言转义，让代码能运行。一页最多 2 个框，`data-eval` 按 `print` 的顺序写。`check_browser` 会把所有组合拿真实 Python 或 C++ 跑一遍。例子见第 1、2、3、4 课，几次运算见第 16、26 课。答案不能出现在黄色框页上：小改写和独立迁移的程序不要做成黄色框 |
| 代码变化 | 讲“在上一版上加一行、改一处”时用。同一个 `.editor` 里先放旧版 `pre.code.was`，紧跟着放新版 `pre.code data-change="2"`，页面加 `data-steps`。翻到第 `data-change` 步时播放变化：没变的行不动，新增的行滑进来（绿条），删掉的行淡出，改过的行换字（黄条）；往回翻退回旧版；系统设了“减少动态效果”就直接切换。缩略图是旧版，PDF 是新版并标好颜色，IDE 按钮总是带新版。两版都要有测试：写 `data-file`，或者在 `tests/claims.json` 给这页写上那一版的输出。框里不能放黄色框。只改了缩进的行（外面套一层循环）会整行滑到新位置。合并两页时，旧版的几步在前，`data-change` 设成变化那一步，后面接新版的几步；只在某几步出现的字、结果、问号用 `only1` 到 `only5`，从某步起一直在的用 `step s2` 到 `s5`，高亮行用 `l1` 到 `l5`。没变的行和改过的行用的是新版那一行，旧版那几步的高亮要写在新版的行上。页面的 IDE 按钮带新版；旧版是主要例题时，在旧版那几步另放一个 `a.ide only2 data-code-file="starter/…"`。工具栏的“本页代码进 IDE”跟着这一步显示的按钮走，没显示的按钮点不到。编辑器要够宽：变化页的行放不下会被截掉，`check_browser` 会报。什么时候用、什么时候不用，见 `basics/PROMPT.md` 的“互动”。例子：第 6 课第 3、18 页（一页里改），第 6 课第 8 页、第 18 课第 5 页（上一页的程序变成例题），第 4 课第 13 页、第 5 课第 17 页、第 24 课第 3 页、第 27 课第 3 页、第 28 课第 3 页（两页合成一页） |
| 数轴 | `.numline` 里放 `u`（线段）、`i`（端点，`.open` 为空心）和 `b`（刻度），位置用百分比 |
| IDE 按钮 | `a.ide`，默认带本页代码；`data-code` 写其他代码，`data-code-file` 带上某个起始程序 |
| 只显示部分代码 | `pre.code data-file="…" data-lines="7-13"`，IDE 仍带完整程序 |
| 代码只是片段 | 页面只放几行、不是完整程序时，在 `tests/claims.json` 里给这页那条完整程序加 `"ide": true`，“本页代码进 IDE”就带它。读报错页也这样，学生在 IDE 里看到的是页面讲的同一个报错。停不下来的程序只写 `page`、`ide`、`code`，检查只编译不运行。`check.py` 会查每页进 IDE 的代码是不是完整、能运行的程序 |
| 章节跳转 | 每章第一页的 `<section>` 加 `data-chapter="名字"` |
| 满版颜色 | `.dark` 听讲，`.band` 动手，`.clay` 挑战，`.olive` 复盘 |

页面用绝对定位，以 1920×1080 为准。放不下就拆页，不缩小字号。

## 4. 构建和检查

在 `basics/` 里运行：

```sh
python3 tools/build.py --pdf
python3 tools/check.py
node tools/check_browser.mjs
```

`--pdf` 只重新打印页面变了的课，并更新 `pdf.json`；PDF 跟不上页面时 `check.py` 会报错。然后看 `.preview/` 里的截图，每页和每个分步都要看。自动检查量不出丑不丑。

## 5. 交给老师

打开 `dist/<课>/index.html`，说明验证了什么、没验证什么。Windows 和投影只有老师现场能确认。更新 `basics/README.md` 的课程表；课数变了，同时改仓库最外层宣传 `README.md` 和 `home/index.html` 里的节数。提交并推送。老师的修改意见如果是通用的，写回 PROMPT.md，下节课就不会再犯。
