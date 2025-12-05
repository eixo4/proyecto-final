from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Workshop(db.Model):
    """Modelo para almacenar los talleres."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.String(20), nullable=False)  # Guardamos como string YYYY-MM-DD por simplicidad
    time = db.Column(db.String(10), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))

    # Relación para ver quién se registró
    attendees = db.relationship('Attendee', backref='workshop', lazy=True, cascade="all, delete")

    def to_dict(self):
        """Helper para convertir el objeto a diccionario."""
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
    """Modelo para registrar estudiantes en talleres."""
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshop.id'), nullable=False)
