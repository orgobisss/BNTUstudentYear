from flask import Flask, render_template, url_for, request, redirect, send_file, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from io import BytesIO


app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studentyear.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    st_name = db.Column(db.Text, nullable=False)
    num_group = db.Column(db.Integer, nullable=False)
    faculty = db.Column(db.String(50), nullable=False)
    main_text = db.Column(db.Text, nullable=False)
    image = db.Column(db.LargeBinary)
    likes = db.Column(db.Integer, default=0)  # Количество лайков
    liked_by = db.relationship('Like', backref='article', lazy=True)  # Связь с лайками

    def __repr__(self):
        return '<Article %r>' % self.id


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)


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
    password_error = None

    if request.method == "POST":
        user_name = request.form.get('user_name')
        st_id_card = request.form.get('st_id_card')
        password = request.form.get('password')

        # Проверка на цифры
        if not st_id_card.isdigit():
            error = "Поле должно содержать только цифры."
        elif len(password) < 6:
            password_error = "Пароль должен содержать минимум 6 символов."
        else:
            # Проверка на уникальность номера
            existing_user = User.query.filter_by(st_id_card=st_id_card).first()
            if existing_user:
                error = "Этот номер уже используется. Пожалуйста, укажите другой."
            else:
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                new_user = User(user_name=user_name, st_id_card=st_id_card, password=hashed_password)
                try:
                    db.session.add(new_user)
                    db.session.commit()
                    flash('Пользователь успешно зарегистрирован!', 'success')
                    return redirect(url_for('login'))  # Перенаправляем на страницу авторизации после успешной регистрации
                except Exception as e:
                    error = f"Ошибка при регистрации: {str(e)}"

    # Если GET-запрос или ошибка, рендерим форму регистрации
    return render_template("signup.html", error=error, password_error=password_error)


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


@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None  # Инициализируем переменную, чтобы избежать ошибки при GET-запросах
    password_error = None

    if request.method == "POST":
        st_id_card = request.form.get('st_id_card')
        password = request.form.get('password')

        # Проверка на цифры
        if not st_id_card.isdigit():
            error = "Поле должно содержать только цифры."
        elif len(password) < 6:
            password_error = "Пароль должен содержать минимум 6 символов."
        else:
            # Проверяем, существует ли пользователь
            user = User.query.filter_by(st_id_card=st_id_card).first()
            if user and bcrypt.check_password_hash(user.password, password):  # Сравнение паролей
                session['user_id'] = user.id  # Сохраняем ID пользователя в сессии
                session['user_name'] = user.user_name  # Опционально сохраняем имя
                flash(f'Добро пожаловать, {user.user_name}!', 'success')
                return redirect('/')  # Перенаправляем на главную страницу
            else:
                error = "Неверный номер студенческого или пароль."

    # Если GET-запрос или ошибка, рендерим форму авторизации
    return render_template("login.html", error=error, password_error=password_error)


@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Удаляем пользователя из сессии
    session.pop('user_name', None)
    flash('Вы успешно вышли из аккаунта.', 'success')
    return redirect('/')


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Войдите в аккаунт, чтобы получить доступ.', 'danger')
        return redirect('/login')
    return render_template('profile.html', user_name=session['user_name'])


@app.route('/like/<int:article_id>', methods=['POST'])
def like_article(article_id):
    if 'user_id' not in session:
        return {"danger": False, "message": "Вы должны быть авторизованы для лайка."}, 403

    user_id = session['user_id']
    article = Article.query.get_or_404(article_id)

    # Проверяем, существует ли запись о лайке
    existing_like = Like.query.filter_by(user_id=user_id, article_id=article_id).first()

    if existing_like:
        # Убираем лайк
        db.session.delete(existing_like)
        article.likes -= 1
    else:
        # Если лайка нет, добавляем его
        new_like = Like(user_id=user_id, article_id=article_id)
        db.session.add(new_like)
        article.likes += 1

    db.session.commit()
    return {"success": True, "likes": article.likes}


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