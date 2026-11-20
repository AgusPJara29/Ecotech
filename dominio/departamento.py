"""Departamento: agrupa empleados y tiene un gerente (que es un Empleado)."""


class Departamento:
    def __init__(self, nombre, gerente=None):
        self.__id_departamento = None
        self.nombre = nombre
        self.__gerente = gerente
        self.__empleados = []

    @property
    def id_departamento(self):
        return self.__id_departamento

    def asignar_id(self, valor):
        if self.__id_departamento is not None:
            raise ValueError("El ID ya fue asignado")
        self.__id_departamento = valor

    @property
    def gerente(self):
        return self.__gerente

    @property
    def empleados(self):
        return tuple(self.__empleados)

    def asignar_empleado(self, empleado):
        anterior = empleado.departamento
        if anterior is not None and anterior is not self:
            anterior._quitar_empleado(empleado)
        if empleado not in self.__empleados:
            self.__empleados.append(empleado)
        empleado._fijar_departamento(self)

    def _quitar_empleado(self, empleado):
        if empleado in self.__empleados:
            self.__empleados.remove(empleado)

    def reasignar_gerente(self, nuevo_gerente):
        if nuevo_gerente is None:
            return False
        self.__gerente = nuevo_gerente
        return True
