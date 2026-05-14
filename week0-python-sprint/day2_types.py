name: str = "Monica"  # String
age: int = 25  # Integer
is_student: bool = True  # Boolean
height: float = 5.6  # Float
nothing: None = None  # None Type

skills: list[str] = ["Python", "Java", "C++"]
grades: dict[str, int] = {"Math": 90, "Science": 80, "English": 70}
coordinate: tuple[int, int] = (10, 20)
unique_tags: set[str] = {"Python", "Java", "C++"}

print(name)
print(age)
print(is_student)
print(height)
print(nothing)
print(skills)
print(grades)
print(coordinate)
print(unique_tags)

print("-" * 30)

middle_name: str | None = None
middle_name = "Abhay"
middle_name = None

score: float | int = 88.5
score = 88.66
print(type(score))

print("-" * 30)


def find_user(user_id: int) -> dict[str, str] | None:
    fake_users = {
        101: {"name": "Alice", "email": "[EMAIL_ADDRESS]"},
        102: {"name": "Bob", "email": "[EMAIL_ADDRESS]"},
    }
    return fake_users.get(user_id)


user = find_user(101)
print(user)
print(find_user(101))
print(find_user(105))

print("-" * 30)

if user is not None:
    print(user["name"])
else:
    print("User not found")

# print(user["name"])


def filter_high_scorers(
    students: list[dict[str, int | str]], threshold: int = 80
) -> list[str]:
    """Return names of students scoring at or above threshold."""
    return [
        s["name"]
        for s in students
        if isinstance(s["score"], int) and s["score"] >= threshold
    ]


students = [
    {"name": "Aarav", "score": 95},
    {"name": "Priya", "score": 78},
    {"name": "Vibha", "score": 88},
]

top = filter_high_scorers(students, threshold=85)
print(top)


# What happens when data is wrong?
bad_students = [
    {"name": "Aarav", "score": "ninety-five"},  # score is a string, oops
    {"name": "Priya"},  # missing score entirely
    {"name": 42, "score": 88},  # name is an int, oops
]

# Pylance won't catch these — the dict is loosely typed.
# At runtime, our function will either crash or silently misbehave.
# Try it and see:

try:
    top = filter_high_scorers(bad_students, threshold=80)
    print(top)
except (KeyError, TypeError) as e:
    print(f"Error caught: {type(e).__name__}: {e}")
