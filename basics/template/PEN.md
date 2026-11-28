# 画笔和白板：交接说明

老师把放映外壳里的画笔和白板交给 Codex 单独改。这份说明写清能改什么、不能动什么，怎么构建、检查和提交。

## 能改的文件

只有这四个文件，都在 `basics/template/` 里：

| 文件 | 内容 |
| --- | --- |
| [pen.js](pen.js) | 画笔和白板的全部脚本：`class PenAndBoard` 里的方法 |
| [pen.css](pen.css) | 画笔、荧光笔、白板、小球的样式 |
| [pen.html](pen.html) | 小球和它打开的工具栏（颜色、白板、收笔）的 HTML |
| [pen-help.html](pen-help.html) | 快捷键帮助（按 ? 打开）里画笔那几行：D、1 2 3、C、W、Esc |

改完要重新构建，构建出来的 `basics/dist/`、`basics/pdf.json` 和 `project/dist/` 也一起提交（见下面“构建和检查”）。

## 不能动的文件

- `basics/template/` 里的其他文件：`deck.js`、`page.html`、`theme.css`、`layouts.css`、`index.html`、`starter.html`、`icons/`。
- `basics/tools/`、`basics/vendor/`、`basics/lessons/`、`basics/course.json`、`basics/site.json`。
- `project/` 里除了构建生成的 `project/dist/` 以外的文件。
- `.github/`、各处的 `AGENTS.md`、`README.md`、`home/`。
- `dist/` 不手改，只提交构建的结果。

这些文件 Python 课和 C++ 课共用，或者是课件内容。需要改它们时，先告诉老师，由 Claude 的子对话来改。

## 画笔怎么接到放映外壳上

构建时把这四个文件拼进每节课的页面：

- `pen.css` 接在 `theme.css` 后面；
- `pen.html` 放在 `page.html` 的 `{{pen}}`，`pen-help.html` 放在 `{{pen_help}}`；
- `pen.js` 放在 `deck.js` 前面，两个文件在同一个 `<script>` 里。

`deck.js` 的最后几行把 `PenAndBoard` 的每个方法挂到放映外壳（`SlidePresentation`）上，所以这些方法里的 `this` 就是放映外壳。

**接口不能改坏。** `pen.js` 开头的注释列了双方互相用到的东西，名字和作用都要保留：

- 画笔用放映外壳的 `this.stage`（1920 × 1080 的舞台）和 `this.reveal()`（显示控制条和小球）。
- 放映外壳在 `deck.js` 里用画笔的这些：
  - 构造时调 `setupPen()`；
  - 每次翻页调 `clearInk()`；窗口大小变了调 `placeBall()`；
  - 鼠标一动，给 `this.ball` 加上 `show`，两秒后去掉；
  - `this.pen` 为真时，点击不翻页，1 2 3 换颜色，4 什么也不做；
  - `this.board` 为真时，算法演示的按键不起作用，Esc 先关白板；
  - 按键：D 调 `togglePen()`，W 调 `toggleBoard()`，C 调 `clearBoard()` 或 `clearInk()`，Esc 调 `toggleBoard(false)` 或 `togglePen(false)`，1 2 3 调 `pickColor()`。

按键是在 `deck.js` 的 `key()` 里读的。想换按键，或者要放映外壳多给画笔一样东西，先告诉老师，不要自己改 `deck.js`。在 `pen.js` 里新增方法、改方法内部的写法都可以，但不要和 `deck.js` 里已有的方法同名，否则会把它盖掉。

另外两处：

- 打印 PDF 时，`theme.css` 的 `@media print` 把 `.ink-layer`、`.pen-ball`、`.board`、`.board-shade` 藏起来。新加的画笔元素在打印时也要藏，就在 `pen.css` 里自己写一条 `@media print`。
- 小球和白板的位置存在浏览器的 `localStorage` 里，键名是 `deck-pen-ball` 和 `deck-board`。改了键名，老师电脑上存过的位置就失效了。

## 构建和检查

命令都在 `python-for-youth/basics/` 里运行（从仓库最外层先 `cd basics`）：

```sh
python3 tools/build.py --pdf            # 重建 30 节课的页面，重新打印 PDF
python3 tools/check.py                  # 程序、页面、链接、PDF 是否跟上
node tools/check_browser.mjs --sample   # 真实 Chrome 里查三节代表课，每页每步有没有溢出、重叠
```

项目课的页面也带画笔，再到 `python-for-youth/project/` 里运行：

```sh
python3 tools/build.py
python3 tools/check.py
node tools/check_browser.mjs
```

都只打一行 `PASS` 才算通过。检查不会替你点画笔，改完要在 Chrome 里打开一节课（比如 `basics/dist/15-params-return/index.html`）亲手试一遍：

- D 拿笔，画一笔；1、2、3 换红、蓝、荧光笔；点小球上的颜色也能换；
- 拿着笔点页面不翻页，按 → 翻页后笔迹清掉；C 擦掉；Esc 收笔；
- W 打开白板写字，拖顶上的横栏移动，拖右下角改大小；翻页时白板留着；W 或 Esc 关掉，写的清掉；
- 把小球拖到另一边，刷新页面后还在那边，白板的位置和大小也还在；
- 按 ? 看快捷键帮助里画笔那几行对不对。

## 提交

- 从最新的 `main` 拉一个新分支，在分支上改，开 PR。不要直接推 `main`。
- PR 里写清改了什么、上面的检查和手动试的结果。
- 推送后 CI 会全量检查 30 节课和项目课（改了 `template/` 就全量，大约 8 分钟）。CI 全绿以后，由老师决定合并。
- C++ 课（`cpp-for-youth`）用同一套文件，合并以后由 Claude 那边同步过去，这里不用管。
