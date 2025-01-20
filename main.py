from flask import Flask, render_template, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
import requests
from werkzeug.utils import redirect
from wtforms import StringField, SubmitField
from flask_ckeditor import CKEditor, CKEditorField
from wtforms.validators import DataRequired
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
ckeditor = CKEditor(app)
Bootstrap5(app)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Create db table

class Books(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()

# Create book form
class AddForm(FlaskForm):
    isbn = StringField(label="Insert Book's ISBN Code", validators=[DataRequired()])
    body = CKEditorField("Book Description", validators=[DataRequired()])
    rating = StringField("Book Rating", validators=[DataRequired()])
    submit = SubmitField(label="Submit")

class EditForm(FlaskForm):
    body = CKEditorField("Book Description", validators=[DataRequired()])
    rating = StringField("Book Rating", validators=[DataRequired()])
    submit = SubmitField(label="Submit")

@app.route('/')
def home():
    result = db.session.execute(db.select(Books))
    books = result.scalars().all()
    return render_template('index.html', all_books=books)

@app.route('/add', methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        isbn = form.isbn.data
        response = requests.get(f"https://openlibrary.org/isbn/{isbn}.json")
        data = response.json()
        year = data["publish_date"]
        title = data["title"]
        isbn_13 = data["isbn_13"][0]

        author = data["authors"]
        author_key = author[0]
        author_id = author_key["key"].split('/')[-1]
        author_response = requests.get(f"https://openlibrary.org/authors/{author_id}.json").json()
        author_name = author_response["name"]

        new_book = Books(
            title=title,
            year=year,
            author=author_name,
            description=form.body.data,
            rating=form.rating.data,
            img_url=f"https://covers.openlibrary.org/b/isbn/{isbn_13}-M.jpg"
        )
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template('add.html', form=form)

@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditForm()
    book_id = request.args.get('id')
    book = db.get_or_404(Books, book_id)
    if form.validate_on_submit():
        book.description = form.body.data
        book.rating = form.rating.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, book=book)

@app.route("/delete")
def delete():
    book_id = request.args.get("id")
    book = db.get_or_404(Books, book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True)