import os
import sqlite3
from contextlib import contextmanager

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:    
    pass

ESQUEMA = """
CREATE TABLE IF NOT EXISTS persona (
    rut       TEXT PRIMARY KEY,
    nombre    TEXT NOT NULL,
    direccion TEXT,
    telefono  TEXT,
    email     TEXT
);
CREATE TABLE IF NOT EXISTS departamento (
    id_departamento INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL UNIQUE,
    id_gerente      INTEGER REFERENCES empleado(id_empleado)
);
CREATE TABLE IF NOT EXISTS empleado (
    id_empleado     INTEGER PRIMARY KEY AUTOINCREMENT,
    rut             TEXT NOT NULL UNIQUE REFERENCES persona(rut),
    fecha_ingreso   TEXT NOT NULL,
    sueldo_base     REAL NOT NULL CHECK (sueldo_base > 0),
    id_departamento INTEGER REFERENCES departamento(id_departamento),
    activo          INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS proyecto (
    id_proyecto  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL,
    descripcion  TEXT,
    fecha_inicio TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS empleado_proyecto (
    id_empleado INTEGER NOT NULL REFERENCES empleado(id_empleado),
    id_proyecto INTEGER NOT NULL REFERENCES proyecto(id_proyecto),
    PRIMARY KEY (id_empleado, id_proyecto)
);
CREATE TABLE IF NOT EXISTS registro_tiempo (
    id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
    id_empleado INTEGER NOT NULL REFERENCES empleado(id_empleado),
    id_proyecto INTEGER NOT NULL REFERENCES proyecto(id_proyecto),
    fecha       TEXT NOT NULL,
    horas       REAL NOT NULL CHECK (horas > 0 AND horas <= 24),
    descripcion TEXT
);
"""


@contextmanager
def obtener_conexion():
    """Abre la conexión; confirma si todo salió bien, deshace si no."""
    conn = sqlite3.connect(os.getenv("DB_PATH", "ecotech.db"))
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def crear_esquema():
    with obtener_conexion() as conn:
        conn.executescript(ESQUEMA)


def probar_conexion():
    """Prueba de conexión del Paso 3 de la guía."""
    with obtener_conexion() as conn:
        return conn.execute("SELECT sqlite_version()").fetchone()[0]
