import os
import sqlite3
from datetime import date

from api_cliente import ApiCliente, ApiClienteError
from clima_servicio import ServicioClima
from dominio.departamento import Departamento
from dominio.empleado import Empleado
from dominio.informe import InformeNomina, InformeProyecto
from dominio.proyecto import Proyecto
from infraestructura.conexion import crear_esquema, probar_conexion
from infraestructura.empleado_repositorio import EmpleadoRepositorio
from infraestructura.proyecto_repositorio import ProyectoRepositorio
from seguridad_usuarios import ErrorAutenticacion, GestorSeguridad

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
    empleado_a_actualizar = ana
    try:
        repo.guardar(ana)
        print("Guardado, id asignado:", ana.id_empleado)
    except sqlite3.IntegrityError:
        print("Empleado ya registrado previamente, continuando prueba...")
        obtenido = repo.obtener("12345678-9")
        if obtenido is not None:
            empleado_a_actualizar = obtenido

    print("Obtener:", repo.obtener("11223344-5"))
    print("Listar :", len(repo.listar()))
    empleado_a_actualizar.sueldo_base = 1_050_000
    print("Actualizar, filas:", repo.actualizar(empleado_a_actualizar))

    print("Inyeccion en listar  :", repo.listar(nombre_contiene="' OR '1'='1"))
    print("Inyeccion en obtener :", repo.obtener("' OR '1'='1"))

    print("Eliminar (logico):", repo.eliminar("11223344-5"))
    print("Tras eliminar, listar:", len(repo.listar()))

    prepo = ProyectoRepositorio()
    p = prepo.guardar(Proyecto("Piloto solar", "Paneles", date(2026, 9, 1)))
    print("Proyecto guardado:", p, "| listar:", len(prepo.listar()))
    print("Inyeccion proyectos:", prepo.listar("' OR '1'='1"))

def demo_unidad3():
    print("\n== Unidad 3: Seguridad, API resiliente y Plan B ==")
    seguridad = GestorSeguridad()

    try:
        usuario = seguridad.autenticar("admin_ecotech", "EcoTech2026!")
        print(f"Sesión iniciada como '{usuario.username}' (rol: {usuario.rol}).")
    except ErrorAutenticacion as err:
        print("Acceso denegado:", err)
        return

    servicio_clima = ServicioClima()
    resultado = servicio_clima.consultar_clima("Santiago", -33.45, -70.66)
    print(f"[{resultado['estado']}] {resultado['mensaje']}")
    if resultado["datos"] is not None:
        d = resultado["datos"]
        print(
            f"  -> {d.ubicacion}: {d.temperatura_c} °C | "
            f"Viento: {d.velocidad_viento_kmh} km/h | obtenido_en: {d.obtenido_en}"
        )

    cliente_invalido = ApiCliente(base_url="https://api.open-meteo.com", max_intentos=3)
    try:
        cliente_invalido.obtener_json(endpoint="/v1/endpoint-inexistente-e3")
    except ApiClienteError as err_http:
        print(f"Prueba URL inválida controlada -> {err_http} (HTTP {err_http.codigo_http})")

if __name__ == "__main__":
    demo_dominio()
    demo_base()
    demo_unidad3()
