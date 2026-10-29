import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

rng = random.Random(42)

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

REFERENCE_TIME = datetime(2026, 10, 29)

TOPICS = {
    "technology": [
        "artificial intelligence", "web development",
        "cybersecurity", "cloud computing", "robotics", "Competetive Programming"
    ],
    "science": [
        "space exploration", "quantum physics",
        "climate science", "genetics", "ocean research"
    ],
    "sports": [
        "football", "cricket", "basketball",
        "tennis", "athletics"
    ],
    "finance": [
        "investing", "budgeting", "banking",
        "financial markets", "business"
    ],
    "entertainment": [
        "movies", "music", "gaming",
        "animation", "photography"
    ],
}

CATEGORIES = list(TOPICS)

FIRST_NAMES = [
    "Aarav", "Rahul", "Soham", "Priya",
    "Rohan", "Sara", "Kabir", "Meera"
]

LAST_NAMES = [
    "Sharma", "Kumar", "Patel", "Singh",
    "Das", "Goyal", "Gupta", "Rao"
]


def random_datetime(start, end):
    """Generate a time within the supplied range."""
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randint(0, seconds))


def generate_users(count):
    users = []

    for user_id in range(1, count + 1):
        name = (
            f"{rng.choice(FIRST_NAMES)} "
            f"{rng.choice(LAST_NAMES)}"
        )

        interests = rng.sample(
            CATEGORIES,
            k=rng.randint(1, 3)
        )

        joined_at = random_datetime(
            REFERENCE_TIME - timedelta(days=365),
            REFERENCE_TIME
        )

        users.append({
            "user_id": user_id,
            "name": name,
            "email": f"user{user_id}@example.com",
            "interests": interests,
            "created_at": joined_at.isoformat()
        })

    return users


def generate_items(count):
    items = []

    title_templates = [
        "A beginner's guide to {topic}",
        "Understanding {topic}",
        "Exploring the basics of {topic}",
        "Five questions about {topic}",
        "How to get started with {topic}"
    ]

    for item_id in range(1, count + 1):
        category = rng.choice(CATEGORIES)
        topic = rng.choice(TOPICS[category])

        title = rng.choice(title_templates).format(topic=topic)

        published_at = random_datetime(
            REFERENCE_TIME - timedelta(days=730),
            REFERENCE_TIME
        )

        items.append({
            "item_id": item_id,
            "title": title,
            "description": (
                f"A mock article about {topic}, "
                f"covering introductory ideas and examples."
            ),
            "category": category,
            "tags": [category, topic],
            "published_at": published_at.isoformat()
        })

    return items

def generate_interactions(users, items, count=5000):
    if count < 0:
        raise ValueError("count must be non-negative")

    if count == 0:
        return []

    if not users or not items:
        raise ValueError("Users and items cannot be empty")

    interaction_rng = random.Random(123)

    shuffled_users = users.copy()
    interaction_rng.shuffle(shuffled_users)

    cold_user_count = int(len(users) * 0.10)
    active_users = shuffled_users[cold_user_count:]

    profiles = []

    for user in active_users:
        signup_time = datetime.fromisoformat(user["created_at"])

        latest_click_time = REFERENCE_TIME - timedelta(minutes=10)

        matching_items = []
        other_items = []

        for item in items:
            published_time = datetime.fromisoformat(
                item["published_at"]
            )
            earliest_time = max(signup_time, published_time)
            if earliest_time > latest_click_time:
                continue
            candidate = (item, earliest_time)
            if item["category"] in user["interests"]:
                matching_items.append(candidate)
            else:
                other_items.append(candidate)
        if matching_items or other_items:
            profiles.append({
                "user_id": user["user_id"],
                "matching_items": matching_items,
                "other_items": other_items,
                "activity_weight": interaction_rng.choices(
                    [1, 3, 8],
                    weights=[40, 40, 20],
                    k=1
                )[0]
            })

    if not profiles:
        raise ValueError(
            "No users have items available within the date range"
        )
    activity_weights = [
        profile["activity_weight"] for profile in profiles
    ]
    interactions = []
    while len(interactions) < count:
        profile = interaction_rng.choices(
            profiles,
            weights=activity_weights,
            k=1
        )[0]

        if interaction_rng.random() < 0.70:
            pool = (
                profile["matching_items"]
                or profile["other_items"]
            )
        else:
            pool = (
                profile["other_items"]
                or profile["matching_items"]
            )
        item, earliest_time = interaction_rng.choice(pool)
        latest_click_time = REFERENCE_TIME - timedelta(minutes=10)
        available_seconds = int(
            (latest_click_time - earliest_time).total_seconds()
        )
        click_time = earliest_time + timedelta(
            seconds=interaction_rng.randint(0, available_seconds)
        )
        interactions.append({
            "user_id": profile["user_id"],
            "item_id": item["item_id"],
            "event_type": "click",
            "timestamp": click_time
        })
        followup = interaction_rng.choices(
            [None, "like", "save"],
            weights=[60, 25, 15],
            k=1
        )[0]

        if followup is not None and len(interactions) < count:
            followup_time = click_time + timedelta(
                seconds=interaction_rng.randint(5, 300)
            )

            interactions.append({
                "user_id": profile["user_id"],
                "item_id": item["item_id"],
                "event_type": followup,
                "timestamp": followup_time
            })

    interactions.sort(key=lambda event: event["timestamp"])

    for interaction_id, event in enumerate(interactions, start=1):
        event["interaction_id"] = interaction_id
        event["timestamp"] = event["timestamp"].isoformat()

    return interactions

def save_csv(filename, records):
    if not records:
        return

    path = OUTPUT_DIR / filename

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(records[0])
        )
        writer.writeheader()

        for record in records:
            row = {
                key: json.dumps(value)
                if isinstance(value, list)
                else value
                for key, value in record.items()
            }
            writer.writerow(row)

    print(f"Saved {len(records)} records to {path}")


if __name__ == "__main__":
    users = generate_users(100)
    items = generate_items(500)

    interactions = generate_interactions(
        users,
        items,
        count=5000
    )

    save_csv("users.csv", users)
    save_csv("items.csv", items)
    save_csv("interactions.csv", interactions)

    assert len(interactions) == 5000

    users_with_history = {
        event["user_id"] for event in interactions
    }

    print(f"\nTotal interactions: {len(interactions)}")
    print(f"Users with history: {len(users_with_history)}")
    print(
        "Users without history:",
        len(users) - len(users_with_history)
    )

    print("\nFirst five interactions:")

    for event in interactions[:5]:
        print(event)