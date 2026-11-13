# 项目课：模块规则

默认简体中文。这里写“项目课”这个模块的规则。整个仓库有哪些模块见仓库最外层的 [AGENTS.md](../AGENTS.md)，基础课件的规则见 [basics/AGENTS.md](../basics/AGENTS.md)。

## 现状

- 第一个项目：井字棋，5 关，网址 `https://lixuanan2.github.io/python-for-youth/project/`。仿照大学里分阶段做的项目：一个项目拆成几关，每关加一样东西，做完一关能跑、能测，再做下一关。
- 老师接受了试点的 14 条假设（棋盘是 9 个字符的字符串、函数名、5 关、电脑怎么下等），原稿在仓库外的 `~/Documents/project-research/pilot-tictactoe/README.md`。
- 时间估计没有在课上试过。

## 不动 basics

- 做项目课不改 `basics/` 里的任何文件。项目课的课件直接读 `basics/` 的模板、字体和 IDE 设置（`page.html`、`theme.css`、`deck.js`、`site.json` 的 `ide`），只读不改；项目自己要的样式和页面放在 `project/template/`。
- 项目课的工具（`project/tools/`）和模板以 Python 课为准，改好后同步给 C++ 课。工具按 `site.json` 的 `language` 分 Python 和 C++，C++ 的那一支现在没有项目在用。

## 目录

下面的路径都从 `project/` 算起。每个项目一个文件夹（现在是 `tictactoe/`，以后比如 `sokoban/`），这个项目的东西都放在里面；直接放在 `project/` 下的只有各个项目共用的工具、样式和生成结果。

- `site.json`：语言、有哪些项目、基础课件的网址、页脚。
- `<项目>/stages.py`：每关的函数（名字、函数头、说明、占位、参考答案）、测试用例、要先学完哪几课，还有整个项目的标题、介绍、前端能玩什么、“想一想”、前端的试玩按键。改内容只改这里。
- `<项目>/slides.html`：课件里手写的页，每关只有“一起想”的在线 IDE 演示和小测。`<!-- @map -->`、`<!-- @run -->`、`<!-- @stage N -->` 的位置由构建按 `stages.py` 生成项目地图、怎么运行测试、第 N 关的开头和要写的函数这几页。演示代码写在 `<pre class="code" data-demo>` 里，输出写在同一页的 `<pre data-out>`；故意出错的写 `data-error="IndexError"`。小测的 `data-right` 从 0 数，那一项的反馈以“答对了”开头。
- `<项目>/templates/`：老师的前端。`play.py` 是终端版，每关都有；某一关另外要发的文件（网页版前端 `play_web.py` 和它的网页、图片 `web/`）在 `stages.py` 那一关的 `extra_py` 里列出，C++ 用 `extra_cpp`。
- `<项目>/draw_assets.py`：用标准库画 `templates/web/assets/` 里的棋盘和棋子（不用别人的图）。老师换自己的图片时文件名不变就行，不用运行它。
- `<项目>/answers/`：参考答案，构建生成，提交进仓库，给老师看，不进 `dist/`。
- `template/`：项目课共用的样式（`project.css` 给课件，`site.css` 给项目地图、开发文档和首页）。
- `tools/`：`build.py` 生成，`check.py` 和 `verify.py` 检查，`check_browser.mjs` 在 Chrome 里看课件和网页，`stagefiles.py` 生成每关的文件和开发文档。
- `dist/`：生成结果，提交进仓库，不要手改，发布到网站的 `/project/`。`dist/index.html` 是项目课首页；`dist/<项目>/` 里有项目地图 `index.html`、开发文档 `guide.html`、课件 `slides/index.html`，`download/` 是发给学生的每关文件夹和 zip（没有答案）。

## 学生拿到什么

- **开发文档是主要的东西**：像大学项目的题目说明，一个项目一份，写清做什么、一共几关、每关的目标、要写的函数（名字、给什么、还什么、例子）、要先学完哪几课、怎么运行测试。由 `stages.py` 生成，每关的文件夹里都有同一份 `guide.md`，网站上是 `guide.html`。
- **课件只给老师在大屏幕上讲**：项目地图、怎么运行测试、每关一页开头、要写的函数，再加“一起想”的在线 IDE 演示和小测。每个项目一份课件，不给每关做一大套。
- **参考答案简洁**：照学生的水平写，短、好读，只用标准库，不用高级的包。测试只用 `unittest`，前端只用普通的 Python。`check.py` 查：发出去的 `.py` 只能 import 标准库里列出的几个（`unittest`、`sys`、`os`，网页前端还用 `json`、`http.server`、`webbrowser` 这些）和项目自己的模块；每个答案函数不超过 20 行。`verify.py` 查答案只用到学过的语法。
- **中文显示**：测试和前端开头有几行，控制台显示不了中文时换成 UTF-8（Windows 英文系统、或者编辑器不设编码时会这样）；中文 Windows 的控制台照原样。

