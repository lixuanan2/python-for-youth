def digit_sum(n):
    if n < 10:
        return n
    return n % 10 + digit_sum(n // 10)


print(digit_sum(int(input())))
