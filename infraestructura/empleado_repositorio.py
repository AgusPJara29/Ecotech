"""Repositorio de Empleado. Todas las consultas van parametrizadas (?)."""
from datetime import date

from dominio.empleado import Empleado
from infraestructura.conexion import obtener_conexion

COLUMNAS = """e.id_empleado, p.rut, p.nombre, e.fecha_ingreso, e.sueldo_base,
              p.direccion, p.telefono, p.email"""
DESDE = "FROM empleado e JOIN persona p ON p.rut = e.rut"


class EmpleadoRepositorio:

    @staticmethod
    def _fila_a_empleado(fila):
        empleado = Empleado(
            rut=fila[1], nombre=fila[2],
            fecha_ingreso=date.fromisoformat(fila[3]), sueldo_base=fila[4],
            direccion=fila[5] or "", telefono=fila[6] or "",
            email=fila[7] or "",
        )
        empleado.asignar_id(fila[0])
        return empleado

    def guardar(self, empleado):
        with obtener_conexion() as conn:
            conn.execute(
                "INSERT INTO persona (rut, nombre, direccion, telefono, email)"
                " VALUES (?, ?, ?, ?, ?)",
                (empleado.rut, empleado.nombre, empleado.direccion,
                 empleado.telefono, empleado.email),
            )
            cur = conn.execute(
                "INSERT INTO empleado (rut, fecha_ingreso, sueldo_base)"
                " VALUES (?, ?, ?)",
                (empleado.rut, empleado.fecha_ingreso.isoformat(),
                 empleado.sueldo_base),
            )
        empleado.asignar_id(cur.lastrowid)
        return empleado

    def obtener(self, rut):
        with obtener_conexion() as conn:
            fila = conn.execute(
                f"SELECT {COLUMNAS} {DESDE} WHERE e.rut = ? AND e.activo = 1",
                (rut,),
            ).fetchone()
        return self._fila_a_empleado(fila) if fila else None

    def listar(self, nombre_contiene=None):
        sql = f"SELECT {COLUMNAS} {DESDE} WHERE e.activo = 1"
        params = []
        if nombre_contiene:
            sql += " AND p.nombre LIKE ?"
            params.append(f"%{nombre_contiene}%")
        with obtener_conexion() as conn:
            filas = conn.execute(sql, params).fetchall()
        return [self._fila_a_empleado(f) for f in filas]

    def actualizar(self, empleado):
        with obtener_conexion() as conn:
            cur = conn.execute(
                "UPDATE empleado SET sueldo_base = ? "
                "WHERE rut = ? AND activo = 1",
                (empleado.sueldo_base, empleado.rut),
            )
            conn.execute(
                "UPDATE persona SET nombre = ?, direccion = ?, telefono = ?,"
                " email = ? WHERE rut = ?",
                (empleado.nombre, empleado.direccion, empleado.telefono,
                 empleado.email, empleado.rut),
            )
        return cur.rowcount

    def eliminar(self, rut):
        """Borrado lógico: el historial de horas se conserva."""
        with obtener_conexion() as conn:
            cur = conn.execute(
                "UPDATE empleado SET activo = 0 WHERE rut = ? AND activo = 1",
                (rut,),
            )
        return cur.rowcount > 0
