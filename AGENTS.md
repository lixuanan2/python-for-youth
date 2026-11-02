# Python 青少年编程：项目规则

默认简体中文。这里写项目规则，教学要求只在 [PROMPT.md](PROMPT.md) 写一次，不要复制第二份。

## 项目

- 私有仓库 `lixuanan2/python-for-youth`，面向小学高年级和初中生的 Python 课程。
- 课堂入口是把 `dist/` 复制到 Windows 电脑后双击打开。开发在 macOS。
- 老师主要通过 AI 做课和改课。

## 目录

- `lessons/<编号-英文名>/slides.html`：一节课的页面，只写 `<section>`。这是唯一的内容源。
- `lessons/<…>/tasks.json`、`starter/`、`solutions/`、`tests/`：题目、起始程序、答案和测试。`tests/claims.json` 记录页面说过的输出和报错。
- `template/`：所有课共用的外壳、样式和脚本。缩略图、时间轴、章节跳转都在这里。
- `course.json`：课程路线。有 `id` 的已做好，其余是首页显示的规划中课程。上下集各占一行。
- `site.json`：网站名称、首页文字、语言和 IDE 平台。换语言或换 IDE 只改这里。
- `dist/`：生成结果，提交进仓库，不要手改。

## 命令

都在仓库根目录运行：

```sh
python3 tools/build.py          # 生成 dist/
python3 tools/build.py --pdf    # 同时用 Chrome 打印 PDF
python3 tools/check.py          # 程序、答案、页面说法、路径
node tools/check_browser.mjs    # 真实 Chrome 逐页检查和交互测试
```

## 规则

- 一律用相对路径：课件、文档和给老师的命令都不写绝对路径。给命令时说明要在仓库根目录运行。
- 改课只改 `lessons/` 和 `template/`，再重建。
- 课件离线可用：样式、脚本和字体都内联，不用 CDN 和在线字体。只有 IDE 和官方文档链接需要联网。
- IDE 地址只写在 `site.json` 的 `ide` 里，换平台只改这一处。
- 程序、页面说法和答案都要过 `tools/check.py`。页面上新写的输出或报错要加进 `claims.json`。
- 小改写和独立迁移的答案不进 `dist/`。`dist/` 里没有 `solutions/`、`tests/`。这只减少学生接触，不是权限控制。
- 一次做一节课，先把设计给老师确认再写。见 `.claude/skills/python-lesson`。
- 新模块沿用现有组件。确实需要新组件时写进 `template/theme.css`，并检查已有课程。
- 不自动公开仓库、不部署。真实学生记录不进 Git。
- 字体只收开源字体，放 `vendor/fonts` 并保留许可。

## 汇报

- 分清验证过和没验证的。macOS Chrome 不等于 Windows 教室，模拟检查不等于真实浏览器，不代填验收结果。
- 完成检查后提交并推送，核对推送结果。推送不了就说明待执行的操作。
- 只讨论方案时不动手。已授权的可逆开发直接做，不反复确认。

## 姊妹项目

C++ 课件在 `lixuanan2/cpp-teaching` 的 `HTML课件/` 文件夹，用同一套模板。本仓库为主：`template/`、`tools/`、`vendor/` 只在这里改，C++ 有需要时提过来。改动对 C++ 也有用时，把这三个文件夹同步过去，再跑那边的检查。

## 旧资料

上级旧仓库 `Python教学`（`lixuanan2/python-teaching`）存放旧的 18 个模块、PPT 和历史记录，只作内容参考，不搬进来。[docs/module-baseline.md](docs/module-baseline.md) 是 18 个模块的内容摘要，做课先读它，需要细节再读旧仓库对应的那一个模块，按 PROMPT.md 重写。
