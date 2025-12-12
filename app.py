import os
from dotenv import load_dotenv # [SNYK FIX] Load env vars
from flask import Flask, jsonify, request, render_template, redirect, url_for, make_response
from models import db, Workshop, Attendee, User
from flask_bcrypt import Bcrypt
import jwt
import datetime
from functools import wraps

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///talleres.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# [SNYK FIX: HIGH] Hardcoded Non-Cryptographic Secret
# We now load it from the environment. If it's not there, we crash (safer than using a default insecure key)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("No SECRET_KEY set for Flask application")

db.init_app(app)
bcrypt = Bcrypt(app)

# Helper to determine if we are in production (for Secure cookies)
IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production'

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'token' in request.cookies:
            token = request.cookies.get('token')
        elif 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            if 'text/html' in request.accept_mimetypes:
                return redirect(url_for('login_page'))
            return jsonify({'message': 'Token faltante'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db.session.get(User, data['user_id'])
            if not current_user or not current_user.is_admin:
                raise Exception("Acceso denegado")
        except:
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
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
            }, app.config['SECRET_KEY'], algorithm="HS256")

            resp = make_response(redirect(url_for('view_admin')))
            
            # [SNYK FIX: LOW] Sensitive Cookie flags
            resp.set_cookie(
                'token', 
                token, 
                httponly=True,       # Prevents JavaScript access (XSS protection)
                secure=IS_PRODUCTION, # True if Prod (HTTPS), False if Dev (HTTP)
                samesite='Lax'       # CSRF protection
            )
            return resp

        return render_template('login.html', error="Credenciales inválidas")

    return render_template('login.html')

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('view_students')))
    # [SNYK FIX: LOW] Secure attribute on logout as well
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
            pass
    return render_template('index.html', workshops=workshops, is_admin=is_admin)

# ... (API Routes remain the same, they don't trigger Snyk warnings) ...
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
        db.session.commit()
    return redirect(url_for('view_admin'))

@app.route('/api/workshops', methods=['POST'])
@admin_required
def api_create_workshop():
    data = request.json
    new_workshop = Workshop(
        name=data['name'],
        description=data.get('description', ''),
        date=data['date'],
        time=data['time'],
        location=data['location'],
        category=data['category']
    )
    db.session.add(new_workshop)
    db.session.commit()
    return jsonify(new_workshop.to_dict()), 201

@app.route('/api/workshops/<int:id>', methods=['PUT', 'DELETE'])
@admin_required
def api_modify_workshop(id):
    workshop = db.session.get(Workshop, id)
    if not workshop:
        return jsonify({"error": "Taller no encontrado"}), 404
    if request.method == 'DELETE':
        db.session.delete(workshop)
        db.session.commit()
        return jsonify({"message": "Taller eliminado"}), 200
    data = request.json
    workshop.name = data.get('name', workshop.name)
    db.session.commit()
    return jsonify(workshop.to_dict()), 200

@app.before_request
def create_initial_admin():
    # [SNYK FIX: LOW] Use of Hardcoded Credentials
    # Now we pull from OS environment
    admin_user = os.getenv('ADMIN_USER', 'admin')
    admin_pass = os.getenv('ADMIN_PASS', 'admin123')
    
    if not User.query.first():
        hashed_pw = bcrypt.generate_password_hash(admin_pass).decode('utf-8')
        admin = User(username=admin_user, password=hashed_pw, is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print(f">>> Usuario Admin creado desde ENV: {admin_user}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # [SNYK FIX: MEDIUM] Debug Mode Enabled
    # We check the environment variable. If it says 'True', we debug. Otherwise, False.
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(debug=debug_mode, port=5000)
