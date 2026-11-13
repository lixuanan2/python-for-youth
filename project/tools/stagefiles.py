"""The files of each stage: what students get (starter, tests, front end, guide) and the teacher's answers.

Shared by Python and C++ (language "python" or "cpp"); a project gives its data in <project>/stages.py and its
front end and helpers in <project>/templates/. Nothing here writes to disk: build.py and verify.py do.
"""
import json
import re
from pathlib import Path

BASICS_COURSE = Path(__file__).resolve().parents[2] / "basics" / "course.json"


def lesson_name(folder):
    """第 15 课 参数与返回值: the number in front of the basics folder name and the title from basics/course.json."""
    titles = {item["id"]: item["title"] for item in json.loads(BASICS_COURSE.read_text(encoding="utf-8")) if "id" in item}
    return "第 %d 课 %s" % (int(re.match(r"\d+", folder).group()), titles[folder])


PROVIDED_MARK = "===== 老师写好的：前几关的参考答案，不用改 ====="
ANSWER_MARK = "===== 参考答案 ====="


def your_mark(n):
    return "===== 第 %d 关：你来写 =====" % n


def short(language):
    return "py" if language == "python" else "cpp"


def names(language, proj, n):
    """File names in a stage folder: the student's file, the tests and the front end."""
    if language == "python":
        return proj.PROJECT["module"] + ".py", "test_stage%d.py" % n, "play.py"
    return proj.PROJECT["module"] + ".h", "test_stage%d.cpp" % n, "play.cpp"


def doc_lines(fn, lang):
    out = []
    for line in fn["doc"]:
        if line.startswith("PY: "):
            if lang != "py":
                continue
            line = line[4:]
        if line.startswith("CPP: "):
            if lang != "cpp":
                continue
            line = line[5:]
        if lang == "cpp":
            line = line.replace("True", "true").replace("False", "false")
        out.append(line)
    return out


def comment(lines, lang, indent=""):
    mark = "#" if lang == "py" else "//"
    return [(indent + mark + " " + l).rstrip() for l in lines]


def block(fn, lang, answer):
    """One function: its header, the explanation as comments, and the answer or the placeholder."""
    if lang == "py":
        lines = [fn["py_sig"]]
        lines += comment(doc_lines(fn, "py"), "py", "    ")
        lines += fn["py_body"] if answer else fn["py_stub"]
    else:
        lines = [fn["cpp_sig"]]
        lines += comment(doc_lines(fn, "cpp"), "cpp", "    ")
        lines += fn["cpp_body"] if answer else fn["cpp_stub"]
        lines.append("}")
    return "\n".join(lines) + "\n"


def blocks(stages, lang, answer):
    return "\n\n".join(block(fn, lang, answer) for st in stages for fn in st["functions"])


def fn_names(st):
    return [fn["name"] for fn in st["functions"]]


def student_file(proj, st, language):
    lang = short(language)
    n = st["id"]
    me, test, play = names(language, proj, n)
    earlier = [s for s in proj.STAGES if s["id"] < n]
    head = [
        "%s —— 第 %d 关：%s" % (proj.PROJECT["title"], n, st["title"]),
        "你只改最下面“第 %d 关：你来写”里的函数。" % n,
        "函数名和参数不能改：老师的测试按这些名字检查。",
        "写完%s运行 %s 检查；全部通过再运行 %s 玩。" % ("保存，" if lang == "cpp" else "", test, play),
    ]
    if lang == "cpp":
        head.append("这个文件没有 main，不要单独编译它；要编译运行的是 %s。" % test)
    head += [""] + proj.BOARD_PICTURE
    lines = comment(head, lang)
    if lang == "cpp":
        lines += ["", "#include <string>", "using namespace std;"]
    out = "\n".join(lines) + "\n"
    mark = "#" if lang == "py" else "//"
    if earlier:
        out += "\n\n%s %s\n\n" % (mark, PROVIDED_MARK)
        out += blocks(earlier, lang, True)
    out += "\n\n%s %s\n" % (mark, your_mark(n))
    out += "%s 把下面函数里的 return 换成你的代码。现在的 return 只是占位，测试会不通过。\n\n" % mark
    out += blocks([st], lang, False)
    return out


