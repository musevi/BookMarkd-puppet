from __future__ import annotations
import random
from datetime import date, timedelta
from typing import List, Tuple

from extensions import db
from models import User, Book, Club, UserBook, UserClub, BookGoal, PageGoal, HourGoal

# ---------------------------
# Configurable “big seed” knobs
# ---------------------------
NUM_USERS = 50          # total users to create
NUM_BOOKS = 40          # total books to create
NUM_CLUBS = 6           # total clubs to create
MAX_BOOKS_PER_USER = 8  # each user will have up to this many books
MAX_CLUBS_PER_USER = 2  # each user will join up to this many clubs
GOAL_USERS_FRACTION = 0.75  # ~75% of users get goals

# Hour goals: about this fraction of users get 1–2 hour goals
HOUR_GOAL_USERS_FRACTION = 0.7
HOUR_GOAL_CHOICES = [5, 10, 15, 20, 25]  # num_hours pool

# For reproducibility across runs (optional)
RANDOM_SEED = 42

# ---------------------------
# Sample data pools
# ---------------------------
FIRST_NAMES = [
    "Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Hank",
    "Ivy", "Jack", "Kara", "Liam", "Mia", "Noah", "Olivia", "Pete",
    "Quinn", "Riley", "Sara", "Theo", "Uma", "Vera", "Wade", "Zara"
]

LAST_NAMES = [
    "Anderson", "Brown", "Carter", "Davis", "Evans", "Foster", "Garcia",
    "Hughes", "Iverson", "Johnson", "Kim", "Lopez", "Miller", "Nolan",
    "Owens", "Patel", "Quincy", "Reed", "Smith", "Turner", "Usman",
    "Vega", "Williams", "Xu", "Young", "Zimmer"
]

GENRES = [
    "Fantasy", "Sci-Fi", "Mystery", "Romance", "Nonfiction", "History",
    "Biography", "Self-Help", "Programming", "YA", "Horror", "Literary"
]

CLUB_THEMES = [
    ("Readers United", "General"),
    ("Midnight Mystery Crew", "Mystery"),
    ("Space & Sci-Fi Circle", "Sci-Fi"),
    ("Rom-Com Readers", "Romance"),
    ("Code & Coffee", "Programming"),
    ("Page Turners", "General"),
    ("History Buffs", "History"),
    ("Horror House", "Horror"),
]

PROGRAMMING_TITLES = [
    ("Clean Code", "Robert C. Martin", 464),
    ("The Pragmatic Programmer", "Andrew Hunt, David Thomas", 352),
    ("Fluent Python", "Luciano Ramalho", 792),
    ("Design Patterns", "Erich Gamma et al.", 395),
    ("You Don’t Know JS Yet", "Kyle Simpson", 143),
]

NONFICTION_TITLES = [
    ("Atomic Habits", "James Clear", 320),
    ("Sapiens", "Yuval Noah Harari", 498),
    ("Educated", "Tara Westover", 352),
    ("Thinking, Fast and Slow", "Daniel Kahneman", 512),
    ("Range", "David Epstein", 352),
]

FICTION_TITLES = [
    ("The Night Circus", "Erin Morgenstern", 512),
    ("Dune", "Frank Herbert", 896),
    ("The Name of the Wind", "Patrick Rothfuss", 662),
    ("The Silent Patient", "Alex Michaelides", 336),
    ("Project Hail Mary", "Andy Weir", 496),
    ("The Seven Husbands of Evelyn Hugo", "Taylor Jenkins Reid", 400),
    ("Circe", "Madeline Miller", 400),
]

# ---------------------------
# Utilities
# ---------------------------
def _rand_date_within(days: int = 365) -> date:
    """Random date within the last N days."""
    return date.today() - timedelta(days=random.randint(0, days))

