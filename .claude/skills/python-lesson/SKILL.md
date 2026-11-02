---
name: python-lesson
description: 做或修改 Python 少儿编程课件。老师说“做下一课”“做一节 XX 课”“改第几页”“迁移旧模块”时使用。
---

# 做一节 Python 课

先读 [PROMPT.md](../../../PROMPT.md)，那里是全部教学要求。这里只规定操作顺序。一次只做一节课。

## 1. 定设计，等老师确认

读 `course.json` 和上一节课的 `slides.html`，确认学生已经学过什么。给老师一份大纲：每页一句话，标出小测、预测、追踪、找错和项目放在哪里。迁移旧模块时，一次只读旧仓库的一个模块。

**老师确认前不写文件。** 只改错字或单页时跳过这步。

## 2. 写程序和测试

新建 `lessons/<编号-英文名>/`，复制上一节的结构，在 `course.json` 给这节课补上 `id`、`tag` 和 `file`。

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
| 语法高亮 | `.f` 函数，`.s` 字符串，`.m` 数字 |
| 分步揭晓 | 页面加 `data-steps="3" data-at="3"`，元素加 `.step .s2`、`.only1`，行加 `.l1` |
| 选择小测 | `.quiz data-right="序号"`，选项加 `data-fb`，后面放 `.fb` |
| 点行找错 | `pre.code.pick data-bug data-yes data-no`，后面放 `.fb` |
| IDE 按钮 | `a.ide`，默认带本页代码；`data-code` 指定其他代码 |
| 章节跳转 | 该章第一页的 `<section>` 加 `data-chapter="名字"` |
| 满版颜色 | `.dark` 听讲，`.band` 动手，`.clay` 挑战，`.olive` 复盘 |

页面用绝对定位，以 1920×1080 为准。放不下就拆页，不缩小字号。

## 4. 构建和检查

在仓库根目录运行：

```sh
python3 tools/build.py --pdf
python3 tools/check.py
node tools/check_browser.mjs
```

然后看 `.preview/` 里的截图，每页和每个分步都要看。自动检查量不出丑不丑。

## 5. 交给老师

打开 `dist/<课>/index.html`，说明验证了什么、没验证什么。Windows 和投影只有老师现场能确认。更新 `README.md` 的课程表，提交并推送。老师的修改意见如果是通用的，写回 PROMPT.md，下节课就不会再犯。