def answer_file(proj, st, language):
    lang = short(language)
    n = st["id"]
    upto = [s for s in proj.STAGES if s["id"] <= n]
    lines = comment(["%s —— 第 1 到 %d 关的参考答案（老师用，不要发给学生）" % (proj.PROJECT["title"], n)], lang)
    if lang == "cpp":
        lines += ["", "#include <string>", "using namespace std;"]
    mark = "#" if lang == "py" else "//"
    return "\n".join(lines) + "\n" + "\n\n%s %s\n\n" % (mark, ANSWER_MARK) + blocks(upto, lang, True)


def lit(v, lang):
    if isinstance(v, tuple) and v[0] == "c":
        return "'%s'" % v[1]
    if isinstance(v, bool):
        if lang == "py":
            return "True" if v else "False"
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    return '"%s"' % v


def call(name, args, lang):
    return "%s(%s)" % (name, ", ".join(lit(a, lang) for a in args))


def py_test(proj, st):
    n = st["id"]
    lines = [
        "# 第 %d 关测试：%s" % (n, st["title"]),
        "# 老师提供，学生不用改。怎么运行见 guide.md。",
        "# 最后一行是 OK：全部通过。最后一行是 FAILED：往上找 FAIL 的那几条，看中文说明和 AssertionError 后面的“你的 != 应该的”。",
        "",
        "import unittest",
    ] + PY_CONSOLE + [
        "",
        "from %s import %s" % (proj.PROJECT["module"], ", ".join(fn_names(st))),
        "",
        "",
        "class TestStage%d(unittest.TestCase):" % n,
    ]
    for k, (name, args, want, what) in enumerate(st["tests"], 1):
        lines += [
            "",
            "    def test_%02d(self):" % k,
            '        """%s"""' % what,
            "        self.assertEqual(%s, %s, \"%s\")" % (call(name, args, "py"), lit(want, "py"), what),
        ]
    lines += ["", "", 'if __name__ == "__main__":', "    unittest.main(verbosity=2)"]
    return "\n".join(lines) + "\n"


def cpp_check_fn(want):
    if isinstance(want, tuple) and want[0] == "c":
        return "check_char"
    if isinstance(want, bool):
        return "check_bool"
    if isinstance(want, int):
        return "check_int"
    return "check_text"


def cpp_test(proj, st):
    n = st["id"]
    lines = [
        "// 第 %d 关测试：%s" % (n, st["title"]),
        "// 老师提供，学生不用改。编译运行这个文件，怎么运行见 guide.md。",
        "// 它会用同一个文件夹里你写的 %s.h。" % proj.PROJECT["module"],
        "",
        '#include "%s.h"' % proj.PROJECT["module"],
        '#include "check.h"',
        "",
        "int main() {",
    ]
    for name, args, want, what in st["tests"]:
        lines.append('    %s(%s, %s, "%s");' % (cpp_check_fn(want), call(name, args, "cpp"), lit(want, "cpp"), what))
    lines += ["    return check_summary();", "}"]
    return "\n".join(lines) + "\n"


def needs(st, language):
    """The basics lessons a stage builds on: [(folder name, what it covers)]."""
    out = []
    for item in st["needs_py" if language == "python" else "needs_cpp"]:
        folder, _, about = item.partition(" ")
        out.append((folder, about))
    return out


def split_example(e):
    note = ""
    if e.endswith("）") and "（" in e:
        k = e.rfind("（")
        note = "：" + e[k + 1:-1]
        e = e[:k]
    return e.strip(), note


def spec(fn, language):
    """A function as the guide and the slides tell it: signature, plain lines and examples."""
    lang = short(language)
    sig = fn["py_sig"] if lang == "py" else fn["cpp_sig"].rstrip(" {")
    plain, examples = [], []
    for line in doc_lines(fn, lang):
        s = line.strip()
        if s.startswith("例子："):
            examples.append(split_example(s[3:]))
        elif examples and line.startswith("      "):
            examples.append(split_example(s))
        else:
            plain.append(s)
    return sig, plain, examples


