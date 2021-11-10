from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect,request
from flask_login import UserMixin, current_user, login_required, login_user, logout_user, LoginManager
from sqlalchemy.orm import query
from werkzeug.security import generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from forms import RegistrationForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

#Database class for the users
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    #image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    questions = db.relationship('Question', backref='author', lazy=True)

################# Hash the password, feature #########################
    # @property
    # def user_password(self):
    #     raise AttributeError('Cannot view unhashed password!')

    # @user_password.setter
    # def user_password(self, user_password):
    #     self.password = generate_password_hash(user_password)

#Database class for the questions
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    q_text = db.Column(db.Text)
    asked_by_id = db.Column(db.String, db.ForeignKey('user.username'))
    post_time = db.Column(db.DateTime)
    solved = db.Column(db.Boolean)
    answers = db.relationship('Answer', backref='question', lazy = True)

#Database class for the answers
class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    a_text = db.Column(db.Text)
    answered_by_id = db.Column(db.String, db.ForeignKey('user.username'))
    answer_to = db.Column(db.Integer, db.ForeignKey('question.id'))
    post_time = db.Column(db.DateTime)
    votes = db.Column(db.Integer)
    voted_best = db.Column(db.Boolean)

db.create_all()
db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    print(user_id)
    return User.query.get(int(user_id))

login_manager.login_view = "login"

#Home/default page route
@app.route("/home/")
@app.route("/")
def home():
    questions = Question.query.all()

    context = {
        'questions' : questions
    }
    return render_template('home.html', **context)

#about/contact us page route
@app.route("/about/")
def about():
    return render_template('about.html', title='About')

#Registration page route
@app.route("/register/", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit() and request.method =='POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user = User(username = username, email = email, password = password)
        if User.query.filter_by(email=email).first() !=None:
            flash(f'Already a user? Sign in now')
            return redirect(url_for('login'))
        else:
            db.session.add(user)
            db.session.commit()
            flash(f'Account created for {form.username.data}!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

#Login page route
@app.route("/login/", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit() and request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user or not (password==user.password):
            flash(u'Login Unsuccessful. Please check username and password', 'error')
            
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html', title='Login', form=form)

#user profile page
@app.route("/profile")
@login_required
def profile():
        return render_template("profile.html")

# Question Post page route
@app.route("/ask/", methods=['GET', 'POST'])
@login_required
def ask():
    if request.method == 'POST':
        question = request.form['question']

        question = Question(
            q_text = question, 
            asked_by_id =current_user.username,
            post_time = datetime.now(),
            solved = False
        )
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return render_template('ask.html')

#Question/Answer view page
@app.route("/question/<int:question_id>", methods=['GET', 'POST'])
def question(question_id):
        question = Question.query.get_or_404(question_id)
        question_id = question.id
        #If an answer is submitted
        if request.method == 'POST' and Answer.query.all()!= None:
            if request.form.get("answer"):
                answer = request.form['answer']
                answer = Answer(
                    a_text = answer, 
                    answered_by_id = current_user.username,
                    answer_to = question_id, 
                    post_time = datetime.now(), 
                    votes = 0, 
                    voted_best = False
                )
                db.session.add(answer)
                db.session.commit()

                return redirect(url_for('answer', question_id=question_id))
            #if the solved button is pressed    
            elif request.form.get("solved"):

#################################################
                ##Implement asker choosing for solution here?
#################################################

                return redirect(url_for('answer', question_id=question_id))
           #if the vote button is pressed
            elif request.form.get("vote"):

#################################################
                ##Implement voting on answer usefulness here
#################################################

                return redirect(url_for('answer', question_id=question_id))

        else:
            answers = Answer.query.filter_by(answer_to=question_id).all()
            context = {
            'question' : question,
            'answers' : answers
            }
        return render_template( 'question_view.html', **context)       

#reroute when there is a change to the question page to prevent new entries on refresh
@app.route("/question/<int:question_id>", methods=['GET', 'POST'])
def answer(question_id):
    question = Question.query.get_or_404(question_id)
    question_id = question.id
    answers = Answer.query.filter_by(answer_to=question_id).all()
    context = {
            'question' : question,
            'answers' : answers
    }
    return render_template('question_view.html', **context)

#Logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(debug=True)