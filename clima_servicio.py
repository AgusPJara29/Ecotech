from dataclasses import dataclass
from datetime import datetime, timezone
import re
import sqlite3
from typing import Any, Dict, Optional

from api_cliente import ApiCliente, ApiClienteError
from infraestructura.conexion import obtener_conexion


@dataclass
class ClimaRegistro:
    ubicacion: str
    temperatura_c: float
    velocidad_viento_kmh: float
    codigo_clima: int
    obtenido_en: str
    desde_cache: bool = False


class ClimaDeserializador:
    """Valida entradas y deserializa respuestas JSON de Open-Meteo."""

    _PATRON_UBICACION = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 _.-]{2,80}$")

    @classmethod
    def validar_ubicacion(cls, ubicacion: str) -> str:
        if not isinstance(ubicacion, str) or not ubicacion.strip():
            raise ValueError("La ubicación no puede estar vacía.")
        limpia = " ".join(ubicacion.strip().split())
        if not cls._PATRON_UBICACION.match(limpia):
            raise ValueError("La ubicación contiene caracteres no permitidos.")
        return limpia

    @staticmethod
    def validar_coordenadas(latitud: float, longitud: float) -> tuple[float, float]:
        lat = float(latitud)
        lon = float(longitud)
        if not (-90.0 <= lat <= 90.0):
            raise ValueError("La latitud debe estar entre -90 y 90.")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError("La longitud debe estar entre -180 y 180.")
        return lat, lon

    @classmethod
    def desde_json(cls, ubicacion: str, payload: Dict[str, Any]) -> ClimaRegistro:
        ubicacion_valida = cls.validar_ubicacion(ubicacion)

        if not isinstance(payload, dict) or not isinstance(payload.get("current_weather"), dict):
            raise ValueError("La respuesta de la API no contiene 'current_weather' válido.")

        actual = payload["current_weather"]

        if "temperature" not in actual or "windspeed" not in actual or "weathercode" not in actual:
            raise ValueError("Faltan campos climáticos obligatorios en la respuesta.")

        try:
            temperatura = float(actual["temperature"])
            viento = float(actual["windspeed"])
            codigo = int(actual["weathercode"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Los valores climáticos tienen un tipo inválido.") from exc

        if not (-90.0 <= temperatura <= 65.0):
            raise ValueError("Temperatura fuera de un rango meteorológico válido.")
        if viento < 0.0:
            raise ValueError("La velocidad del viento no puede ser negativa.")

        marca_tiempo = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return ClimaRegistro(
            ubicacion=ubicacion_valida,
            temperatura_c=temperatura,
            velocidad_viento_kmh=viento,
            codigo_clima=codigo,
            obtenido_en=marca_tiempo,
            desde_cache=False,
        )


class ClimaRepositorio:
    """Persiste registros climáticos en SQLite de forma idempotente y con Plan B."""

    def __init__(self, usar_contexto_externo: bool = False) -> None:
        self.usar_contexto_externo = usar_contexto_externo
        self._asegurar_tabla()

    def _asegurar_tabla(self) -> None:
        with obtener_conexion() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS registros_clima (
                    ubicacion TEXT PRIMARY KEY,
                    temperatura_c REAL NOT NULL,
                    velocidad_viento_kmh REAL NOT NULL,
                    codigo_clima INTEGER NOT NULL,
                    obtenido_en TEXT NOT NULL
                )
                """
            )

    def guardar_idempotente(self, registro: ClimaRegistro) -> None:
        """Inserta o actualiza por ubicación (PK), evitando duplicados al reejecutar."""
        with obtener_conexion() as con:
            con.execute(
                """
                INSERT INTO registros_clima (
                    ubicacion,
                    temperatura_c,
                    velocidad_viento_kmh,
                    codigo_clima,
                    obtenido_en
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(ubicacion) DO UPDATE SET
                    temperatura_c = excluded.temperatura_c,
                    velocidad_viento_kmh = excluded.velocidad_viento_kmh,
                    codigo_clima = excluded.codigo_clima,
                    obtenido_en = excluded.obtenido_en
                """,
                (
                    registro.ubicacion,
                    registro.temperatura_c,
                    registro.velocidad_viento_kmh,
                    registro.codigo_clima,
                    registro.obtenido_en,
                ),
            )

    def obtener_plan_b(self, ubicacion: str) -> Optional[ClimaRegistro]:
        """Recupera el último dato local almacenado junto con su antigüedad (obtenido_en)."""
        ubicacion_valida = ClimaDeserializador.validar_ubicacion(ubicacion)
        with obtener_conexion() as con:
            cursor = con.execute(
                """
                SELECT ubicacion, temperatura_c, velocidad_viento_kmh, codigo_clima, obtenido_en
                FROM registros_clima
                WHERE ubicacion = ?
                """,
                (ubicacion_valida,),
            )
            fila = cursor.fetchone()
            if fila is None:
                return None
            return ClimaRegistro(
                ubicacion=fila[0],
                temperatura_c=float(fila[1]),
                velocidad_viento_kmh=float(fila[2]),
                codigo_clima=int(fila[3]),
                obtenido_en=str(fila[4]),
                desde_cache=True,
            )

class ServicioClima:
    """Orquesta consulta en línea con respaldo automático a BD local (Plan B)."""

    def __init__(
        self,
        cliente: Optional[ApiCliente] = None,
        repositorio: Optional[ClimaRepositorio] = None,
    ) -> None:
        self.cliente = cliente or ApiCliente(base_url="https://api.open-meteo.com")
        self.repositorio = repositorio or ClimaRepositorio()

    def consultar_clima(self, ubicacion: str, latitud: float, longitud: float) -> Dict[str, Any]:
        ubicacion_limpia, (lat, lon) = (
            ClimaDeserializador.validar_ubicacion(ubicacion),
            ClimaDeserializador.validar_coordenadas(latitud, longitud),
        )

        try:
            payload = self.cliente.obtener_json(
                endpoint="/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": "true",
                },
            )
            registro = ClimaDeserializador.desde_json(ubicacion_limpia, payload)
            self.repositorio.guardar_idempotente(registro)
            return {
                "estado": "ok_en_linea",
                "mensaje": f"Clima actualizado para {registro.ubicacion} (obtenido_en: {registro.obtenido_en}).",
                "datos": registro,
            }
        except ApiClienteError as error_api:
            respaldo = self.repositorio.obtener_plan_b(ubicacion_limpia)
            if respaldo is not None:
                return {
                    "estado": "plan_b_local",
                    "mensaje": (
                        f"Aviso: {error_api}. Mostrando respaldo local para {respaldo.ubicacion} "
                        f"(obtenido_en: {respaldo.obtenido_en})."
                    ),
                    "datos": respaldo,
                }
            return {
                "estado": "sin_datos",
                "mensaje": f"Aviso: {error_api}. No existen datos locales previos para {ubicacion_limpia}.",
                "datos": None,
            }