from pydantic import BaseModel
from typing import Optional
import json

class Student(BaseModel):
    name: str
    score: int

alice = Student(name="Alice", score=95)
print(alice)
print(alice.name)
print(alice.score)


try:
    bad_alice = Student(name="Bob", score="ninety-five")
except Exception as e:
    print(f"Error caught: {type(e).__name__}: {e}")

print("-" * 50)

coerced = Student(name="Charlie", score="92")
print(coerced.score)
print(type(coerced.score))

print("-" * 50)

class Address(BaseModel):
    street: str
    city: str
    zip: str

class Person(BaseModel):
    name: str
    age: int
    address: Address

print("-" * 50)

p = Person(
    name="Prashant",
    age=32,
    address={
        "street": "123 Main St",
        "city": "Anytown",
        "zip": "12345"
    }
)

print(p)
print("Person's address:", p.address.street, p.address.city, p.address.zip)


print("-" * 50)

class UserProfile(BaseModel):
    username: str
    email: str
    bio: str | None = None
    tags: list[str] = []
    follower_count: int = 0
    is_verified: bool = True

user1 = UserProfile(
    username = "Prashant",
    email = "pras@gmail.com",
)

print(f"user1: {user1}")

user2 = UserProfile(
    username = "Priya",
    email = "priya@gmail.com",
    bio = "Software Engineer",
    tags = ["Python", "Java", "C++"],
    follower_count = 100,
    is_verified = True
)

print(f"user2: {user2}")

print("\n" + "-" * 50)

user1_json = user1.model_dump_json()
user1_dict = user1.model_dump()

print(f"user1_json: {user1_json}")
print(f"user1_dict: {user1_dict}")

user2_json = user2.model_dump_json()
user2_dict = user2.model_dump()

print(f"user2_json: {user2_json}")
print(f"user2_dict: {user2_dict}")

parsed = UserProfile.model_validate_json(user2_json)
print(f"parsed: {parsed}")


