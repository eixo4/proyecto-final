from flask_sqlalchemy import SQLAlchemy
# 3am idea: what if we just imported everything? nah jk

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Workshop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))

    # Usamos String para fecha/hora en lugar de objetos DateTime porque si
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(10), nullable=False)

    location = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))

    # cascade="all, delete" asegura que si borras un taller,
    # se borren automáticamente todos los asistentes registrados a él. Limpieza automática.
    attendees = db.relationship('Attendee', backref='workshop', lazy=True, cascade="all, delete")

    def to_dict(self):
        # changing this dict manually every time I add a field makes me want to cry
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "date": self.date,
            "time": self.time,
            "location": self.location,
            "category": self.category
        }


class Attendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshop.id'), nullable=False)