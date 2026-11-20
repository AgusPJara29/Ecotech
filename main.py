import os
from datetime import date

from dominio.departamento import Departamento
from dominio.empleado import Empleado
from dominio.informe import InformeNomina, InformeProyecto
from dominio.proyecto import Proyecto
from infraestructura.conexion import crear_esquema, probar_conexion
from infraestructura.empleado_repositorio import EmpleadoRepositorio
from infraestructura.proyecto_repositorio import ProyectoRepositorio


def demo_dominio():
    ana = Empleado("12345678-9", "Ana Rojas", date(2024, 3, 1), 950_000)
    luis = Empleado("9876543-K", "Luis Soto", date(2025, 1, 10), 800_000)
    depto = Departamento("Investigacion y Desarrollo", gerente=ana)
    depto.asignar_empleado(ana)
    depto.asignar_empleado(luis)
    proyecto = Proyecto("Investigacion Tecnologica", "Tecnologia sostenible",
                        date(2026, 8, 30))
    proyecto.agregar_empleado(luis)
    print("Registro valido:",
          luis.registrar_horas(proyecto, date(2026, 9, 2), 7.5, "Investigacion"))
    print("Sin asignacion :",
          ana.registrar_horas(proyecto, date(2026, 9, 2), 4, "Reunion"))
    try:
        luis.sueldo_base = -5
    except ValueError as error:
        print("Encapsulamiento protege el sueldo ->", error)
    for informe in (InformeNomina([ana, luis]), InformeProyecto(proyecto)):
        print(informe.exportar())     # polimorfismo


def demo_base():
    print("\n== Paso 3: base de datos ==")
    crear_esquema()
    print("Conexion exitosa. SQLite version:", probar_conexion())

    repo = EmpleadoRepositorio()
    ana = Empleado("12345678-9", "Ana Rojas", date(2024, 3, 1), 950_000)
    repo.guardar(ana)
    print("Guardado, id asignado:", ana.id_empleado)
    print("Obtener:", repo.obtener("12345678-9"))
    print("Listar :", len(repo.listar()))
    ana.sueldo_base = 1_050_000
    print("Actualizar, filas:", repo.actualizar(ana))

    print("Inyeccion en listar  :", repo.listar(nombre_contiene="' OR '1'='1"))
    print("Inyeccion en obtener :", repo.obtener("' OR '1'='1"))

    print("Eliminar (logico):", repo.eliminar("12345678-9"))
    print("Tras eliminar, listar:", len(repo.listar()))

    prepo = ProyectoRepositorio()
    p = prepo.guardar(Proyecto("Piloto solar", "Paneles", date(2026, 9, 1)))
    print("Proyecto guardado:", p, "| listar:", len(prepo.listar()))
    print("Inyeccion proyectos:", prepo.listar("' OR '1'='1"))


if __name__ == "__main__":
    demo_dominio()
    demo_base()
