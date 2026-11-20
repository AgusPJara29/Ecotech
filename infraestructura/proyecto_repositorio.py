"""Repositorio de Proyecto. Consultas parametrizadas."""
import sqlite3
from datetime import date

from dominio.proyecto import Proyecto
from infraestructura.conexion import obtener_conexion

COLUMNAS = "id_proyecto, nombre, descripcion, fecha_inicio"


class ProyectoRepositorio:

    @staticmethod
    def _fila_a_proyecto(fila):
        proyecto = Proyecto(
            nombre=fila[1], descripcion=fila[2],
            fecha_inicio=date.fromisoformat(fila[3]),
        )
        proyecto.asignar_id(fila[0])
        return proyecto

    def guardar(self, proyecto):
        with obtener_conexion() as conn:
            cur = conn.execute(
                "INSERT INTO proyecto (nombre, descripcion, fecha_inicio)"
                " VALUES (?, ?, ?)",
                (proyecto.nombre, proyecto.descripcion,
                 proyecto.fecha_inicio.isoformat()),
            )
        proyecto.asignar_id(cur.lastrowid)
        return proyecto

    def obtener(self, id_proyecto):
        with obtener_conexion() as conn:
            fila = conn.execute(
                f"SELECT {COLUMNAS} FROM proyecto WHERE id_proyecto = ?",
                (id_proyecto,),
            ).fetchone()
        return self._fila_a_proyecto(fila) if fila else None

    def listar(self, nombre_contiene=None):
        sql = f"SELECT {COLUMNAS} FROM proyecto"
        params = []
        if nombre_contiene:
            sql += " WHERE nombre LIKE ?"
            params.append(f"%{nombre_contiene}%")
        with obtener_conexion() as conn:
            filas = conn.execute(sql, params).fetchall()
        return [self._fila_a_proyecto(f) for f in filas]

    def actualizar(self, proyecto):
        with obtener_conexion() as conn:
            cur = conn.execute(
                "UPDATE proyecto SET nombre = ?, descripcion = ? "
                "WHERE id_proyecto = ?",
                (proyecto.nombre, proyecto.descripcion, proyecto.id_proyecto),
            )
        return cur.rowcount

    def eliminar(self, id_proyecto):
        """Se impide borrar si tiene registros de tiempo (FK)."""
        try:
            with obtener_conexion() as conn:
                cur = conn.execute(
                    "DELETE FROM proyecto WHERE id_proyecto = ?",
                    (id_proyecto,),
                )
            return cur.rowcount > 0
        except sqlite3.IntegrityError:
            return False
