mine = set(input().split())
yours = set(input().split())
both = mine & yours
if len(both) == 0:
    print("没有一样的爱好")
else:
    print("都喜欢：" + " ".join(sorted(both)))
