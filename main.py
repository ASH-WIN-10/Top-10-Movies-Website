from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class RateMovieForm(FlaskForm):
    id = HiddenField(label='')
    rating = FloatField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")

class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'any_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)

app.app_context().push()

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    year = db.Column(db.Integer)
    description = db.Column(db.String(500))
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(250))
    img_url = db.Column(db.String(100))

db.create_all()


def search_movie(movie_title):
    url = f"https://api.themoviedb.org/3/search/movie?query={movie_title}&include_adult=true&language=en-US&page=1"
    headers = {
        "accept": "application/json",
        "Authorization": os.environ.get("API_KEY" ,"Your API key from themoviedb.org")
    }
    print(headers)
    response = requests.get(url, headers=headers)
    movies = response.json()
    return movies

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
    headers = {
        "accept": "application/json",
        "Authorization": os.environ.get("API_KEY" ,"Your API key from themoviedb.org")
    }
    response = requests.get(url, headers=headers)
    details = response.json()
    return details


@app.route("/", methods=['GET', 'POST'])
def home():
    all_movies = db.session.query(Movie).order_by(Movie.rating).all()

    i = 0
    for movie in all_movies:
        movie.ranking = len(all_movies) - i
        i += 1
    db.session.commit()

    return render_template("index.html", all_movies=all_movies)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        movie_id = request.form['id']
        movie_to_update = db.session.query(Movie).get(movie_id)
        movie_to_update.rating = request.form['rating']
        movie_to_update.review = request.form['review']
        db.session.commit()
        return redirect(url_for('home'))
    form = RateMovieForm()
    movie_id = request.args.get('movie_id')
    movie_to_update = db.session.query(Movie).get(movie_id)
    return render_template('edit.html', form=form, movie=movie_to_update)


@app.route('/delete')
def delete():
    movie_id = request.args.get('movie_id')
    movie = db.session.query(Movie).get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddMovieForm()
    if request.method == 'POST':
        movie_title = request.form.get('title')
        movies = search_movie(movie_title)
        return render_template('select.html', movies=movies)
    
    if request.args.get('movie_id'):
        movie_id = request.args.get('movie_id')
        details = get_movie_details(movie_id)

        new_movie = Movie(
            title=details['title'],
            year=details['release_date'][:4],
            description=details['overview'],
            img_url=f"https://image.tmdb.org/t/p/w500/{details['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()

        id = new_movie.id

        return redirect(url_for('edit', movie_id=id))

    return render_template('add.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
