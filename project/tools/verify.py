"""Check every stage of every project the way a student would meet it.

Run in project/ after build.py: python3 tools/verify.py   (C++ needs g++ or CXX)

Each stage, with the folder students get (dist/<project>/download/stageN/):
  1. The starter runs or compiles, and its tests fail cleanly: failures, no crash.
  2. The answer passes this stage's tests and every earlier stage's tests.
  3. What the teacher wrote into stage N+1's file is exactly stage N's answer.
  4. The answer uses only what the basics lessons taught by then (Python: ast; C++: keywords).
  5. The front end, with the answer, plays the scripted keys to the end; the last stage with the starter warns, not crashes.
"""
import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import stagefiles as sf  # noqa: E402

# This script's own report is UTF-8 everywhere. The programs it runs get no such help: they print the way they
# would on a student's computer, so a console that cannot show Chinese shows up here.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
LANGUAGE = SITE["language"]
problems = []


def bad(msg):
    problems.append(msg)
    print("  ✗ " + msg)


def good(msg):
    print("  ✓ " + msg)


def load(name):
    spec = importlib.util.spec_from_file_location(name + "_stages", ROOT / name / "stages.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(cmd, cwd, stdin=""):
    # Read the child's output as UTF-8 whatever this machine's code page is; what the child itself can print
    # depends on its own console settings, which is what the Windows job is here to show.
    p = subprocess.run(cmd, cwd=cwd, input=stdin.encode("utf-8"), capture_output=True, timeout=60)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", errors="replace")


def stage_dir(name, n):
    return ROOT / "dist" / name / "download" / ("stage%d" % n)


def answer_path(name, proj, n):
    me = sf.names(LANGUAGE, proj, n)[0]
    return ROOT / name / "answers" / ("stage%d" % n) / me


def temp_copy(name, proj, n):
    d = Path(tempfile.mkdtemp(prefix="%s-%d-" % (name, n)))
    shutil.copytree(stage_dir(name, n), d, dirs_exist_ok=True)
    for k in range(1, n):  # earlier tests too: the answer must not break what came before
        shutil.copy(stage_dir(name, k) / sf.names(LANGUAGE, proj, k)[1], d)
    return d


def use_answer(name, proj, n, d):
    shutil.copy(answer_path(name, proj, n), d / sf.names(LANGUAGE, proj, n)[0])


# ---------------------------------------------------------------- Python

PY_ALLOWED_METHODS = {"count"}  # 13-string-methods
PY_FORBIDDEN = {
    ast.Break: "break（第 27 课）", ast.Continue: "continue", ast.JoinedStr: "f-string（第 28 课）",
    ast.ListComp: "列表推导式", ast.ClassDef: "类", ast.Import: "import", ast.ImportFrom: "import",
    ast.Global: "global", ast.With: "with / 文件", ast.Lambda: "lambda", ast.Try: "try（第 22 课）",
    ast.Dict: "字典（第 17 课）", ast.Tuple: "元组（第 30 课）",
}


def py_syntax(path):
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        found += [what for t, what in PY_FORBIDDEN.items() if isinstance(node, t)]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr not in PY_ALLOWED_METHODS:
            found.append("." + node.func.attr + "()")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("ord", "chr", "list"):
            found.append(node.func.id + "()")
    return sorted(set(found))


def py_summary(out):
    last = [l for l in out.strip().splitlines() if l.strip()]
    return last[-1] if last else ""


def check_python(name, proj, n):
    print("%s 第 %d 关（Python）" % (proj.PROJECT["title"], n))
    d = temp_copy(name, proj, n)
    test = sf.names(LANGUAGE, proj, n)[1]
    code, out = run([sys.executable, test], d)
    s = py_summary(out)
    m = re.match(r"FAILED \(failures=(\d+)\)$", s)
    if code != 0 and m and "errors=" not in s:
        good("起始程序：测试干净地不通过（%s 条失败，0 条报错）" % m.group(1))
    else:
        bad("第 %d 关起始程序：测试结果不对：%s\n%s" % (n, s, out[-800:]))
    use_answer(name, proj, n, d)
    for k in range(1, n + 1):
        code, out = run([sys.executable, sf.names(LANGUAGE, proj, k)[1]], d)
        if code == 0 and py_summary(out) == "OK":
            good("参考答案通过第 %d 关测试" % k)
        else:
            bad("第 %d 关参考答案没通过第 %d 关测试：%s\n%s" % (n, k, py_summary(out), out[-800:]))
    found = py_syntax(answer_path(name, proj, n))
    if found:
        bad("第 %d 关参考答案用到没学过的：%s" % (n, ", ".join(found)))
    else:
        good("参考答案只用学过的语法")
    shutil.rmtree(d)


# ---------------------------------------------------------------- C++

CPP_FORBIDDEN = [
    (r"\bbreak\b", "break"), (r"\bcontinue\b", "continue"), (r"\bvoid\b", "void（第 25 课）"),
    (r"&\s*\w+\s*[,)]", "引用参数（第 25 课）"), (r"\+=", "+="), (r"\bclass\b", "类"),
    (r"\(int\)", "强制转换"), (r"\bconst\b", "const"), (r"\bauto\b", "auto"), (r"\bvector\b", "vector（第 23 课）"),
    (r"\bstruct\b", "结构体（第 19 课）"), (r"#include\s*<(?!string>)", "别的头文件"), (r"\.\w+\(", "成员函数"),
]
CXX = os.environ.get("CXX", "g++")


def cpp_syntax(path):
    code = "\n".join(l for l in path.read_text(encoding="utf-8").splitlines() if not l.strip().startswith("//"))
    return sorted({what for rx, what in CPP_FORBIDDEN if re.search(rx, code)})


def compile_cpp(src, d, std="c++98"):
    exe = d / (Path(src).stem + "_" + std.replace("+", "p") + (".exe" if os.name == "nt" else ""))
    code, out = run([CXX, "-std=" + std, "-Wall", "-pedantic", src, "-o", str(exe)], d)
    return code, out, exe


def check_cpp(name, proj, n):
    print("%s 第 %d 关（C++）" % (proj.PROJECT["title"], n))
    d = temp_copy(name, proj, n)
    test = sf.names(LANGUAGE, proj, n)[1]
    code, out, exe = compile_cpp(test, d)
    if code != 0 or out.strip():
        bad("第 %d 关起始程序编译不干净：%s" % (n, out[:300]))
    else:
        code, out = run([str(exe)], d)
        wrong = len([l for l in out.splitlines() if l.startswith("[错]")])
        if code == 1 and wrong > 0:
            good("起始程序：能编译，测试干净地不通过（%d 条 [错]）" % wrong)
        else:
            bad("第 %d 关起始程序：返回码 %s，[错] %d 条" % (n, code, wrong))
    use_answer(name, proj, n, d)
    for k in range(1, n + 1):
        for std in ("c++98", "c++11"):
            code, out, exe = compile_cpp(sf.names(LANGUAGE, proj, k)[1], d, std)
            if code != 0 or out.strip():
                bad("第 %d 关参考答案 + 第 %d 关测试（%s）编译不干净：%s" % (n, k, std, out[:300]))
                continue
            code, out = run([str(exe)], d)
            if code != 0 or "[错]" in out:
                bad("第 %d 关参考答案没通过第 %d 关测试（%s）" % (n, k, std))
            elif std == "c++98":
                good("参考答案通过第 %d 关测试（C++98、C++11 都编译）" % k)
    found = cpp_syntax(answer_path(name, proj, n))
    if found:
        bad("第 %d 关参考答案用到没学过的：%s" % (n, ", ".join(found)))
    else:
        good("参考答案只用学过的语法")
    shutil.rmtree(d)


# ---------------------------------------------------------------- stages hand over, front end

def check_handover(name, proj):
    print("前后两关一致")
    for n in range(1, len(proj.STAGES)):
        answer = answer_path(name, proj, n).read_text(encoding="utf-8")
        answer = answer[answer.index("\n", answer.index(sf.ANSWER_MARK)) + 1:].strip()
        starter = (stage_dir(name, n + 1) / sf.names(LANGUAGE, proj, n + 1)[0]).read_text(encoding="utf-8")
        given = starter[starter.index("\n", starter.index(sf.PROVIDED_MARK)) + 1:starter.index(sf.your_mark(n + 1))].rsplit("\n", 1)[0].strip()
        if answer == given:
            good("第 %d 关起始程序里老师写好的部分 = 第 %d 关参考答案" % (n + 1, n))
        else:
            bad("第 %d 关起始程序和第 %d 关参考答案不一致" % (n + 1, n))


def play_command(name, proj, n, d):
    play = sf.names(LANGUAGE, proj, n)[2]
    if LANGUAGE == "python":
        return [sys.executable, play]
    code, out, exe = compile_cpp(play, d)
    if code != 0 or out.strip():
        bad("第 %d 关 %s 编译不干净：%s" % (n, play, out[:400]))
        return None
    return [str(exe)]


def check_play(name, proj):
    print("前端 play（配本关参考答案）")
    last = len(proj.STAGES)
    for n in range(1, last + 1):
        d = temp_copy(name, proj, n)
        use_answer(name, proj, n, d)
        cmd = play_command(name, proj, n, d)
        for keys, wants in proj.PLAYS[n] if cmd else []:
            code, out = run(cmd, d, keys)
            out = out.replace("还 true", "还 True").replace("还 false", "还 False")
            missing = [w for w in wants if w not in out]
            if code == 0 and not missing and "Traceback" not in out:
                good("第 %d 关 play：%s" % (n, " / ".join(wants)))
            else:
                bad("第 %d 关 play：返回码 %s，缺少 %s\n%s" % (n, code, missing, out[-600:]))
        shutil.rmtree(d)
    d = temp_copy(name, proj, last)
    cmd = play_command(name, proj, last, d)
    if cmd:
        keys, want = proj.PLAY_UNFINISHED
        code, out = run(cmd, d, keys)
        if code == 0 and want in out and "Traceback" not in out:
            good("第 %d 关 play 配起始程序：给出提示，没有崩溃" % last)
        else:
            bad("第 %d 关 play 配起始程序：%s" % (last, out[-400:]))
    shutil.rmtree(d)



def build_api(n, d):
    """C++: play_web.py talks to api, built from api.cpp the way a student builds it (plain g++, C++98 clean)."""
    if LANGUAGE == "python":
        return
    code, out, exe = compile_cpp("api.cpp", d)
    if code != 0 or out.strip():
        bad("第 %d 关 api.cpp 编译不干净：%s" % (n, out[:300]))
        return
    shutil.copy(exe, d / ("api.exe" if os.name == "nt" else "api"))


def check_web(name, proj):
    """The web front end (play_web.py) checks itself without a browser: it starts its server on 127.0.0.1 and plays
    through the same interface the page uses. With the answer every way of playing ends; with the untouched starter
    it answers with the hint instead of crashing."""
    stages = [st["id"] for st in proj.STAGES if (stage_dir(name, st["id"]) / "play_web.py").exists()]
    if not stages:
        return
    print("网页前端 play_web（--selftest）")
    for n in stages:
        d = temp_copy(name, proj, n)
        use_answer(name, proj, n, d)
        build_api(n, d)
        code, out = run([sys.executable, "play_web.py", "--selftest"], d)
        if code == 0 and "自检通过" in out and "Traceback" not in out:
            good("第 %d 关 play_web 配参考答案：%s" % (n, out.strip().splitlines()[-1]))
        else:
            bad("第 %d 关 play_web 配参考答案：返回码 %s\n%s" % (n, code, out[-600:]))
        shutil.rmtree(d)
        d = temp_copy(name, proj, n)
        build_api(n, d)
        code, out = run([sys.executable, "play_web.py", "--selftest"], d)
        if code != 0 and "test_stage%d.%s 全部通过" % (n, sf.short(LANGUAGE)) in out and "Traceback" not in out:
            good("第 %d 关 play_web 配起始程序：给出提示，没有崩溃" % n)
        else:
            bad("第 %d 关 play_web 配起始程序：返回码 %s\n%s" % (n, code, out[-600:]))
        shutil.rmtree(d)

def main():
    for name in SITE["projects"]:
        proj = load(name)
        for st in proj.STAGES:
            (check_python if LANGUAGE == "python" else check_cpp)(name, proj, st["id"])
        check_handover(name, proj)
        check_play(name, proj)
        check_web(name, proj)
    print()
    if problems:
        print("有 %d 个问题：" % len(problems))
        for p in problems:
            print(" - " + p.splitlines()[0])
        sys.exit(1)
    print("全部检查通过。")


if __name__ == "__main__":
    main()
