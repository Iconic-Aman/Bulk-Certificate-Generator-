# import json
# import random
# from datetime import date, timedelta

# first_names = [
#     "Aarav", "Aditi", "Arjun", "Ananya",
#     "Benjamin", "Bella", "Brandon", "Bianca",
#     "Charlie", "Chloe", "Christopher", "Clara",
#     "Daniel", "Diya", "David", "Diana",
#     "Ethan", "Emily", "Evan", "Ella",
#     "Finn", "Freya", "Felix", "Faith",
#     "Gabriel", "Grace", "George", "Gia",
#     "Henry", "Hannah", "Hudson", "Hazel",
#     "Isaac", "Isabella", "Ian", "Ivy",
#     "Jacob", "Julia", "James", "Jasmine",
#     "Kai", "Kiara", "Kevin", "Katherine",
#     "Liam", "Lily", "Lucas", "Layla",
#     "Mason", "Mia", "Michael", "Maya",
#     "Noah", "Nora", "Nathan", "Naomi",
#     "Oliver", "Olivia", "Oscar", "Ophelia",
#     "Peter", "Priya", "Patrick", "Penelope",
#     "Quinn", "Queenie", "Quentin", "Quincy",
#     "Ryan", "Ruby", "Robert", "Riya",
#     "Samuel", "Sofia", "Sebastian", "Sneha",
#     "Thomas", "Tara", "Theodore", "Trisha",
#     "Umar", "Uma", "Uday", "Uri",
#     "Victor", "Victoria", "Vincent", "Vera",
#     "William", "Willow", "Wesley", "Wren",
#     "Xavier", "Xena", "Xander", "Ximena",
#     "Yash", "Yara", "Yusuf", "Yvonne",
# ]

# last_names = [
#     "Sharma", "Verma", "Patel", "Singh",
#     "Carter", "Bennett", "Cooper", "Morgan",
#     "Reed", "Parker", "Brooks", "Hayes",
#     "Miller", "Wilson", "Turner", "Collins",
#     "Foster", "Mitchell", "Bailey", "Ward",
#     "Anderson", "Thomas", "Jackson", "White",
#     "Harris", "Martin", "Lewis", "Young",
#     "Hall", "Allen", "King", "Scott",
# ]

# # Generate exactly 100 distinct names
# random.seed(42)
# random.shuffle(first_names)
# random.shuffle(last_names)

# people = []
# used_names = set()
# used_emails = set()
# today = date.today()

# for first in first_names:
#     for last in last_names:
#         full_name = f"{first} {last}"

#         if full_name in used_names:
#             continue

#         email = (
#             f"{first.lower()}.{last.lower()}"
#             f"{len(people) + 1:03d}@example.com"
#         )

#         if email in used_emails:
#             continue
#         days_ago = random.randint(0, 6)
#         issue_date = (
#             today - timedelta(days=days_ago)
#         ).isoformat()
        
#         people.append({
#             "id": len(people) + 1,
#             "name": full_name,
#             "email": email,
#             "issue_date": issue_date
#         })

#         used_names.add(full_name)
#         used_emails.add(email)

#         if len(people) == 100:
#             break

#     if len(people) == 100:
#         break

# # Save to JSON file
# with open("people.json", "w", encoding="utf-8") as file:
#     json.dump(people, file, indent=4, ensure_ascii=False)

# print(f"Successfully generated {len(people)} people.")
# print("Unique names:", len(used_names))
# print("Unique emails:", len(used_emails))
# print("File saved as people.json")

import json
import random
from datetime import date, timedelta

# Read the existing JSON file
with open("people.json", "r", encoding="utf-8") as file:
    users = json.load(file)

# Generate a random issue date within the last 7 days
days_ago = random.randint(0, 6)
issue_date = (date.today() - timedelta(days=days_ago)).isoformat()

# Transform all users into the required structure
result = {
    "title": "string",
    "issued_by": "string",
    "issue_date": issue_date,
    "recipients": [
        {
            "name": user["name"],
            "email": user["email"]
        }
        for user in users
    ]
}

# Save the converted data to a new file
with open("converted.json", "w", encoding="utf-8") as file:
    json.dump(result, file, indent=2, ensure_ascii=False)

print("Conversion completed! Saved to converted.json")
print(f"Issue date: {issue_date}")
