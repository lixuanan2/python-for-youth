# 参与这门课

这是一门给小学高年级和初中生的 Python 课。课件由老师和 AI 一起做，老师负责审定。欢迎老师、程序员、家长和学生提意见。

## 最有用的建议

- 这一页学生会卡在哪里。
- 这里讲错了，或者说法到后面会不成立。
- 这一页可以删掉，或者应该换个顺序。
- 哪道题太难、太简单，或者不像这个年纪的学生会做的事。

最好写清楚第几课第几页，看过学生实际反应的话也请写上。

## 怎么提

| 想说的 | 去哪里 |
| --- | --- |
| 讲错了、代码不对 | Issue：内容错误 |
| 教学上的改进想法 | Issue：教学建议 |
| 页面显示不正常 | Issue：页面显示问题 |
| 还没想清楚，想聊聊 | Discussions |

## 想直接改

错字和小改动可以直接发 PR。新增页面、调整结构这类大改动，先开 Issue 商量，免得白做。

现在只有一个模块“基础课件”，在 `basics/` 文件夹里。改课只改 `basics/lessons/` 和 `basics/template/`，`basics/dist/` 由工具生成，不要手改。从仓库最外层运行：

```sh
cd basics
python3 tools/build.py --pdf
python3 tools/check.py
node tools/check_browser.mjs
```

`--pdf` 会用 Chrome 把页面变了的课重新打印成 PDF。改了课件正文或模板都要带上它：`basics/pdf.json` 记着每份 PDF 是照哪一版页面打印的，`check.py` 发现 PDF 跟不上页面就会报错，GitHub 上的检查也会拦住。没装 Chrome 的话，只运行 `python3 tools/build.py` 也行，在 PR 里说一声，由维护者补打 PDF。

然后把重新生成的 `basics/dist/` 和 `basics/pdf.json` 一起提交。页面上新写的输出或报错，要加进那节课的 `tests/claims.json`。教学要求都在 [basics/PROMPT.md](basics/PROMPT.md)。

`basics/template/`、`basics/tools/`、`basics/vendor/` 是这门课和 [C++ 课](https://github.com/lixuanan2/cpp-for-youth)共用的模板、工具和字体，以这里为准。要改就在这里改，由维护者同步到 C++ 课，不用去 C++ 那边再提一次。

## 不收的内容

- 必做、选做、作业这类标记，课件不给题目分等级。
- CDN、在线字体这类让课件离线打不开的改动。
- 来源不明或没有授权的图片、题目和文字。
- 自己没有看过、没有运行过的 AI 生成内容。

## 怎么决定

意见都会看，但不一定采纳。这门课有自己的受众和节奏，最后由老师决定。

## 保护学生

这门课的读者可能是未成年人。在 Issue、PR、Discussions 和评论里：

- 不贴学生的姓名、照片、成绩、学校或联系方式。想说课堂情况，写“有个学生”就够了。
- 说话友善，对事不对人。

发现仓库里有不该公开的内容，开一个 Issue，只写“有隐私问题”，不要贴出具体内容。

## 许可

提交的内容按 [LICENSE.md](LICENSE.md) 里同样的许可发布。
