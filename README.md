# Python 青少年编程

Free, open Python courseware in Chinese for upper-primary and middle-school students (about ages 10 to 15). Each lesson is a web page that opens offline with a double-click, reads well enough for self-study, and sends any code on the page to an online IDE in one click. Teachers, schools and anyone who wants to collaborate are welcome to get in touch through GitHub Discussions.

这是一套给小学高年级和初中生的 Python 课件，免费、开源。每节课是一个网页，老师拿来上课，学生也能照着自学。

- 在线看：<https://lixuanan2.github.io/python-for-youth/>
- 第一课：<https://lixuanan2.github.io/python-for-youth/basics/01-input-output/>

## 适合谁

- 学生：小学高年级和初中生，零基础起步。
- 老师：学校、机构和兴趣班的老师。课件里的句子写得完整、口语化，老师照着读就能讲，不用另备讲稿。
- 自学的孩子和家长：只看页面也能看懂，每讲一点就有一道题马上练。

## 有什么不一样

- **离线双击就能打开。** 每节课是一个网页文件，样式、脚本和字体都在里面，不用装软件，不用联网。只有打开 IDE 和官方文档时要联网。
- **学生能照着自学。** 每节课按“讲一点、练一点”推进：先猜结果再揭晓，选择小测点了马上解释，点出报错的那一行，最后做一个自己定主题的小程序，再和同桌换着玩。
- **代码一键进在线 IDE。** 页面上的代码点一下就带到 JupyterLite 里运行，动手题带着起始程序打开，不用复制粘贴。
- **黄色框能在页面上直接改值。** 只改一个数、结果一眼能看到的地方，学生在页面上改，结果马上变，省掉打开 IDE 的时间。
- **每个程序和页面说法都有自动检查。** 页面上的程序都由工具检查过：页面说的输出和报错用真实 Python 运行核对，个别停不下来的示例只检查写法、不运行；题目答案用测试数据跑过，动手题和挑战的答案不会出现在学生拿到的文件里。每次改动后，每一页还会在真实的 Chrome 里打开，检查排版、小测、黄色框和 IDE 链接。

## 怎么用

- **在线：** 打开 <https://lixuanan2.github.io/python-for-youth/>，选一节课。
- **教室电脑：** 在这个仓库的页面点 Code → Download ZIP，解压后把 `basics/dist` 文件夹整个复制到教室电脑，双击里面的 `index.html`。这个文件夹里有课件、PDF 和起始程序，没有答案。

放映时按 `→` 或空格翻页，`R` 带着本页代码打开 IDE，`F` 全屏，`?` 查看全部快捷键。更多用法见 [basics/README.md](basics/README.md)。

## 模块和进度

| 模块 | 内容 | 进度 |
| --- | --- | --- |
| [基础课件](basics/README.md) | 从输入输出、变量讲起，经过判断、循环、列表、字符串、函数、字典，到递归、排序、二分查找这些算法入门 | 30 节已完成，[在线看](https://lixuanan2.github.io/python-for-youth/basics/) |

以后会继续加别的模块，比如项目课。

## 用 Edge 的话

IDE 里的 Python 是在浏览器里跑的。Edge 开着“增强的安全性”时会关掉它要用的功能，表现是点了运行右边一直空白。在 Edge 设置里搜“增强的安全性”，在“例外”里添加 `jupyterlite.github.io` 就好了；或者改用 Chrome。

## 想合作或交流

来 [Discussions](https://github.com/lixuanan2/python-for-youth/discussions) 留言。在学校或机构里用了这套课、想一起做新模块、发现哪里讲得不好，都欢迎来说。具体的错误和建议可以开 Issue，怎么提见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可

课件内容用 CC BY-NC-SA 4.0，可以免费用在课堂上、修改和分享；想用在收费课程里，先开一个 Issue 问一下。代码用 MIT。详见 [LICENSE.md](LICENSE.md)。