def _uniq_usernames(n: int) -> List[str]:
    base = set()
    while len(base) < n:
        username = f"{random.choice(FIRST_NAMES)}{random.choice(LAST_NAMES)}".lower()
        # add a suffix sometimes to reduce collision risk
        if random.random() < 0.35:
            username += str(random.randint(1, 999))
        base.add(username)
    return list(base)

def _email_for(username: str) -> str:
    domains = ["example.com", "mail.test", "students.edu"]
    return f"{username}@{random.choice(domains)}"

def _random_title() -> Tuple[str, str, int, str]:
    """Return title, author, pages, genre."""
    bucket = random.choice(["prog", "nonfic", "fic", "compiled"])
    if bucket == "prog":
        title, author, pages = random.choice(PROGRAMMING_TITLES)
        return title, author, pages, "Programming"
    if bucket == "nonfic":
        title, author, pages = random.choice(NONFICTION_TITLES)
        return title, author, pages, "Nonfiction"
    if bucket == "fic":
        title, author, pages = random.choice(FICTION_TITLES)
        # map loosely to a fiction subgenre
        return title, author, pages, random.choice(["Fantasy", "Sci-Fi", "Mystery", "Romance", "Horror", "YA", "Literary"])
    # compiled synthetic
    title = f"{random.choice(['Shadow', 'Silver', 'Crimson', 'Fallen', 'Hidden', 'Last'])} " \
            f"{random.choice(['Empire', 'Secret', 'Voyage', 'Garden', 'Library', 'Algorithm'])}"
    author = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    pages = random.randint(180, 900)
    genre = random.choice(GENRES)
    return title, author, pages, genre

# ---------------------------
# Creators
# ---------------------------
def _create_users(n: int) -> List[User]:
    usernames = _uniq_usernames(n)
    users: List[User] = []
    for username in usernames:
        user = User(username=username, email=_email_for(username), password_hash="")
        user.set_password("password123")  # default demo password
        users.append(user)
    db.session.add_all(users)
    db.session.commit()
    return users

def _create_books(n: int) -> List[Book]:
    books: List[Book] = []
    # Prefer known titles, then synthesize more if needed
    pool = []
    for title, author, page in PROGRAMMING_TITLES + NONFICTION_TITLES + FICTION_TITLES:
        pool.append((title, author, page, None))  # genre None means we'll map below
    # Add synthetic titles to reach n
    while len(pool) < n:
        title, author, page, genre = _random_title()
        pool.append((title, author, page, genre))

    random.shuffle(pool)
    for i in range(n):
        title, author, page, genre = pool[i]
        genre = genre if genre else ( "Programming" if (title, author, page) in PROGRAMMING_TITLES else
                              "Nonfiction" if (title, author, page) in NONFICTION_TITLES else
                              random.choice(["Fantasy", "Sci-Fi", "Mystery", "Romance", "Horror", "YA", "Literary"]))
        books.append(Book(title=title, author=author, page_count=page, genre=genre))
    db.session.add_all(books)
    db.session.commit()
    return books

def _create_clubs(n: int) -> List[Club]:
    # Use predefined then synthesize names if needed
    clubs: List[Club] = []
    base = CLUB_THEMES[:]
    while len(base) < n:
        base.append((
            f"{random.choice(['Book', 'Novel', 'Chapter', 'Leaf', 'Paper'])} {random.choice(['Club', 'Society', 'Collective', 'Guild'])}",
            random.choice(GENRES)
        ))
    for name, genre in base[:n]:
        # Generate a slug from the name
        slug = name.strip().lower().replace(' ', '-')
        clubs.append(Club(club_name=name, slug=slug, description=f"A club about {genre}"))
    db.session.add_all(clubs)
    db.session.commit()
    return clubs

# ---------------------------
# Linkers / Relations
# ---------------------------
def _link_user_books(users: List[User], books: List[Book]) -> None:
    rows: List[UserBook] = []
    for user in users:
        k = random.randint(2, MAX_BOOKS_PER_USER)
        picks = random.sample(books, k=k)
        for book in picks:
            rating = round(random.uniform(2.5, 5.0), 1) if random.random() < 0.8 else None
            rows.append(UserBook(
                user_id=user.user_id,
                book_id=book.book_id,
                add_date=_rand_date_within(240),
                user_rating=rating
            ))
    db.session.add_all(rows)
    db.session.commit()

