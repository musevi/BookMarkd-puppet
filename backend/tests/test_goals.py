
import json
from models import BookGoal, PageGoal, HourGoal
from extensions import db

class TestGoalsAPI:
	def login(self, client):
		resp = client.post('/api/auth/login', json={
			'email': 'test@example.com',
			'password': 'password123'
		})
		return resp.get_json()['token']

	def test_create_goal_requires_auth(self, client):
		resp = client.post('/api/goals', json={
			'amount': 5, 'type': 'books read', 'duration': 'this year'
		})
		assert resp.status_code in (401, 422)

	def test_create_goal_success(self, client, sample_user):
		token = self.login(client)
		resp = client.post('/api/goals', json={
			'amount': 5, 'type': 'books read', 'duration': 'this year'
		}, headers={'Authorization': f'Bearer {token}'})
		assert resp.status_code == 201
		data = resp.get_json()
		assert data['goal']['type'] == 'books read'
		assert data['goal']['total'] == 5
		assert 'description' in data['goal']

	def test_create_goal_missing_fields(self, client, sample_user):
		token = self.login(client)
		resp = client.post('/api/goals', json={'type': 'books read', 'duration': 'this year'}, headers={'Authorization': f'Bearer {token}'})
		assert resp.status_code == 400
		data = resp.get_json()
		assert 'error' in data

	def test_get_goals(self, client, sample_user, app):
		token = self.login(client)
		# Add a goal for the user
		with app.app_context():
			goal = BookGoal(user_id=sample_user, num_books=3, description='Read 3 books this year')
			db.session.add(goal)
			db.session.commit()
		resp = client.get('/api/goals', headers={'Authorization': f'Bearer {token}'})
		assert resp.status_code == 200
		data = resp.get_json()
		assert 'goals' in data
		assert any(g['description'].startswith('Read 3 books') for g in data['goals'])

	def test_delete_goal(self, client, sample_user, app):
		token = self.login(client)
		# Add a goal for the user
		with app.app_context():
			goal = BookGoal(user_id=sample_user, num_books=2, description='Read 2 books this year')
			db.session.add(goal)
			db.session.commit()
			goal_id = goal.goal_id
		resp = client.delete(f'/api/goals/{goal_id}', headers={'Authorization': f'Bearer {token}'})
		assert resp.status_code == 200
		data = resp.get_json()
		assert data['deleted_goal']['id'] == goal_id

	def test_update_goal_progress(self, client, sample_user, app):
		token = self.login(client)
		# Add a goal for the user
		with app.app_context():
			goal = BookGoal(user_id=sample_user, num_books=4, description='Read 4 books this year')
			db.session.add(goal)
			db.session.commit()
			goal_id = goal.goal_id
		resp = client.put(f'/api/goals/{goal_id}', json={'progress': 2}, headers={'Authorization': f'Bearer {token}'})
		assert resp.status_code == 200
		data = resp.get_json()
		assert data['goal']['progress'] == 2
		assert data['goal']['id'] == goal_id
