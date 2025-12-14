# Code written by students fueled by 3 energy drinks and pure panic for trying to do all this 1 day before the due date
import os
import jwt
import datetime
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, redirect, url_for, make_response
from flask_bcrypt import Bcrypt
from models import db, Workshop, Attendee, User

load_dotenv()

app = Flask(__name__)

# SQLite es ligero y no requiere servidor externo, perfecto para este proyecto.
# En PROD, cambiaríamos esto a PostgreSQL. Pero no es PROD entonces lo mas simple mejor
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///talleres.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
if not app.config['SECRET_KEY']:
    # if this triggers, I'm quitting immediately lol
    raise ValueError("No SECRET_KEY set for Flask application")

db.init_app(app)
bcrypt = Bcrypt(app)

# Checking if we are live. If 'FLASK_ENV' is missing, we assume we are unsafe. YOLO.
IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production'

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Revisamos cookies Y headers.
        # Cookies = Para el navegador (seguro). Headers = Para Postman/API (flexible).
        if 'token' in request.cookies:
            token = request.cookies.get('token')
        elif 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Bearer <token>

        if not token:
            # No ticket? No ride. Get out.
            if 'text/html' in request.accept_mimetypes:
                return redirect(url_for('login_page'))
            return jsonify({'message': 'Token faltante'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db.session.get(User, data['user_id'])
            if not current_user or not current_user.is_admin:
                raise Exception("Acceso denegado")
        except:
            # Something smelled fishy with the token.
            if 'text/html' in request.accept_mimetypes:
                return redirect(url_for('login_page'))
            return jsonify({'message': 'Token inválido'}), 401

        return f(*args, **kwargs)

    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            # 2 hours expiration because security is my middle name (it's not)
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
            }, app.config['SECRET_KEY'], algorithm="HS256")

            resp = make_response(redirect(url_for('view_admin')))

            # httponly=True evita que JavaScript lea la cookie (anti-XSS).
            # samesite='Lax' protege contra CSRF. secure=True solo si hay HTTPS.
            resp.set_cookie(
                'token',
                token,
                httponly=True,
                secure=IS_PRODUCTION,
                samesite='Lax'
            )
            return resp

        return render_template('login.html', error="Credenciales inválidas")

    return render_template('login.html')


@app.route('/logout')
def logout():
    # deleting cookies like I delete my browsing history
    resp = make_response(redirect(url_for('view_students')))
    resp.set_cookie('token', '', expires=0, httponly=True, secure=IS_PRODUCTION, samesite='Lax')
    return resp

@app.route('/')
def view_students():
    workshops = Workshop.query.all()
    is_admin = False

    if 'token' in request.cookies:
        try:
            jwt.decode(request.cookies.get('token'), app.config['SECRET_KEY'], algorithms=["HS256"])
            is_admin = True
        except:
            pass  # token was fake or expired, whatever dude

    return render_template('index.html', workshops=workshops, is_admin=is_admin)

@app.route('/api/workshops', methods=['GET'])
def api_get_workshops():
    workshops = Workshop.query.all()
    return jsonify([w.to_dict() for w in workshops]), 200


@app.route('/api/workshops/<int:id>', methods=['GET'])
def api_get_workshop_detail(id):
    workshop = db.session.get(Workshop, id)
    if not workshop:
        return jsonify({"error": "Taller no encontrado"}), 404
    return jsonify(workshop.to_dict()), 200


@app.route('/api/workshops/<int:id>/register', methods=['POST'])
def api_register_student(id):
    # Please don't SQL inject me
    data = request.json
    student_name = data.get('student_name')

    if not student_name:
        return jsonify({"error": "Nombre requerido"}), 400

    workshop = db.session.get(Workshop, id)
    if not workshop:
        return jsonify({"error": "Taller no encontrado"}), 404

    new_attendee = Attendee(student_name=student_name, workshop_id=id)
    db.session.add(new_attendee)
    db.session.commit()

    return jsonify({"message": f"Estudiante {student_name} registrado"}), 201

@app.route('/admin')
@admin_required
def view_admin():
    workshops = Workshop.query.all()
    return render_template('admin.html', workshops=workshops, is_admin=True)


@app.route('/admin/create', methods=['POST'])
@admin_required
def web_create_workshop():
    # Usamos request.form porque viene de un formulario HTML normal, no JSON.
    new_workshop = Workshop(
        name=request.form['name'],
        description=request.form['description'],
        date=request.form['date'],
        time=request.form['time'],
        location=request.form['location'],
        category=request.form['category']
    )
    db.session.add(new_workshop)
    db.session.commit()
    return redirect(url_for('view_admin'))


@app.route('/admin/edit/<int:id>', methods=['POST'])
@admin_required
def web_edit_workshop(id):
    workshop = db.session.get(Workshop, id)
    if workshop:
        # Manually mapping fields like a caveman. Automappers are for the weak.
        workshop.name = request.form['name']
        workshop.description = request.form['description']
        workshop.date = request.form['date']
        workshop.time = request.form['time']
        workshop.location = request.form['location']
        workshop.category = request.form['category']
        db.session.commit()
    return redirect(url_for('view_admin'))


@app.route('/admin/delete/<int:id>')
@admin_required
def web_delete_workshop(id):
    workshop = db.session.get(Workshop, id)
    if workshop:
        db.session.delete(workshop)
        db.session.commit()  # // Begone thot
    return redirect(url_for('view_admin'))

@app.before_request
def create_initial_admin():
    # Esto corre antes de cada petición. Si no existe un admin, lo crea.
    # Usamos credenciales del sistema (ENV) para no dejar contraseñas hardcodeadas en el código.
    admin_user = os.getenv('ADMIN_USER', 'admin')
    admin_pass = os.getenv('ADMIN_PASS', 'admin123')

    # Checking DB every request is inefficient, but I am too tired to fix it
    if not User.query.first():
        hashed_pw = bcrypt.generate_password_hash(admin_pass).decode('utf-8')
        admin = User(username=admin_user, password=hashed_pw, is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print(f">>> Usuario Admin creado: {admin_user} (God mode enabled)")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    # Do not run debug=True in production unless you like getting hacked ;) (ThankS SNYK)
    app.run(debug=debug_mode, port=5000)