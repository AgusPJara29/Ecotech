# EcoTech Solutions – Sistema de Gestión (TI3021 · Unidad 2 · EF)

Avance estructural: modelo UML en Python, principios POO y conexión a base de datos.

## Cómo ejecutar
    python main.py
Opcional: copiar `.env.example` a `.env` para cambiar la ruta de la base (`DB_PATH`).
Solo usa la librería estándar (`sqlite3`).

## Estructura (arquitectura en capas)
    dominio/            lógica de negocio, sin SQL
      persona.py        clase base (rut, nombre, contacto)
      empleado.py       Empleado hereda de Persona
      departamento.py   Departamento (gerente + empleados)
      proyecto.py       Proyecto (dueño de sus RegistroTiempo)
      registro_tiempo.py
      informe.py        clase abstracta Informe + subclases (polimorfismo)
    infraestructura/    acceso a datos
      conexion.py       conexión, esquema y prueba de conexión
      empleado_repositorio.py / proyecto_repositorio.py   CRUD parametrizado
    main.py             demostración

## Decisiones de diseño (Paso 0 del laboratorio)
| Decisión | Opciones | La nuestra |
| --- | --- | --- |
| ¿Se borra de verdad? | DELETE real · activo = 0 | Empleado: borrado lógico (`activo = 0`) para conservar el historial de horas. Proyecto: DELETE real. |
| ¿Qué pasa con los hijos? | Cascada · impedir · huérfanos | Proyecto con registros de tiempo: se impide el borrado (clave foránea). |
| ¿Quién asigna el id? | La base · el programa | La base (AUTOINCREMENT). El RUT es la clave de Persona y se guarda como TEXTO. |

## Correspondencia UML -> código
| Relación | Implementación |
| --- | --- |
| Empleado es una Persona (herencia) | `class Empleado(Persona)` |
| Departamento 1 — 0..* Empleado | `Departamento.asignar_empleado()`; un empleado solo en un departamento |
| Departamento tiene 1 gerente | `Departamento.gerente` (un Empleado) |
| Empleado 0..* — 0..* Proyecto | `Proyecto.agregar_empleado()` / `quitar_empleado()` |
| Proyecto 1 ◆— 0..* RegistroTiempo (composición) | `Proyecto.registrar_horas()` crea los registros |
| RegistroTiempo -> Empleado | atributo `empleado` del registro |
| Informe (abstracta) <- InformeNomina, InformeProyecto | `exportar()` polimórfico |

## Seguridad
- Atributos privados (`__x`) con propiedades y validación en los setters.
- Consultas SQL siempre con marcadores `?` (prueba `' OR '1'='1` superada).
- Ruta de la base fuera del código (`.env`).