# Teacher files print Chinese. Through a pipe on a Windows whose code page cannot hold it (an English Windows, or an
# editor that reads the output without setting PYTHONIOENCODING), print fails with UnicodeEncodeError. These lines
# switch only such a stream to UTF-8; consoles and Chinese Windows keep what they have.
PY_CONSOLE = [
    "import sys",
    "",
    "for stream in (sys.stdout, sys.stderr):  # 有的电脑的控制台显示不了中文，换成 UTF-8；学生不用管",
    "    try:",
    "        \"中文\".encode(stream.encoding or \"ascii\")",
    "    except (LookupError, UnicodeEncodeError):",
    "        stream.reconfigure(encoding=\"utf-8\")",
]


def stage_challenge(proj, n, py):
    ch = proj.CHALLENGES[n]
    if ch.startswith("PY: "):
        ch = ch.split("|")[0][4:] if py else ch.split("|")[1][5:]
    return ch


def dev_doc(proj, language):
    """The project's development document, the main thing students read: what we build, the stages in order, and
    for each stage its goal, the functions with their exact names and contracts, examples, the basics lessons it
    needs and how to run its tests. One file; every stage folder ships the same copy as guide.md."""
    py = language == "python"
    lang = "python" if py else "cpp"
    me, test1, play = names(language, proj, 1)
    last = len(proj.STAGES)
    L = ["# %s：开发文档（%s）" % (proj.PROJECT["title"], "Python" if py else "C++"), ""]
    L += ["## 我们要做什么", "", proj.PROJECT["lead"], ""]
    start = proj.PROJECT["start"][language]
    L += ["**开始之前**：先学完基础课件的%s（`%s`），才能做第 1 关。每关还要先学完哪几课，见下面的表。" % (lesson_name(start), start), ""]
    L += ["```"] + proj.BOARD_PICTURE + ["```", ""]
    L += ["## 一关一关来", "", "| 关 | 做什么 | 要写的函数 | 要先学完 |", "| --- | --- | --- | --- |"]
    for st in proj.STAGES:
        L.append("| %d | %s | %s | %s |" % (st["id"], st["title"], "、".join("`%s`" % f for f in fn_names(st)),
                                           "、".join(f for f, _ in needs(st, language))))
    L += ["", "函数名和参数必须照这份文档写，一个字母也不能改：老师的测试按这些名字检查。", ""]
    L += ["## 每关的文件夹", "", "每关一个文件夹（`stage1` 到 `stage%d`），老师用 U 盘发。打开哪一关，就用编辑器打开那一个文件夹。" % last, ""]
    L += ["| 文件 | 谁写 | 做什么 |", "| --- | --- | --- |",
          "| `%s` | **你** | 只改最下面“第 N 关：你来写”的部分；上面是前几关的参考答案，可以看、不用改 |" % me,
          "| `test_stageN.%s` | 老师 | 检查你写对没有 |" % ("py" if py else "cpp")]
    if not py:
        L.append("| `check.h` | 老师 | 测试用的小工具 |")
    L += ["| `%s` | 老师 | 测试全过以后用来玩 |" % play]
    L += ["| %s | 老师 | %s |" % row for row in getattr(proj, "FILES_PY" if py else "FILES_CPP", [])]
    L += ["| `guide.md` | 老师 | 就是这份开发文档 |", ""]
    L += ["## 怎么运行测试", ""]
    if py:
        L += [
            "任选一种（下面的 N 换成第几关）：",
            "",
            "- **PyCharm**：File → Open，选 `stageN` 文件夹。左边右键 `test_stageN.py` → Run。",
            "- **VS Code**：File → Open Folder，选这个文件夹。打开 `test_stageN.py`，点右上角的 ▶（Run Python File）。要先装好 Python 扩展。",
            "- **IDLE**：打开 `test_stageN.py`，按 F5。",
            "- **命令行**：在这个文件夹的地址栏里输入 `cmd` 回车，再输入 `python test_stageN.py`（不行就试 `py test_stageN.py`）。",
            "",
            "怎么看结果：每条测试两行，第二行后面是 `ok` 或 `FAIL`。最后一行是 `OK` 就是全部通过；是 `FAILED (failures=3)` 就是有 3 条没通过，往上找 `FAIL`，看中文说明和 `AssertionError` 后面“你的 != 应该的”。",
            "",
            "如果出现 `ImportError` 或 `NameError`：多半是函数名写错了，或者 `%s` 不在同一个文件夹里。" % me,
            "",
            "不要在文件夹窗口里双击 `.py` 文件：窗口会一闪就关，看不到结果。用编辑器打开再运行。",
        ]
    else:
        L += [
            "任选一种（下面的 N 换成第几关）：",
            "",
            "- **Dev-C++**：文件 → 打开，选 `test_stageN.cpp`，按 F11（编译运行）。要打开的是测试文件，**不是** `%s`（它没有 main，单独编译会出错）。改完 `%s` 先保存，再回到测试文件按 F11。" % (me, me),
            "- **VS Code**：File → Open Folder，选这个文件夹。打开 `test_stageN.cpp`，点右上角的 ▶（Run C/C++ File）。要先装好 C/C++ 扩展和 MinGW 编译器。",
            "- **命令行**：在这个文件夹里输入 `g++ test_stageN.cpp -o test_stageN`，再输入 `test_stageN`。",
            "",
            "怎么看结果：每条一行，`[对]` 或 `[错]`；错的会写“应该是”和“你的是”。最后一行“通过 几 / 几”。",
            "",
            "如果编译出错，说找不到某个函数：多半是函数名写错了，或者 `%s` 不在同一个文件夹里。如果中文显示成乱码，告诉老师（教室电脑的设置问题，不是你写错了）。" % me,
        ]
    L.append("")
    for st in proj.STAGES:
        n = st["id"]
        L += ["## 第 %d 关：%s" % (n, st["title"]), "", st["goal"], ""]
        L += ["- **要先学完**：" + "、".join("%s（%s）" % (f, a) if a else f for f, a in needs(st, language)),
              "- **大约要多久**：" + (st.get("minutes_cpp", st["minutes"]) if not py else st["minutes"]),
              "- **文件夹**：`stage%d`，测试是 `%s`" % (n, names(language, proj, n)[1])]
        if not py:
            L += ["- **先看补页** `%s`" % extra for extra in st.get("extra_cpp", [])]
        L.append("")
        if not py and st.get("note_cpp"):
            L += st["note_cpp"] + [""]
        for fn in st["functions"]:
            sig, plain, examples = spec(fn, language)
            L += ["### `%s`" % fn["name"], "", "```%s" % lang, sig, "```", ""]
            L += ["- " + line for line in plain]
            if examples:
                L += ["", "例子：", ""] + ["- `%s`%s" % e for e in examples]
            L.append("")
        L += ["**测试全过以后**：运行 `%s`。%s" % (play, proj.PLAY_NOTES[n]), ""]
        L += [line for text in st.get("after_py" if py else "after_cpp", []) for line in (text, "")]
        L += ["**做完了？想一想**：" + stage_challenge(proj, n, py), ""]
    return "\n".join(L)


def stage_files(proj, folder, st, language):
    """{file name: text} for the folder students get for one stage. No answers in it."""
    n = st["id"]
    me, test, play = names(language, proj, n)
    templates = Path(folder) / "templates"
    files = {me: student_file(proj, st, language),
             test: py_test(proj, st) if language == "python" else cpp_test(proj, st),
             play: (templates / play).read_text(encoding="utf-8").replace("@STAGE@", str(n)),
             "guide.md": dev_doc(proj, language)}
    if language == "cpp":
        files["check.h"] = (templates / "check.h").read_text(encoding="utf-8")
    # Extra files for one stage, from templates/: a page to read first, another front end, its pictures (bytes).
    for extra in st.get("extra_py" if language == "python" else "extra_cpp", []):
        source = templates / extra
        files[extra] = source.read_bytes() if source.suffix in BINARY else source.read_text(encoding="utf-8").replace("@STAGE@", str(n))
    return files


BINARY = (".png", ".gif", ".wav")


def as_bytes(data):
    """A stage file as it goes on disk or into a zip: text in UTF-8, pictures as they are."""
    return data if isinstance(data, bytes) else data.encode("utf-8")
