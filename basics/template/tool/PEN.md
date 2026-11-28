# 画笔和白板：交接说明

画笔和白板是共用模板的一部分：和 `template/` 里别的文件一样，只在 Python 课改，合并后同步到 C++ 课。这份说明写清改画笔时能改什么、不能动什么，怎么构建、检查和提交。

## 能改的文件

只改 `basics/template/tool/` 里的文件，也就是这份说明所在的文件夹。注意别和 `basics/tools/` 搞混：`tools/` 放的是构建和检查工具，不能改。

构建只读下面这四个文件：

| 文件 | 内容 |
| --- | --- |
| [pen.js](pen.js) | 画笔和白板的全部脚本：`class PenAndBoard` 里的方法 |
| [pen.css](pen.css) | 画笔、荧光笔、白板、小球的样式 |
| [pen.html](pen.html) | 小球和它打开的工具栏（签字笔、荧光笔、橡皮、文字，换颜色的一排，撤销和重做，白板，收笔）的 HTML |
| [pen-help.html](pen-help.html) | 快捷键帮助（按 ? 打开）里画笔那几行：D、1 2 3 4、文字、Shift、C、Ctrl+Z、W、[ ]、Esc |

在 `tool/` 里另建的文件不会自动拼进页面。确实需要多一个文件，就要连构建（`tools/build.py`）一起改，先和老师商量。

改完要重新构建，构建出来的 `basics/dist/`、`basics/pdf.json` 和 `project/dist/` 也一起提交（见下面“构建和检查”）。

## 不能动的文件

- `basics/template/` 里 `tool/` 以外的文件：`deck.js`、`page.html`、`theme.css`、`layouts.css`、`index.html`、`starter.html`、`icons/`。
- `basics/tools/`（构建和检查工具；其中 `check_browser.mjs` 会点画笔，画笔的按键或工具栏改了，可能要跟着改它那几行，先说清楚再改）、`basics/vendor/`、`basics/lessons/`、`basics/course.json`、`basics/site.json`。
- `project/` 里除了构建生成的 `project/dist/` 以外的文件。
- `.github/`、各处的 `AGENTS.md`、`README.md`、`home/`。
- `dist/` 不手改，只提交构建的结果。

这些文件 Python 课和 C++ 课共用，或者是课件内容。改画笔时不顺手改它们；真要改，按它们各自的说明另外改。

## 课件是离线的单个文件

每节课构建出来是一个 HTML 文件，老师把 `dist/` 复制到教室电脑上双击打开，不联网也要能用。所以：

- 画笔用到的图片、纹理、图标、字体，都不能引外部链接（CDN、网上的图片、在线字体），也不能另放成文件。
- 只能写在 `pen.css` 和 `pen.js` 里：用 CSS 渐变、内联 SVG（写在 CSS 的 `url("data:image/svg+xml,…")` 或 JS 生成的元素里），或者用 canvas 画出来。字体只用页面已经有的（`var(--code)`、`var(--text)`）。
- 新加的动画和过渡要照顾 `prefers-reduced-motion`：系统设了“减少动态效果”时，用 `@media (prefers-reduced-motion: reduce)` 关掉或缩短动画。
- 新加的画笔元素在打印 PDF 时要藏起来（见下面“另外两处”）。

## 画笔怎么接到放映外壳上

构建时把这四个文件拼进每节课的页面：

- `pen.css` 接在 `theme.css` 后面；
- `pen.html` 放在 `page.html` 的 `{{pen}}`，`pen-help.html` 放在 `{{pen_help}}`；
- `pen.js` 放在 `deck.js` 前面，两个文件在同一个 `<script>` 里。

`deck.js` 的最后几行把 `PenAndBoard` 的每个方法挂到放映外壳（`SlidePresentation`）上，所以这些方法里的 `this` 就是放映外壳。

**接口不能改坏。** `pen.js` 开头的注释列了双方互相用到的东西，名字和作用都要保留：

- 画笔用放映外壳的 `this.stage`（1920 × 1080 的舞台）、`this.reveal()`（显示控制条和小球），只读 `this.index`（现在是第几页，页面笔迹按页记住）。
- 放映外壳在 `deck.js` 里用画笔的这些：
  - 构造时调 `setupPen()`；
  - 每次翻页调 `clearInk()`（画笔据此收起这一页的笔迹、拿出新一页的）；窗口大小变了调 `placeBall()`；
  - 鼠标一动，给 `this.ball` 加上 `show`，两秒后去掉；
  - `this.pen` 为真时，点击不翻页，1 2 3 调 `pickColor()` 换手里的工具（签字笔、荧光笔、橡皮；笔的颜色在工具栏上选），4 它不管（画笔自己读，拿起文字）；
  - `this.board` 为真时，算法演示的按键不起作用，Esc 先关白板；
  - 按键：D 调 `togglePen()`，W 调 `toggleBoard()`，C 调 `clearBoard()` 或 `clearInk()`，Esc 调 `toggleBoard(false)` 或 `togglePen(false)`，1 2 3 调 `pickColor()`。