def _link_user_clubs(users: List[User], clubs: List[Club]) -> None:
    rows: List[UserClub] = []
    for user in users:
        k = random.randint(0, MAX_CLUBS_PER_USER)
        if k == 0:
            continue
        picks = random.sample(clubs, k=k)
        for club in picks:
            rows.append(UserClub(user_id=user.user_id, club_id=club.club_id))
    db.session.add_all(rows)
    db.session.commit()

# ---------------------------
# Goals
# ---------------------------
def _create_goals(users: List[User]) -> None:
    """Create book, page, and hour goals for subsets of users. """
    book_goal_rows: List[BookGoal] = []
    page_goal_rows: List[PageGoal] = []
    hour_goal_rows: List[HourGoal] = []

    for user in users:
        # Book/Page goals cohort
        if random.random() <= GOAL_USERS_FRACTION:
            # 1–2 book goals
            for _ in range(random.randint(1, 2)):
                book_goal_rows.append(BookGoal(
                    user_id=user.user_id,
                    description=random.choice([
                        "Read more sci-fi", "Finish a trilogy", "Explore non-fiction",
                        "Try a new genre", "Classics month"
                    ]),
                    num_books=random.choice([3, 5, 10, 12])
                ))
            # 1–2 page goals
            for _ in range(random.randint(1, 2)):
                page_goal_rows.append(PageGoal(
                    user_id=user.user_id,
                    description=random.choice([
                        "Daily 20 pages", "Weekend long reads", "Commute reading",
                        "Bedtime chapter", "Morning routine pages"
                    ]),
                    num_pages=random.choice([300, 500, 800, 1000, 1500])
                ))

        if random.random() <= HOUR_GOAL_USERS_FRACTION:
            for _ in range(random.randint(1, 2)):
                hour_goal_rows.append(HourGoal(
                    user_id=user.user_id,
                    description=random.choice([
                        "Read 5 hours per week",
                        "Nightly reading habit",
                        "Weekend marathon",
                        "Lunch-break reading challenge",
                        "Daily 1-hour focus time"
                    ]),
                    num_hours=random.choice(HOUR_GOAL_CHOICES)
                ))

    db.session.add_all(book_goal_rows + page_goal_rows + hour_goal_rows)
    db.session.commit()

# ---------------------------
# Public entrypoint
# ---------------------------
def seed_db() -> None:
    """
    Populate the database with a large but sensible demo dataset.
    Idempotent: if Users exist, we assume seeding already happened.
    """
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)

    # Idempotency guard
    if User.query.first():
        return

    users = _create_users(NUM_USERS)
    books = _create_books(NUM_BOOKS)
    clubs = _create_clubs(NUM_CLUBS)

    _link_user_books(users, books)
    _link_user_clubs(users, clubs)
    _create_goals(users)

    # Optional: ensure every user has at least one relation for nicer demos
    _ensure_minimum_links(users, books, clubs)

def _ensure_minimum_links(users: List[User], books: List[Book], clubs: List[Club]) -> None:
    """Soft pass to give isolated users a book or a club."""
    # users without any books
    lonely_users = [u for u in users if not u.user_books]
    for user in lonely_users:
        b = random.choice(books)
        db.session.add(UserBook(
            user_id=user.user_id,
            book_id=b.book_id,
            add_date=_rand_date_within(120),
            user_rating=round(random.uniform(3.0, 5.0), 1)
        ))

    # users without any clubs (only if clubs exist)
    if clubs:
        clubless = [u for u in users if not u.user_clubs]
        for user in clubless:
            c = random.choice(clubs)
            db.session.add(UserClub(user_id=user.user_id, club_id=c.club_id))

    db.session.commit()
