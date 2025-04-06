from flask import Flask, render_template, request, url_for, redirect, flash 
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

import pandas as pd
import pickle

app = Flask(__name__)
app.secret_key = "Secret Key"

#SQLAlchemy - connecting to database from workbench
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:P347word%40%24%23@localhost/real_estate' # encoded password - as some characters interferes with @localhost
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)                        

login_manager = LoginManager()              
login_manager.init_app(app)                 
login_manager.login_view = "login"    #updated 9/9/2024 from Login -> login (for testing error)      

# @login_manager.user_loader                  
# def load_user(user_id):                     
#     return User.query.get(int(user_id))     

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # -  #updated 9/9/2024

class User(db.Model, UserMixin):                                                           
    id = db.Column(db.Integer, primary_key=True) # Changed from ID to id                   
    username = db.Column(db.String(20), nullable=False, unique=True)                       
    password = db.Column(db.String(80), nullable=False)

class RegisterForm(FlaskForm):                                                             
    username = StringField(validators=[InputRequired(), Length(                            
        min=4, max=20)], render_kw={"placeholder": "Username"})                            
    password = PasswordField(validators=[InputRequired(), Length(                          
        min=4, max=20)], render_kw={"placeholder": "Password"})                             
    submit = SubmitField("Register")                                                       

    def validate_username(self, username):                                                 
        existing_user_username = User.query.filter_by(                                     
            username=username.data).first()                                                
        if existing_user_username:                                                         
            raise ValidationError(                                                         
                "The username already exists. Please choose a different one.")             
        
class LoginForm(FlaskForm):                                                                
    username = StringField(validators=[InputRequired(), Length(                            
        min=4, max=20)], render_kw={"placeholder": "Username"})                            
    password = PasswordField(validators=[InputRequired(), Length(                          
        min=4, max=20)], render_kw={"placeholder": "Password"})                            
    submit = SubmitField("Login")


#crud table
class Data(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(100))

    def __init__(self, name, email, phone):
        self.name = name
        self.email = email
        self.phone = phone


# Load the model from the pickle file
with open('models/RandomForest.pkl', 'rb') as file: # 9/11/2024 - added lr pkl to model folder
    model = pickle.load(file)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'] )                                 
def login():                                                                    
    form = LoginForm()                                                          

    if form.validate_on_submit():                                               
        user = User.query.filter_by(username=form.username.data).first()        
        if user:                                                                  
            if bcrypt.check_password_hash(user.password, form.password.data):   
                login_user(user)                                                
                return redirect(url_for('crud'))                                

    return render_template('login.html', form=form)                             


@app.route('/crud')
@login_required
def crud():
    all_data = Data.query.all()
    return render_template("crud.html", projects=all_data)


@app.route('/logout', methods=['GET', 'POST'])                                  
@login_required
def logout():
    logout_user()
    return redirect(url_for('index')) #logout button routes to home page


@app.route('/register', methods=['GET', 'POST'])                                
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


# Add new project  - insert post data from html form into database
@app.route('/insert', methods=['POST'])
def insert():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        my_data = Data(name, email, phone)
        db.session.add(my_data)
        db.session.commit()

        flash("project inserted successfully")
        return redirect(url_for('crud'))


#Edit row - Update database from form input
@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        # my_data = Data.query.get(request.form.get('id'))
        my_data = db.session.get(Data, request.form.get('id')) # - updated 9/9/2024

        my_data.name = request.form['name']
        my_data.email = request.form['email']
        my_data.phone = request.form['phone']

        db.session.commit()
        flash("project updated successfully")
        return redirect(url_for('crud'))


#Delete row - 
@app.route('/delete/<id>/', methods=['GET', 'POST'])
def delete(id):
    # my_data = Data.query.get(id)
    my_data = db.session.get(Data, id) #updated - 9/9/2024
    db.session.delete(my_data)
    db.session.commit()
    flash("project deleted successfully")
    return redirect(url_for('crud'))



@app.route('/predict/<id>', methods=['GET', 'POST'])
def predict(id):
    # project = Data.query.get(id) 
    project = db.session.get(Data, id) #- updated 9/9/2024 -  Replaced the legacy .get() method with session.get().


    if request.method == 'POST':
        # Retrieve form data
        beds = int(request.form.get('beds'))
        baths = int(request.form.get('baths'))
        garage = int(request.form.get('garage'))
        sqft = int(request.form.get('sqft'))
        stories = int(request.form.get('stories'))

        # Prepare the feature DataFrame for prediction
        features = pd.DataFrame([[beds, baths, garage, sqft, stories]],
                                columns=['beds', 'baths', 'garage', 'sqft', 'stories'])

        # Predict the house price using the loaded model
        predicted_price = model.predict(features)[0]

        # Clipping the predicted price to a minimum value
        predicted_price = max(predicted_price, 207835.7886)

        # Redirect to a new page to display the result
        return redirect(url_for('result', price=predicted_price, id=id))

    # Render the prediction form template (GET request)
    return render_template('predict.html', project=project)



@app.route('/result')
def result():
    price = request.args.get('price')
    project_id = request.args.get('id')
    # project = Data.query.get(project_id)
    project = db.session.get(Data, project_id) #- - updated 9/9/2024
    return render_template('result.html', price=price, project=project)




# Application entry point:
if __name__ == "__main__":
    app.run(debug=True)



