import pytest
from app import app, db, Data

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()

        # Create a test project for CRUD operations
        test_project = Data(name='Test Project', email='test@example.com', phone='123456789')
        db.session.add(test_project)
        db.session.commit()

        yield app.test_client()

        db.session.remove()
        db.drop_all()


def test_insert_project(client):
    response = client.post('/insert', data=dict(name='Test Project', email='test@example.com', phone='123456789'))
    assert response.status_code == 302  # Redirect after successful insertion

    # Check that the new project exists in the database
    project = Data.query.filter_by(name='Test Project').first()
    assert project is not None
    assert project.email == 'test@example.com'
    assert project.phone == '123456789'

def test_update_project(client):
    # Insert data first
    client.post('/insert', data=dict(name='Test Project', email='test@example.com', phone='123456789'))
    project = Data.query.filter_by(name='Test Project').first()

    # Update the project
    response = client.post('/update', data=dict(id=project.id, name='Updated Project', email='updated@example.com', phone='987654321'))
    assert response.status_code == 302  # Redirect after successful update

    # Check that the project was updated
    updated_project = Data.query.get(project.id)
    assert updated_project.name == 'Updated Project'
    assert updated_project.email == 'updated@example.com'
    assert updated_project.phone == '987654321'

def test_delete_project(client):
    # Insert data first
    client.post('/insert', data=dict(name='Test Project', email='test@example.com', phone='123456789'))
    project = Data.query.filter_by(name='Test Project').first()

    # Delete the project
    response = client.post(f'/delete/{project.id}/')
    assert response.status_code == 302  # Redirect after successful deletion

    # Check that the project is deleted
    deleted_project = Data.query.get(project.id)
    assert deleted_project is None
