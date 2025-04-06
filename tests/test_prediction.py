import pytest
import pandas as pd
from app import app, db, Data, model

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()

        # Create a test project for prediction
        test_project = Data(name='Test Project', email='test@example.com', phone='123456789')
        db.session.add(test_project)
        db.session.commit()

        yield app.test_client()

        db.session.remove()
        db.drop_all()

def test_prediction(client):
    # Get the test project ID
    project = Data.query.filter_by(name='Test Project').first()

    # Post valid prediction form data
    response = client.post(f'/predict/{project.id}', data=dict(beds=3, baths=2, garage=1, sqft=1500, stories=1))
    assert response.status_code == 302  # Should redirect to result page

    # Follow the redirect to the result page
    follow_up = client.get('/result', query_string=dict(price=300000, id=project.id))
    assert b'300000' in follow_up.data  # Check if the predicted price is displayed
