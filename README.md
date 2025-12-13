# 🎓 Sistema de Gestión de Talleres de Formación

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.0-000000?logo=flask)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple?logo=bootstrap)
![JWT](https://img.shields.io/badge/Auth-JWT-orange?logo=json-web-tokens)
![Status](https://img.shields.io/badge/Status-Prototipo_Funcional-success)

## 📋 Descripción

Aplicación web Full Stack diseñada para gestionar talleres de formación profesional.

El sistema cuenta con roles diferenciados:
1.  **Estudiantes (Público):** Pueden consultar la agenda y registrarse en talleres libremente.
2.  **Profesores (Privado):** Requieren **autenticación segura** para gestionar el ciclo de vida de los talleres (crear, editar, eliminar) a través de un panel de control protegido.

## 🚀 Características

### 🔹 Funcionalidades Web
* **Vista Pública:** Listado de talleres con detalles y registro rápido para estudiantes.
* **Autenticación:** Sistema de Login/Logout seguro utilizando **Cookies + JWT**.
* **Panel de Profesores:** Dashboard privado para la administración de talleres.
* **Interfaz:** Diseño moderno y responsivo con **Bootstrap 5** y estilos personalizados.

### 🔹 API RESTful & Seguridad
Backend robusto que protege las rutas sensibles:
* `GET /api/workshops`: Público.
* `POST /api/workshops`: **Protegido (Token Requerido)**.
* `DELETE /api/workshops/{id}`: **Protegido (Token Requerido)**.
* `POST /api/workshops/{id}/register`: Público (Inscripción de estudiantes).

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python, Flask, Flask-Bcrypt
* **Seguridad:** PyJWT (JSON Web Tokens)
* **Base de Datos:** SQLite (SQLAlchemy ORM)
* **Frontend:** HTML5, Jinja2, Bootstrap 5, CSS personalizado
* **Testing:** Pytest

## 📂 Estructura del Proyecto

```text
gestion_talleres/
├── static/                  # Archivos estáticos
│   ├── custom.css           # Estilos personalizados
│   └── background.jpg       # Imágenes del sitio
├── templates/
│   ├── base.html            # Layout principal (Navbar dinámico)
│   ├── index.html           # Vista Estudiantes
│   ├── login.html           # Vista de Acceso (Profesores)
│   └── admin.html           # Vista Panel de Gestión
├── app.py                   # Lógica de la aplicación y Seguridad
├── models.py                # Modelos (User, Workshop, Attendee)
├── test_app.py              # Pruebas Unitarias (con Auth)
├── requirements.txt         # Dependencias
└── README.md                # Documentación
````

## ⚙️ Instalación y Ejecución

Sigue estos pasos para levantar el proyecto en tu máquina local:

### 1\. Clonar el repositorio

```bash
git clone https://github.com/eixo4/proyecto-final/
cd gestion_talleres
```

### 2\. Configurar entorno virtual

```bash
# Linux / Mac
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3\. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4\. Ejecutar la aplicación

Al ejecutar la aplicación por primera vez, se creará automáticamente la base de datos y un **usuario profesor por defecto**.

```bash
python app.py
```

📍 **Acceder al sitio web:** Abre tu navegador en `http://127.0.0.1:5000`

### 🔑 Credenciales de Acceso (Profesor)

Para acceder al panel de administración, usa las siguientes credenciales generadas automáticamente:

  * **Usuario:** `admin`
  * **Contraseña:** `admin123`

## 🧪 Pruebas (Testing)

El proyecto incluye pruebas automatizadas que verifican tanto las rutas públicas como las protegidas (simulando tokens de autorización).

```bash
pytest
```

## 📖 Documentación de la API

| Método | Endpoint | Descripción | Seguridad | Body (JSON) |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/workshops` | Listar talleres | 🔓 Pública | N/A |
| `POST` | `/api/workshops/<id>/register` | Inscribir estudiante | 🔓 Pública | `{"student_name": "..."}` |
| `POST` | `/api/workshops` | Crear taller | 🔒 **Profesor** | `{"name": "...", ...}` |
| `PUT` | `/api/workshops/<id>` | Editar taller | 🔒 **Profesor** | `{"name": "...", ...}` |
| `DELETE` | `/api/workshops/<id>` | Eliminar taller | 🔒 **Profesor** | N/A |
