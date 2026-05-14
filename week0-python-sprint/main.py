def calculate_grade(score: int) -> str:
    """return a grade for score."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


# print(calculation_grade(95))
# print(calculation_grade(85))
# print(calculation_grade(75))
# print(calculation_grade(65))
# print(calculation_grade(55))


def main() -> None:
    students = [
        {"name": "Aarav", "score": 95},
        {"name": "Priya", "score": 78},
        {"name": "Rohan", "score": 62},
        {"name": "Sneha", "score": 45},
        {"name": "Vibha", "score": 88},
        {"name": "Rahul", "score": 60},
    ]

    # Add a grade to each student
    for student in students:
        student["grade"] = calculate_grade(student["score"])

    # Print results header
    print("Class results:")
    print("-" * 30)

    sorted_students = sorted(students, key=lambda x: x["score"], reverse=True)

    # Print each student
    for student in sorted_students:
        print(f"{student['name']:<10} {student['score']:>3}  {student['grade']}")

    # top performers
    top_performers = [s for s in sorted_students if s["grade"] in ("A", "B")]
    print("Top Performers:")
    print("-" * 30)
    for student in top_performers:
        print(f"{student['name']:<10} {student['score']:>3}  {student['grade']}")

    # calculate average
    total_score = sum(student["score"] for student in students)
    average_score = total_score / len(students)

    print("-" * 30)
    print(f"Average score: {average_score:.2f}")

    # find highest and lowest score
    highest_score = max(student["score"] for student in students)
    lowest_score = min(student["score"] for student in students)

    print("-" * 30)
    print(f"Highest score: {highest_score}")
    print(f"Lowest score: {lowest_score}")


if __name__ == "__main__":
    main()
