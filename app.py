from flask import Flask, render_template, url_for, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studentyear.db'
db = SQLAlchemy(app)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    st_name = db.Column(db.Text, nullable=False)
    num_group = db.Column(db.Integer, nullable=False)
    faculty = db.Column(db.String(50), nullable=False)
    main_text = db.Column(db.Text, nullable=False)
    image = db.Column(db.LargeBinary)
    like = db.Column(db.Integer)

    def __repr__(self):
        return '<Article %r>' % self.id


# class User(db.Model):
#     user_name = db.Column(db.String(100), nullable=False)
#     st_id_card = db.Column(db.Integer, nullable=False)
#     password = db.Column(db.String(100), nullable=False)


@app.route('/')
@app.route('/index')
def index():
    articles = Article.query.all()
    return render_template("index.html", articles=articles)


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/signup')
def signup():
    return render_template("signup.html")


@app.route('/create-article', methods=['POST', 'GET'])
def create_article():
    if request.method == "POST":
        st_name = request.form['st_name']
        num_group = request.form['num_group']
        faculty = request.form['faculty']
        main_text = request.form['main_text']
        image = request.files['image']

        # Если изображение было загружено, преобразуем его в бинарные данные
        image_data = image.read() if image else None

        new_article = Article(st_name=st_name, num_group=num_group, faculty=faculty, main_text=main_text, image=image_data)

        try:
            db.session.add(new_article)
            db.session.commit()
            return redirect('/')
        except:
            return "Error"
    else:
         return render_template("create-article.html")


@app.route('/image/<int:article_id>')
def image(article_id):
    # Извлекаем изображение для статьи
    article = Article.query.get_or_404(article_id)
    if article.image:
        return send_file(BytesIO(article.image), mimetype='image/jpeg')
    return "No image", 404


if __name__ == "__main__":
    app.run(debug=True)