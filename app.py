from flask import Flask, render_template, url_for, request, redirect, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO


app = Flask(__name__)
app.secret_key = "your_secret_key"
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


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    st_id_card = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.id


@app.route('/')
@app.route('/index')
def index():
    articles = Article.query.all()
    return render_template("index.html", articles=articles)


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    error = None  # Инициализируем переменную, чтобы избежать ошибки при GET-запросах

    if request.method == "POST":
        user_name = request.form.get('user_name')
        st_id_card = request.form.get('st_id_card')
        password = request.form.get('password')

        # Проверка на уникальность номера
        existing_user = User.query.filter_by(st_id_card=st_id_card).first()
        if existing_user:
            error = "Этот номер уже используется. Пожалуйста, укажите другой."
        else:
            new_user = User(user_name=user_name, st_id_card=st_id_card, password=password)
            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Пользователь успешно зарегистрирован!', 'success')
                return redirect('/')  # Перенаправляем на главную страницу после успешной регистрации
            except Exception as e:
                error = f"Ошибка при регистрации: {str(e)}"

    # Если GET-запрос или ошибка, рендерим форму регистрации
    return render_template("signup.html", error=error)


def check_id():
    # Проверяем, что запрос содержит JSON-данные
    if not request.is_json:
        return {"error": "Invalid request format. Expected JSON."}, 400

    # Получаем поле st_id_card из JSON-данных
    st_id_card = request.json.get('st_id_card')
    if not st_id_card:
        return {"error": "Missing 'st_id_card' field in request."}, 400

    # Проверяем, существует ли запись с данным st_id_card
    exists = User.query.filter_by(st_id_card=st_id_card).first() is not None

    # Возвращаем результат проверки
    return {"exists": exists}, 200


@app.route('/login')
def login():
    return render_template("login.html")


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
            flash('Ваша анкета успешно добавлена!', 'success')
            return redirect('/')
        except:
            return "Ошибка при добавлении анкеты!"
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