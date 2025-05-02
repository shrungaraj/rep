import unittest
from app import app, db
from models import User
from flask_login import current_user


class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())

    def test_register_page(self):
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'register', response.data.lower())

    def test_login_page(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())

    def test_user_registration(self):
        with app.app_context():
            response = self.app.post('/register', data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'password123',
                'confirm_password': 'password123'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'test@example.com')

    def test_user_login(self):
        with app.app_context():
            # Create a test user
            from werkzeug.security import generate_password_hash
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(user)
            db.session.commit()
            
            # Try to login
            response = self.app.post('/login', data={
                'username': 'testuser',
                'password': 'password123'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'dashboard', response.data.lower())


if __name__ == '__main__':
    unittest.main()