## 命令

都在 `project/` 里运行：

```sh
python3 tools/build.py          # 生成 dist/ 和 answers/
python3 tools/check.py          # dist 是不是最新、有没有答案、演示输出、小测、链接
python3 tools/verify.py         # 每关：起始程序测试干净地不过、答案全过、只用学过的、前端能玩，网页前端自检
node tools/check_browser.mjs    # 真实 Chrome 逐页看课件，截图在 .preview/；后面写项目名只查那几个
```

`check.py` 和 `check_browser.mjs` 全部通过时只打一行，失败才打详细内容。`check_browser.mjs` 每次通过后，把截图和上次在本机通过时的比（存在 `.check-shots/`，不进 Git），画面变了的页列在 `.preview/changed.txt`，只看清单里的截图。

CI 在 Ubuntu 和 Windows（Python 3.12、3.14）上跑 `check.py` 和 `verify.py`，每次都跑。网页前端用 `play_web.py --selftest` 自检：不开浏览器，在 127.0.0.1 上起服务器，照网页用的接口下完几局；配答案要下完，配起始程序要回提示、不崩溃。浏览器按改动决定（规则在仓库最外层的 `.github/browser_plan.py`）：只改了某个项目的文件夹（`<项目>/`、`dist/<项目>/`），只查那个项目；改了 `template/`、`site.json`、`dist/index.html`、`tools/` 里的 `build.py`、`stagefiles.py`、`check_browser.mjs`，或者 basics 的模板、字体、`site.json`，查全部项目；只改了 `check.py`、`verify.py` 或说明，不开浏览器。都过了才发布到 `/project/`。

## 和基础课件的不同

- **代码在哪里跑：**项目代码在学生自己的电脑上写和运行，编辑器不限（PyCharm、VS Code 都行）。只有课件页上的演示脚本用在线 IDE（JupyterLite）讲解。
- `basics/` 里说学生只用在线 IDE、不在电脑上打开文件，那几条只管基础课件。项目课的代码在本地打开和运行。
- **谁写什么：**素材包（图片、音效这些材质）和显示画面的前端代码由老师提供，学生只写后端逻辑。
- **名字照抄：**开发文档里点名的重要函数、类和方法，学生必须用老师给的名字，一个字母也不能改，因为测试按这些名字调用。
- **不用 class：**第一轮的项目只用函数，数据放在列表或字典里。测试调用老师点名的函数。
- **每个阶段做对没有：**用老师提供的测试文件判断，学生运行测试，全部通过才算这个阶段做完。第一轮是行为测试，比如“角色向上走一格”：调用学生写的函数，看位置变没变对。
- **怎么发给学生：**起始程序包由老师下载，用 U 盘发给学生。一个阶段一份：起始代码、前端、素材和测试。上课时学生不用上网下载任何东西。每关一个文件夹，学生文件里已经带着前几关的参考答案，上一关没做完也能接着做。U 盘里放解压好的文件夹，不放 zip。

## 测试怎么写

- 测试不能要求学生另外安装东西，所以用 Python 自带的 `unittest`，不用 pytest 这类要另装的框架。井字棋就是这样做的。
- 在编辑器里能直接运行测试文件（PyCharm 和 VS Code 都认得 `unittest`），也能在命令行运行：在这个阶段的文件夹里 `python -m unittest`。
- 测试文件只调用开发文档里点名的函数、类和方法。失败时的提示用中文写清哪一项错了，比如“向上走一格后，行号应该是 2”。

## 先学哪些基础课

每个阶段写明要先学完哪几节基础课，用基础课件的文件夹名，比如：

- 用格子地图的阶段，要先学 `10-list-basics` 和 `11-list-loop`。
- 二维的格子地图，要先学 `20-2d-lists`。
- 用函数拆开逻辑的，要先学 `14-functions` 和 `15-params-return`；用字典存角色、物品的，要先学 `17-dict-basics`。

## 以后的升级

- 基础课 30 节没有讲 class（存数据用的是列表、字典和元组）。等有了讲 class 的课，同一个项目再用 class 重做一遍，当作升级的一轮，就像大学项目的第二部分。
- 升级那一轮加功能测试：getter、setter 和 toString。在 Python 里 toString 就是 `__str__`，用 `str(对象)` 或 `print(对象)` 检查；getter、setter 写成普通方法还是 `@property`，由开发文档定。

## 规划资料

- 规划研究放在仓库外的 `~/Documents/project-research`，老师同意后才把内容搬进来。井字棋的试点已经搬进来了（`tictactoe/`），原稿不改。

## 共用的规则

- 文字一律用中文，一律用相对路径。
- 不写“必做”“选做”“作业”这类字样，题目也不分等级。
- 真实学生的姓名、联系方式和成绩不进 Git，也不写进 Issue、PR 和评论。
