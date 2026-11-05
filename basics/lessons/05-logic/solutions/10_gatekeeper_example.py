word = input()
age = int(input())
if word == "芝麻开门" and age >= 10:
    print("欢迎进入秘密基地")
elif word == "芝麻开门" or age >= 10:
    print("还差一点，再试试")
else:
    print("门没有开")