按键是在 `deck.js` 的 `key()` 里读的；只有这几样由 `pen.js` 自己读：Ctrl+Z、Ctrl+Shift+Z、Ctrl+Y（Mac 上是 ⌘，`deck.js` 不管按着 Ctrl 或 ⌘ 的键），拿着笔时的 4（文字，`deck.js` 这时不管 4），白板开着时的 [ 和 ]（翻白板页，`deck.js` 不用），写字时按住的 Shift（直线）。在文字框里打字时，按键停在文字框上，不会传给 `deck.js` 和画笔的快捷键。想换按键，或者要放映外壳多给画笔一样东西，要连 `deck.js` 一起改，先和老师商量，不要在改画笔时顺手改。在 `pen.js` 里新增方法、改方法内部的写法都可以，但不要和 `deck.js` 里已有的方法同名，否则会把它盖掉。

另外两处：

- 打印 PDF 时，`theme.css` 的 `@media print` 把 `.ink-layer`、`.pen-ball`、`.board`、`.board-shade` 藏起来。新加的画笔元素在打印时也要藏，就在 `pen.css` 里自己写一条 `@media print`。
- 小球和白板的位置存在浏览器的 `localStorage` 里，键名是 `deck-pen-ball` 和 `deck-board`；签字笔和荧光笔选的颜色存在 `deck-pen-colors`；白板上写的东西（分页，笔画和文字）存在 `deck-board-ink`，按课的网址分开存，总共超过约 1 MB 时先丢最久没用的课。改了键名，老师电脑上存过的东西就失效了。
- 性能：教室和学生的电脑可能很差。空闲时不能有每帧都跑的循环；写字在事件里当场画；没有笔迹的画布不显示；不用大面积的 `filter`、`backdrop-filter`、一直播放的动画。改了画法，在 Chrome 开发者工具里把 CPU 降 6 倍，试写字、开白板、撤销卡不卡。

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

- D 拿笔，画一笔；1、2、3、4 换签字笔（红）、荧光笔（黄）、橡皮、文字；点工具栏上的也能换；拿着签字笔或荧光笔再点它一下，旁边出现一排颜色，选一个，刷新后还是这个颜色；
- 3 拿起橡皮，擦过的那一笔整笔消失，别的不动，Ctrl+Z 找回；
- 4 拿起文字，点一下打字，打 W、C、空格、方向键都不翻页；Enter 换行，Esc 放下；再点这段字能改；Ctrl+Z 撤掉；
- 按住 Shift 拖，画出直线，接近水平时自动摆平；
- 拿着笔点页面不翻页，按 → 翻页后页面干净，翻回来笔迹还在；C 擦掉；Esc 收笔并擦掉这一页的；
- 画两笔，Ctrl+Z 撤掉一笔，Ctrl+Shift+Z 重做；C 擦掉后 Ctrl+Z 能找回；小球上的撤销、重做按钮也能用；
- W 打开白板写字，拖顶上的横栏移动，拖右下角改大小；翻页时白板留着；W 或 Esc 关掉，再打开时写的还在，刷新页面后也还在；标题栏上的撤销、重做、橡皮能用；
- 白板上写点东西，按 ] 开第 2 页（纸角的页码变成 2 / 2），再按 [ 回第 1 页，字还在，课件没翻页；刷新后两页都在；
- 把小球拖到另一边，刷新页面后还在那边，白板的位置和大小也还在；
- 按 ? 看快捷键帮助里画笔那几行对不对。

## 提交

- 从最新的 `main` 拉一个新分支，在分支上改，开 PR。不要直接推 `main`。
- PR 里写清改了什么、上面的检查和手动试的结果。
- 推送后 CI 会全量检查 30 节课和项目课（改了 `template/` 就全量，大约 8 分钟）。CI 全绿以后，由老师决定合并。
- C++ 课（`cpp-for-youth`）用同一套文件，合并以后由维护者同步过去（见仓库最外层 `AGENTS.md` 的“跨课程的规则”），这里不用管。
