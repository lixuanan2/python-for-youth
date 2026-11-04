def grade(score):
    if score >= 90:
        return "优秀"
    if score >= 60:
        return "及格"
    return "不及格"
score = int(input())
print(grade(score))
