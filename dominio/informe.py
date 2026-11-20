"""Clase abstracta Informe y subclases: polimorfismo con exportar()."""
from abc import ABC, abstractmethod
from datetime import date


class Informe(ABC):
    def __init__(self, titulo, fecha=None):
        self.titulo = titulo
        self.fecha = fecha or date.today()

    @abstractmethod
    def exportar(self):
        """Cada subclase decide cómo exporta."""


class InformeNomina(Informe):
    def __init__(self, empleados):
        super().__init__("Nómina de empleados")
        self.__empleados = empleados

    def exportar(self):
        lineas = [f"{e.nombre};{e.get_salario()}" for e in self.__empleados]
        return "\n".join([self.titulo] + lineas)


class InformeProyecto(Informe):
    def __init__(self, proyecto):
        super().__init__(f"Horas del proyecto {proyecto.nombre}")
        self.__proyecto = proyecto

    def exportar(self):
        total = self.__proyecto.obtener_horas_totales()
        return f"{self.titulo}\nTotal horas: {total}"
