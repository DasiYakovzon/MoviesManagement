from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf.file import FileField
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/movie'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    admin = db.Column(db.Boolean, default=True, nullable=False)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poster = db.Column(db.String(200), nullable=False, default='default.jpg')
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    classification = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(200), nullable=False)
    season = db.Column(db.String(200), nullable=False)
    reviews = db.relationship('Review', backref='movie', lazy=True)

    # Add foreign key constraint to reviews relationship
    # Specify the column name as 'movie_id' since it refers to the 'id' column in the Movie model
    reviews = db.relationship('Review', backref='movie', lazy=True, foreign_keys='Review.movie_id')


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)


class AddMovieForm(FlaskForm):
    poster = FileField('Movie Poster', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    classification = StringField('Classification', validators=[DataRequired()])
    season = StringField('Season', validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


with app.app_context():
    db.create_all()


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User(username=username, password=password, admin=True)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        if user.admin:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('show_all_movies'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            if user.admin:
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('show_all_movies'))
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/admin')
@login_required
def admin():
    if not current_user.admin:
        return redirect(url_for('home'))
    form = AddMovieForm()
    movies = Movie.query.all()
    return render_template('add_movie.html', form=form, movies=movies)

@app.route('/admin/add_movie', methods=['GET', 'POST'])
@login_required
def add_movie():
    if not current_user.admin:
        return redirect(url_for('home'))
    form = AddMovieForm()
    if form.validate_on_submit():
        poster = form.poster.data
        title = form.title.data
        description = form.description.data
        classification = form.classification.data
        season = form.season.data
        color = form.color.data

        # Save the file to a secure location
        poster_filename = secure_filename(poster.filename)
        poster_path = os.path.join(app.config['UPLOAD_FOLDER'], poster_filename)
        poster_path = poster_path.replace('\\', '/')
        poster.save(poster_path)

        # Create the movie object with the relative file path
        movie = Movie(
            poster='movie/' + poster_filename,
            title=title,
            description=description,
            classification=classification,
            season=season,
            color=color
        )
        db.session.add(movie)
        db.session.commit()
        return redirect(url_for('show_movies'))
    return render_template('add_movie.html', form=form)


@app.route('/user')
@login_required
def show_all_movies():
    return redirect(url_for('show_movies'))


@app.route('/movies')
@login_required
def show_movies():
    movies = Movie.query.all()
    return render_template('all_movies.html', movies=movies)

@app.route('/movie/<int:movie_id>')
@login_required
def show_movie(movie_id):
    # Retrieve the movie details using the movie_id
    movie = Movie.query.get_or_404(movie_id)
    return render_template('movie.html', movie=movie)

if __name__ == '__main__':
    app.run(debug=True)
