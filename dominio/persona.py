"""Clase base Persona: datos personales con encapsulamiento."""
import re

PATRON_RUT = re.compile(r"^\d{7,8}-[\dKk]$")
PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Persona:
    def __init__(self, rut, nombre, direccion="", telefono="", email=""):
        self.__rut = None
        self.__nombre = None
        self.__direccion = direccion
        self.__telefono = telefono
        self.__email = None
        self.__asignar_rut(rut)
        self.nombre = nombre
        self.email = email

    def __asignar_rut(self, rut):
        if not isinstance(rut, str) or not PATRON_RUT.match(rut):
            raise ValueError("RUT invalido. Formato esperado: 12345678-9")
        self.__rut = rut.upper()

    @property
    def rut(self):
        return self.__rut  

    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        if not valor or not valor.strip():
            raise ValueError("El nombre no puede estar vacio")
        self.__nombre = valor.strip()

    @property
    def direccion(self):
        return self.__direccion

    @direccion.setter
    def direccion(self, valor):
        self.__direccion = valor

    @property
    def telefono(self):
        return self.__telefono

    @telefono.setter
    def telefono(self, valor):
        self.__telefono = valor

    @property
    def email(self):
        return self.__email

    @email.setter
    def email(self, valor):
        if valor and not PATRON_EMAIL.match(valor):
            raise ValueError("Email invalido")
        self.__email = valor

    def __str__(self):
        return f"{self.__nombre} ({self.__rut})"
