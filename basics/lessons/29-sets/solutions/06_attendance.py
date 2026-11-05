everyone = set(input().split())
signed = set(input().split())
print("到了", len(everyone & signed), "人")
missing = everyone - signed
if len(missing) == 0:
    print("全到了")
else:
    print("没到：" + " ".join(sorted(missing)))
