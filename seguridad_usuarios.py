from dataclasses import dataclass
import os
import re

import bcrypt
from dotenv import load_dotenv

from infraestructura.conexion import obtener_conexion

load_dotenv()


class ErrorAutenticacion(Exception):
    """Error controlado de autenticación o autorización."""


@dataclass
class UsuarioAutenticado:
    username: str
    rol: str


class GestorSeguridad:
    """Gestiona usuarios con contraseñas hasheadas con salt (bcrypt) y validación de entradas."""

    _PATRON_USUARIO = re.compile(r"^[a-zA-Z0-9_.-]{3,30}$")

    def __init__(self) -> None:
        self._asegurar_tabla_usuarios()
        self._sembrar_usuario_inicial()

    def _asegurar_tabla_usuarios(self) -> None:
        with obtener_conexion() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios_seguridad (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    rol TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def validar_credenciales_entrada(username: str, password: str) -> tuple[str, str]:
        if not isinstance(username, str) or not username.strip():
            raise ValueError("El nombre de usuario no puede estar vacío.")
        usuario_limpio = username.strip()
        if not GestorSeguridad._PATRON_USUARIO.match(usuario_limpio):
            raise ValueError("El nombre de usuario tiene un formato inválido.")

        if not isinstance(password, str) or len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        if len(password.encode("utf-8")) > 72:
            raise ValueError("La contraseña excede el límite de 72 bytes de bcrypt.")

        return usuario_limpio, password

    @staticmethod
    def hashear_password(password: str) -> str:
        _, clave_valida = GestorSeguridad.validar_credenciales_entrada("usuario_temp", password)
        hashed = bcrypt.hashpw(clave_valida.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    @staticmethod
    def verificar_password(password: str, password_hash: str) -> bool:
        if not password or not password_hash:
            return False
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            return False

    def registrar_usuario(self, username: str, password: str, rol: str = "operador") -> None:
        usuario_limpio, clave_valida = self.validar_credenciales_entrada(username, password)
        rol_limpio = (rol or "operador").strip().lower()
        if rol_limpio not in {"admin", "operador", "lector"}:
            raise ValueError("Rol no permitido.")

        password_hash = self.hashear_password(clave_valida)
        with obtener_conexion() as con:
            con.execute(
                """
                INSERT INTO usuarios_seguridad (username, password_hash, rol)
                VALUES (?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    password_hash = excluded.password_hash,
                    rol = excluded.rol
                """,
                (usuario_limpio, password_hash, rol_limpio),
            )

    def _sembrar_usuario_inicial(self) -> None:
        """Crea un usuario demo inicial si la tabla está vacía, usando variables de entorno si existen."""
        usuario_env = os.getenv("ECOTECH_DEMO_USER", "admin_ecotech")
        clave_env = os.getenv("ECOTECH_DEMO_PASS", "EcoTech2026!")
        with obtener_conexion() as con:
            cursor = con.execute("SELECT COUNT(*) FROM usuarios_seguridad")
            total = cursor.fetchone()[0]
        if total == 0:
            self.registrar_usuario(usuario_env, clave_env, rol="admin")

    def autenticar(self, username: str, password: str) -> UsuarioAutenticado:
        usuario_limpio, clave_valida = self.validar_credenciales_entrada(username, password)
        with obtener_conexion() as con:
            cursor = con.execute(
                """
                SELECT username, password_hash, rol
                FROM usuarios_seguridad
                WHERE username = ?
                """,
                (usuario_limpio,),
            )
            fila = cursor.fetchone()

        if fila is None or not self.verificar_password(clave_valida, str(fila[1])):
            raise ErrorAutenticacion("Credenciales inválidas.")

        return UsuarioAutenticado(username=str(fila[0]), rol=str(fila[2]))