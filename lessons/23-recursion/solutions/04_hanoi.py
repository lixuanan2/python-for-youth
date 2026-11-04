def hanoi(n, start, middle, end):
    if n == 1:
        print(start, "->", end)
    else:
        hanoi(n - 1, start, end, middle)
        print(start, "->", end)
        hanoi(n - 1, middle, start, end)
hanoi(int(input()), "A", "B", "C")
