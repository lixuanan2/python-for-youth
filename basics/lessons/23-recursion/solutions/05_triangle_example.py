def triangle(n):
    if n > 0:
        triangle(n - 1)
        print("*" * n)
triangle(int(input()))
