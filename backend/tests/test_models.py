from models import User, UserClub, Club, Book, BookGoal, ClubPost, ClubComment, UserBook, HourGoal, PageGoal
from extensions import db

class TestUserModel:
    """Tests for User model"""
    
    def test_create_user(self, app):
        """Test creating a user"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.password_hash is not None
            assert user.password_hash != 'password123'
    
    def test_password_hashing(self, app):
        """Test password is properly hashed"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            
            assert user.check_password('password123') is True
            assert user.check_password('wrongpassword') is False
    
    def test_user_repr(self, app):
        """Test user string representation"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            assert 'testuser' in repr(user)


class TestBookModel:
    def test_create_book(self, app):
        """Test creating a Book instance"""
        with app.app_context():
            book = Book(title='Test Book', author='Author Name', page_count=123, genre='Fiction')
            db.session.add(book)
            db.session.commit()
            assert book.book_id is not None
            assert book.title == 'Test Book'
            assert book.author == 'Author Name'
            assert book.page_count == 123
            assert book.genre == 'Fiction'
            assert 'Test Book' in repr(book)


class TestUserBookModel:
    def test_create_user_book(self, app):
        with app.app_context():
            user = User(username='userbookuser', email='userbook@example.com')
            user.set_password('password')
            book = Book(title='UserBook Test', author='Author', page_count=200)
            db.session.add(user)
            db.session.add(book)
            db.session.commit()
            user_book = UserBook(user_id=user.user_id, book_id=book.book_id, page_progress=50, user_rating=4.5)
            db.session.add(user_book)
            db.session.commit()
            assert user_book.id is not None
            assert user_book.user_id == user.user_id
            assert user_book.book_id == book.book_id
            assert user_book.page_progress == 50
            assert user_book.user_rating == 4.5
            assert str(user_book).startswith('<UserBook user=')


class TestBookGoalModel:
    def test_create_book_goal(self, app):
        """Test creating a BookGoal instance"""
        with app.app_context():
            user = User(username='goaluser', email='goal@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            goal = BookGoal(user_id=user.user_id, description='Read 5 books', num_books=5)
            db.session.add(goal)
            db.session.commit()
            assert goal.goal_id is not None
            assert goal.user_id == user.user_id
            assert goal.description == 'Read 5 books'
            assert goal.num_books == 5
            assert goal.progress == 0.0
            assert 'Read 5 books' in repr(goal)


class TestHourGoalModel:
    def test_create_hour_goal(self, app):
        with app.app_context():
            user = User(username='hourgoaluser', email='hourgoal@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            goal = HourGoal(user_id=user.user_id, description='Read 20 hours', num_hours=20)
            db.session.add(goal)
            db.session.commit()
            assert goal.goal_id is not None
            assert goal.user_id == user.user_id
            assert goal.description == 'Read 20 hours'
            assert goal.num_hours == 20
            assert goal.progress == 0.0
            assert 'Read 20 hours' in repr(goal)


class TestPageGoalModel:
    def test_create_page_goal(self, app):
        with app.app_context():
            user = User(username='pagegoaluser', email='pagegoal@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            goal = PageGoal(user_id=user.user_id, description='Read 1000 pages', num_pages=1000)
            db.session.add(goal)
            db.session.commit()
            assert goal.goal_id is not None
            assert goal.user_id == user.user_id
            assert goal.description == 'Read 1000 pages'
            assert goal.num_pages == 1000
            assert goal.progress == 0.0
            assert 'Read 1000 pages' in repr(goal)


class TestUserClubModel:
    def test_create_user_club(self, app):
        """Test creating a UserClub association"""
        with app.app_context():
            user = User(username='userclubuser', email='userclub@example.com')
            user.set_password('password')
            club = Club(club_name='Test Club', slug='test-club')
            db.session.add(user)
            db.session.add(club)
            db.session.commit()

            user_club = UserClub(user_id=user.user_id, club_id=club.club_id)
            db.session.add(user_club)
            db.session.commit()

            assert user_club.user_id == user.user_id
            assert user_club.club_id == club.club_id
            assert str(user_club).startswith('<UserClub user=')



class TestUserClubModel:
    def test_create_user_club(self, app):
        """Test creating a UserClub association (duplicate for coverage)"""
        with app.app_context():
            user = User(username='userclubuser2', email='userclub2@example.com')
            user.set_password('password')
            club = Club(club_name='Test Club 2', slug='test-club-2')
            db.session.add(user)
            db.session.add(club)
            db.session.commit()

            user_club = UserClub(user_id=user.user_id, club_id=club.club_id)
            db.session.add(user_club)
            db.session.commit()

            assert user_club.user_id == user.user_id
            assert user_club.club_id == club.club_id
            assert str(user_club).startswith('<UserClub user=')


class TestClubCommentModel:
    def test_create_club_comment(self, app):
        """Test creating a ClubComment instance"""
        with app.app_context():
            user = User(username='commentuser', email='commentuser@example.com')
            user.set_password('password')
            club = Club(club_name='Comment Club', slug='comment-club')
            db.session.add(user)
            db.session.add(club)
            db.session.commit()

            post = ClubPost(club_id=club.club_id, author_id=user.user_id, body='A club post')
            db.session.add(post)
            db.session.commit()

            comment = ClubComment(post_id=post.id, author_id=user.user_id, body='A comment')
            db.session.add(comment)
            db.session.commit()

            assert comment.id is not None
            assert comment.post_id == post.id
            assert comment.author_id == user.user_id
            assert comment.body == 'A comment'
            assert str(comment).startswith('<ClubComment')


class TestClubPostModel:
    def test_create_club_post(self, app):
        """Test creating a ClubPost instance"""
        with app.app_context():
            user = User(username='postuser', email='postuser@example.com')
            user.set_password('password')
            club = Club(club_name='Post Club', slug='post-club')
            db.session.add(user)
            db.session.add(club)
            db.session.commit()

            post = ClubPost(club_id=club.club_id, author_id=user.user_id, body='A club post body')
            db.session.add(post)
            db.session.commit()

            assert post.id is not None
            assert post.club_id == club.club_id
            assert post.author_id == user.user_id
            assert post.body == 'A club post body'
            assert str(post).startswith('<ClubPost')
