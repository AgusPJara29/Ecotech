"""Empleado hereda de Persona (un Empleado ES una Persona)."""
from dominio.persona import Persona


class Empleado(Persona):

    def __init__(self, rut, nombre, fecha_ingreso, sueldo_base,
                 direccion="", telefono="", email=""):
        super().__init__(rut, nombre, direccion, telefono, email)
        self.__id_empleado = None 
        self.__fecha_ingreso = fecha_ingreso
        self.__sueldo_base = 0
        self.__departamento = None
        self.sueldo_base = sueldo_base 

    @property
    def id_empleado(self):
        return self.__id_empleado

    def asignar_id(self, valor):
        if self.__id_empleado is not None:
            raise ValueError("El ID ya fue asignado")
        self.__id_empleado = valor

    @property
    def fecha_ingreso(self):
        return self.__fecha_ingreso

    @property
    def sueldo_base(self):
        return self.__sueldo_base

    @sueldo_base.setter
    def sueldo_base(self, valor):
        if valor <= 0:
            raise ValueError("El sueldo debe ser mayor a 0")
        self.__sueldo_base = valor

    @property
    def departamento(self):
        return self.__departamento

    def _fijar_departamento(self, departamento):
        """Uso interno: lo invoca Departamento.asignar_empleado()."""
        self.__departamento = departamento


    def registrar_horas(self, proyecto, fecha, horas, descripcion):
        """Delega en el Proyecto, que es dueño de sus registros."""
        return proyecto.registrar_horas(self, fecha, horas, descripcion)
    
    def get_salario(self):
        return self.__sueldo_base
