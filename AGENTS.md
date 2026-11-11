# Python 青少年编程：仓库规则

默认简体中文。仓库 `lixuanan2/python-for-youth` 按模块分文件夹，每个模块有自己的说明，各自独立构建和检查。这里只写模块之间的事。

## 模块

| 文件夹 | 页面上叫 | 说明 | 网址 |
| --- | --- | --- | --- |
| `basics/` | 基础课件 | [basics/AGENTS.md](basics/AGENTS.md) | `https://lixuanan2.github.io/python-for-youth/basics/` |
| `project/` | 项目课（规划中） | [project/AGENTS.md](project/AGENTS.md) | 还没有 |

- 做课、改课先读 `basics/AGENTS.md`，命令都在 `basics/` 里运行。教学要求在 `basics/PROMPT.md`。
- 项目课和基础课件不同：代码在学生自己的电脑上写和运行，老师给素材、前端和测试，学生只写后端逻辑。还没有课，不进 CI、宣传 README 和首页。
- 每个模块自带模板、工具和字体（`template/`、`tools/`、`vendor/`），不和别的模块共用。以后的模块要不要共用，等老师定了再改。

## 跨课程的规则

这些规则 Python 课和 C++ 课都一样，在这里写全，单独 clone 这个仓库也看得到：

- 一律用相对路径：课件里的链接、文档和给老师的命令都不写绝对路径。给命令时写清在哪个文件夹里运行，比如“在 `basics/` 里运行”。
- 课件是上课讲的，不写“必做”“选做”“作业”这类字样，题目也不分等级。课后作业老师另外布置。
- 只改一个值、结果一眼能看到的地方，用黄色框让学生直接在页面上改，省掉打开 IDE 的时间。多行输出、循环、改结构、读报错、运行完整程序，或者做起来复杂、容易出错的，都用 IDE，不勉强。具体写法见 [.claude/skills/python-lesson/SKILL.md](.claude/skills/python-lesson/SKILL.md) 的“黄色框”，每课几处、放在哪里见 [basics/PROMPT.md](basics/PROMPT.md) 的“互动”。
- `basics/` 里的 `template/`、`tools/`、`vendor/` 是 Python 课和 C++ 课（[lixuanan2/cpp-for-youth](https://github.com/lixuanan2/cpp-for-youth)）共用的，只在本仓库改，检查通过后由维护者同步到 C++ 课，再跑那边的检查。C++ 课需要改共用文件时也提到这里来。

老师本机有主文件夹的话（本仓库的上一层，里面还放着 C++ 课），那里的 `AGENTS.md` 还写了几门课怎么一起管理、同步共用文件的命令。它只是老师本机的补充，上面的规则不依赖它。

## 最外层

- `README.md`：宣传门面，写给老师、机构和逛 GitHub 的人。最上面两三句英文，正文中文。改了要同步 `home/index.html`，两者内容一致。
- `home/index.html`：网站首页 `https://lixuanan2.github.io/python-for-youth/`，手写，不经过构建。用到的字体由发布网站的那一步从 `basics/vendor/fonts/` 复制到网站的 `fonts/`。
- `.github/workflows/check.yml` 先在各模块文件夹里跑检查：`check` 在 Ubuntu 和 Windows 上跑 `tools/check.py`，`browser` 在 Ubuntu 的 Chrome 里跑 `tools/check_browser.mjs`。两项都通过后，`deploy` 才把 `home/` 和各模块的 `dist/` 组装成网站发布：首页在最外层，`basics/dist/` 放到 `/basics/`。`deploy` 还按 `ide/` 构建课程用的 IDE，放到 `/ide/`。只有 `main` 上的推送和手动运行会发布，PR 只检查。
- `ide/`：课程用的在线 IDE，是固定版本的 JupyterLite，Python（Pyodide）一起发布，学生打开时不从 CDN 下载。只提交版本和配置：`requirements.txt` 定 JupyterLite 的版本，`prepare.py` 定 Pyodide 的版本，下载并核对哈希，只留内核启动要用的包。构建结果不进 Git，由 `deploy` 生成。本机试：在 `ide/` 里 `pip install -r requirements.txt`、`python prepare.py`、`jupyter lite build`，再用任意静态服务器打开 `_output/repl/index.html`。
- `CONTRIBUTING.md`、`LICENSE.md`、`.github/` 的模板管整个仓库。
- 联系方式只写 GitHub Discussions，不公开邮箱。

## 新增模块

1. 新建 `<英文名>/` 文件夹，写它自己的 `AGENTS.md`、`CLAUDE.md`（内容 `@AGENTS.md`）和 `README.md`。
2. 在上面的表格、宣传 `README.md` 和 `home/index.html` 的“模块和进度”里加上它。
3. 在 `check.yml` 里加上它的检查（`check` 和 `browser` 各一步），再在 `deploy` 里加一行复制它的 `dist/`。
4. 现在写死 `basics/` 的地方要一起改：`.claude/skills/python-lesson/SKILL.md` 只管基础课件，新模块要么另写 skill，要么在这个 skill 里写清各模块的路径；`.github/pull_request_template.md` 的自查清单；`CONTRIBUTING.md` 的“想直接改”和共用文件那一段。
