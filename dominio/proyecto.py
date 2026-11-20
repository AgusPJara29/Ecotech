"""Proyecto: dueño de sus RegistroTiempo (composición)."""
from dominio.registro_tiempo import RegistroTiempo


class Proyecto:
    def __init__(self, nombre, descripcion, fecha_inicio):
        self.__id_proyecto = None
        self.nombre = nombre
        self.descripcion = descripcion
        self.__fecha_inicio = fecha_inicio
        self.__empleados = []
        self.__registros = []

    @property
    def id_proyecto(self):
        return self.__id_proyecto

    def asignar_id(self, valor):
        if self.__id_proyecto is not None:
            raise ValueError("El ID ya fue asignado")
        self.__id_proyecto = valor

    @property
    def fecha_inicio(self):
        return self.__fecha_inicio

    @property
    def empleados(self):
        return tuple(self.__empleados)    # copia: no se modifica desde fuera

    @property
    def registros(self):
        return tuple(self.__registros)

    # --- acciones ---
    def agregar_empleado(self, empleado):
        if empleado not in self.__empleados:
            self.__empleados.append(empleado)

    def quitar_empleado(self, empleado):
        if empleado in self.__empleados:
            self.__empleados.remove(empleado)

    def registrar_horas(self, empleado, fecha, horas, descripcion):
        """Crea el RegistroTiempo: solo si el empleado está asignado."""
        if empleado not in self.__empleados:
            return False
        self.__registros.append(
            RegistroTiempo(empleado, self, fecha, horas, descripcion))
        return True

    # --- consultas ---
    def obtener_horas_totales(self):
        return sum(r.horas_trabajadas for r in self.__registros)

    def __str__(self):
        return f"{self.nombre} (id={self.__id_proyecto})"
