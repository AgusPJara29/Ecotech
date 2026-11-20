"""RegistroTiempo: horas de un empleado en un proyecto."""
HORAS_MAX_DIA = 24


class RegistroTiempo:
    def __init__(self, empleado, proyecto, fecha, horas_trabajadas,
                 descripcion):
        self.__id_registro = None
        self.__empleado = empleado
        self.__proyecto = proyecto
        self.__fecha = fecha
        self.__horas_trabajadas = horas_trabajadas
        self.__descripcion = descripcion
        if not self.validar_horas():
            raise ValueError(
                f"Horas inválidas: deben estar entre 0 y {HORAS_MAX_DIA}")

    @property
    def id_registro(self):
        return self.__id_registro

    @property
    def empleado(self):
        return self.__empleado

    @property
    def proyecto(self):
        return self.__proyecto

    @property
    def fecha(self):
        return self.__fecha

    @property
    def horas_trabajadas(self):
        return self.__horas_trabajadas

    @property
    def descripcion(self):
        return self.__descripcion

    def validar_horas(self):
        return 0 < self.__horas_trabajadas <= HORAS_MAX_DIA
