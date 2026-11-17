page = int(input())
lo = 1
hi = 500
mid = 0
while mid != page:
    mid = (lo + hi) // 2
    if mid < page:
        print("翻到", mid, "页，往后翻")
        lo = mid + 1
    elif mid > page:
        print("翻到", mid, "页，往前翻")
        hi = mid - 1
print("找到第", page, "页")
