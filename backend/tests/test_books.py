
import json
from models import Book, UserBook
from extensions import db

class TestBooksAPI:
	def login(self, client):
		resp = client.post('/api/auth/login', json={
			'email': 'test@example.com',
			'password': 'password123'
		})
		return resp.get_json()['token']

	def test_create_book_requires_auth(self, client):
		resp = client.post('/api/books', json={
			'title': 'Book1', 'author': 'Author1', 'total_pages': 100
		})
		assert resp.status_code in (401, 422)

	def test_create_book_success(self, client, sample_user, app):
		token = self.login(client)
		resp = client.post('/api/books', json={
			'title': 'Book1', 'author': 'Author1', 'total_pages': 100
		}, headers={'Authorization': f'Bearer {token}'})
		assert resp.status_code == 201
		data = resp.get_json()
		assert data['title'] == 'Book1'
		assert data['author'] == 'Author1'
		assert data['status'] == 'wishlist'
		assert data['total_pages'] == 100

	def test_create_book_missing_fields(self, client, sample_user):
		token = self.login(client)
		resp = client.post('/api/books', json={
			'author': 'Author1', 'total_pages': 100
		}, headers={'Authorization': f'Bearer {token}'})
		assert resp.status_code == 400
		data = resp.get_json()
		assert 'error' in data

	def test_get_books(self, client, sample_user, app):
		token = self.login(client)
		# Add a book for the user
		with app.app_context():
			book = Book(title='Book2', author='Author2', page_count=150)
			db.session.add(book)
			db.session.commit()
			user_book = UserBook(user_id=sample_user, book_id=book.book_id, page_progress=0)
			db.session.add(user_book)
			db.session.commit()
		resp = client.get('/api/books', headers={'Authorization': f'Bearer {token}'})
		assert resp.status_code == 200
		data = resp.get_json()
		assert isinstance(data, list)
		assert any(b['title'] == 'Book2' for b in data)

	def test_delete_book(self, client, sample_user, app):
		token = self.login(client)
		# Add a book for the user
		with app.app_context():
			book = Book(title='Book3', author='Author3', page_count=120)
			db.session.add(book)
			db.session.commit()
			user_book = UserBook(user_id=sample_user, book_id=book.book_id, page_progress=0)
			db.session.add(user_book)
			db.session.commit()
			book_id = book.book_id
		resp = client.delete(f'/api/books/{book_id}', headers={'Authorization': f'Bearer {token}'})
		assert resp.status_code == 200
		data = resp.get_json()
		assert 'message' in data

	def test_update_book_progress(self, client, sample_user, app):
		token = self.login(client)
		# Add a book for the user
		with app.app_context():
			book = Book(title='Book4', author='Author4', page_count=200)
			db.session.add(book)
			db.session.commit()
			user_book = UserBook(user_id=sample_user, book_id=book.book_id, page_progress=0)
			db.session.add(user_book)
			db.session.commit()
			book_id = book.book_id
		resp = client.put(f'/api/books/{book_id}/progress', json={'page_progress': 50}, headers={'Authorization': f'Bearer {token}'})
		assert resp.status_code == 200
		data = resp.get_json()
		assert data['page_progress'] == 50
		assert data['status'] == 'reading'

	def test_update_book_rating(self, client, sample_user, app):
		token = self.login(client)
		# Add a book for the user and mark as read
		with app.app_context():
			book = Book(title='Book5', author='Author5', page_count=100)
			db.session.add(book)
			db.session.commit()
			user_book = UserBook(user_id=sample_user, book_id=book.book_id, page_progress=100)
			db.session.add(user_book)
			db.session.commit()
			book_id = book.book_id
		resp = client.put(f'/api/books/{book_id}/rating', json={'rating': 4.5}, headers={'Authorization': f'Bearer {token}'})
		assert resp.status_code == 200
		data = resp.get_json()
		assert data['rating'] == 4.5
		assert data['status'] == 'read'

	def test_recommendations_requires_auth(self, client):
		resp = client.post('/api/recommendations', json={})
		assert resp.status_code in (401, 422)

	def test_recommendations_missing_fields(self, client, sample_user):
		token = self.login(client)
		resp = client.post('/api/recommendations', json={'genre': 'fiction'}, headers={'Authorization': f'Bearer {token}'})
		assert resp.status_code == 400
		data = resp.get_json()
		assert 'error' in data
