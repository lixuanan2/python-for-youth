secret = int(input())
lo = 1
hi = 100
guess = 0
while guess != secret:
    guess = (lo + hi) // 2
    print(guess)
    if guess < secret:
        lo = guess + 1
    elif guess > secret:
        hi = guess - 1
