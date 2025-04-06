import pytest
from app import app, db, bcrypt, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database for tests

    with app.app_context():
        db.create_all()

        # Create a test user
        hashed_password = bcrypt.generate_password_hash('testpassword').decode('utf-8')
        test_user = User(username='testuser', password=hashed_password)
        db.session.add(test_user)
        db.session.commit()

        yield app.test_client()

        db.session.remove()
        db.drop_all()


def test_password_hashing():
    password = 'testpassword'
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    assert bcrypt.check_password_hash(hashed_password, password)

def test_login_valid_credentials(client):
    response = client.post('/login', data=dict(username='testuser', password='testpassword'))
    assert response.status_code == 302  # Redirection after successful login
    assert response.headers['Location'] == '/crud'

def test_login_invalid_credentials(client):
    response = client.post('/login', data=dict(username='wronguser', password='wrongpassword'))
    assert b'Invalid credentials' not in response.data
    assert response.status_code == 200  # No redirection, should stay on login page

def test_logout(client):
    client.post('/login', data=dict(username='testuser', password='testpassword'))
    response = client.get('/logout')
    assert response.status_code == 302  # Should redirect to index after logout
