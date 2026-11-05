# Python 青少年编程：仓库规则

默认简体中文。仓库 `lixuanan2/python-for-youth` 按模块分文件夹，每个模块有自己的说明，各自独立构建和检查。这里只写模块之间的事。

## 模块

| 文件夹 | 页面上叫 | 说明 | 网址 |
| --- | --- | --- | --- |
| `basics/` | 基础课件 | [basics/AGENTS.md](basics/AGENTS.md) | `https://lixuanan2.github.io/python-for-youth/basics/` |

- 做课、改课先读 `basics/AGENTS.md`，命令都在 `basics/` 里运行。教学要求在 `basics/PROMPT.md`。
- 每个模块自带模板、工具和字体（`template/`、`tools/`、`vendor/`），不和别的模块共用。以后的模块要不要共用，等老师定了再改。
- 跨课程的规则（相对路径、黄色框、不写“必做”“选做”“作业”、和 C++ 课同步模板）见主文件夹的 `AGENTS.md`，从这里算是 `../AGENTS.md`。

## 最外层

- `README.md`：宣传门面，写给老师、机构和逛 GitHub 的人。最上面两三句英文，正文中文。改了要同步 `home/index.html`，两者内容一致。
- `home/index.html`：网站首页 `https://lixuanan2.github.io/python-for-youth/`，手写，不经过构建。用到的字体由 Pages workflow 从 `basics/vendor/fonts/` 复制到网站的 `fonts/`。
- `.github/workflows/pages.yml` 把 `home/` 和各模块的 `dist/` 组装成网站：首页在最外层，`basics/dist/` 放到 `/basics/`。新增模块时在这里加一行复制。
- `.github/workflows/check.yml` 在各模块文件夹里跑检查。新增模块时加一步。
- `CONTRIBUTING.md`、`LICENSE.md`、`.github/` 的模板管整个仓库。
- 联系方式只写 GitHub Discussions，不公开邮箱。

## 新增模块

1. 新建 `<英文名>/` 文件夹，写它自己的 `AGENTS.md`、`CLAUDE.md`（内容 `@AGENTS.md`）和 `README.md`。
2. 在上面的表格、宣传 `README.md` 和 `home/index.html` 的“模块和进度”里加上它。
3. 在两个 workflow 里加上它的构建结果和检查。
