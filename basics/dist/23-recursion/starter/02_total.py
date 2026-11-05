def total(n):
    if n == 1:
        return 1
    return n + total(n - 1)
print(total(int(input())))
