from flask import Flask, jsonify, request, render_template, redirect, url_for
from models import db, Workshop, Attendee

app = Flask(__name__)
# Configuración de base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///talleres.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

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


@app.route('/api/workshops', methods=['POST'])
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


@app.route('/api/workshops/<int:id>', methods=['PUT'])
def api_update_workshop(id):
    workshop = db.session.get(Workshop, id)
    if not workshop:
        return jsonify({"error": "Taller no encontrado"}), 404

    data = request.json
    workshop.name = data.get('name', workshop.name)
    workshop.description = data.get('description', workshop.description)
    workshop.date = data.get('date', workshop.date)
    # ... actualizar resto de campos si es necesario

    db.session.commit()
    return jsonify(workshop.to_dict()), 200


@app.route('/api/workshops/<int:id>', methods=['DELETE'])
def api_delete_workshop(id):
    workshop = db.session.get(Workshop, id)
    if not workshop:
        return jsonify({"error": "Taller no encontrado"}), 404

    db.session.delete(workshop)
    db.session.commit()
    return jsonify({"message": "Taller eliminado"}), 200


@app.route('/api/workshops/<int:id>/register', methods=['POST'])
def api_register_student(id):
    data = request.json
    student_name = data.get('student_name')

    workshop = db.session.get(Workshop, id)
    if not workshop:
        return jsonify({"error": "Taller no encontrado"}), 404

    new_attendee = Attendee(student_name=student_name, workshop_id=id)
    db.session.add(new_attendee)
    db.session.commit()

    return jsonify({"message": f"Estudiante {student_name} registrado exitosamente"}), 201

@app.route('/')
def view_students():
    """Vista principal para estudiantes: Ver y registrarse."""
    workshops = Workshop.query.all()
    return render_template('index.html', workshops=workshops)


@app.route('/admin')
def view_admin():
    """Panel de administración: Crear y borrar."""
    workshops = Workshop.query.all()
    return render_template('admin.html', workshops=workshops)


# Rutas auxiliares para que los formularios HTML funcionen sin usar AJAX complejo
@app.route('/admin/create', methods=['POST'])
def web_create_workshop():
    # Esta función recibe datos del formulario HTML, no JSON
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


@app.route('/admin/delete/<int:id>')
def web_delete_workshop(id):
    workshop = db.session.get(Workshop, id)
    if workshop:
        db.session.delete(workshop)
        db.session.commit()
    return redirect(url_for('view_admin'))

@app.route('/admin/edit/<int:id>', methods=['POST'])
def web_edit_workshop(id):
    workshop = db.session.get(Workshop, id)
    if not workshop:
        return redirect(url_for('view_admin'))

    workshop.name = request.form['name']
    workshop.description = request.form['description']
    workshop.date = request.form['date']
    workshop.time = request.form['time']
    workshop.location = request.form['location']
    workshop.category = request.form['category']

    db.session.commit()
    return redirect(url_for('view_admin'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
    app.run(debug=True, port=5000)
