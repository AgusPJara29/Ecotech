import random
import time
from typing import Any, Dict, Optional

import requests
from requests.exceptions import RequestException, Timeout


class ApiClienteError(Exception):
    """Error controlado del cliente de API sin exponer detalles sensibles."""

    def __init__(self, mensaje: str, codigo_http: Optional[int] = None, es_red: bool = False):
        super().__init__(mensaje)
        self.codigo_http = codigo_http
        self.es_red = es_red


class ApiCliente:
    """Cliente HTTP resiliente con timeout obligatorio, backoff exponencial y control de HTTP."""

    ESTADOS_REINTENTABLES = {500, 502, 503, 504}

    def __init__(
        self,
        base_url: str,
        timeout: float = 8.0,
        max_intentos: int = 3,
        backoff_base: float = 0.5,
        session: Optional[requests.Session] = None,
    ) -> None:
        if not base_url or not base_url.strip():
            raise ValueError("La URL base de la API no puede estar vacía.")
        if timeout <= 0:
            raise ValueError("El timeout debe ser mayor a 0 segundos.")
        if max_intentos < 1 or max_intentos > 4:
            raise ValueError("El máximo de reintentos debe estar entre 1 y 4.")

        self.base_url = base_url.rstrip("/")
        self.timeout = float(timeout)
        self.max_intentos = int(max_intentos)
        self.backoff_base = float(backoff_base)
        self.session = session or requests.Session()

    def _calcular_espera_429(self, response: requests.Response, intento: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                segundos = float(retry_after.strip())
                if segundos >= 0:
                    return min(segundos, 15.0)
            except ValueError:
                pass
        return self._calcular_backoff(intento)

    def _calcular_backoff(self, intento: int) -> float:
        jitter = random.uniform(0.05, 0.25)
        return (self.backoff_base * (2 ** (intento - 1))) + jitter

    def obtener_json(
        self,
        endpoint: str = "",
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        ruta = endpoint.lstrip("/")
        url = f"{self.base_url}/{ruta}" if ruta else self.base_url

        for intento in range(1, self.max_intentos + 1):
            try:
                respuesta = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
                codigo = respuesta.status_code

                if codigo == 200:
                    try:
                        data = respuesta.json()
                    except ValueError as exc:
                        raise ApiClienteError(
                            "La respuesta del servicio externo no tiene un formato JSON válido.",
                            codigo_http=codigo,
                        ) from exc

                    if not isinstance(data, dict):
                        raise ApiClienteError(
                            "La estructura JSON recibida no es un objeto válido.",
                            codigo_http=codigo,
                        )
                    return data

                if codigo == 429:
                    if intento < self.max_intentos:
                        espera = self._calcular_espera_429(respuesta, intento)
                        time.sleep(espera)
                        continue
                    raise ApiClienteError(
                        "El servicio externo limitó temporalmente las solicitudes (HTTP 429).",
                        codigo_http=codigo,
                    )

                if 400 <= codigo < 500:
                    # Errores 4xx (ej. 404 URL inválida): no se reintentan.
                    raise ApiClienteError(
                        f"Solicitud rechazada por el servicio externo (HTTP {codigo}).",
                        codigo_http=codigo,
                    )

                if codigo in self.ESTADOS_REINTENTABLES or codigo >= 500:
                    if intento < self.max_intentos:
                        time.sleep(self._calcular_backoff(intento))
                        continue
                    raise ApiClienteError(
                        f"El servicio externo presentó un error temporal (HTTP {codigo}).",
                        codigo_http=codigo,
                    )

                raise ApiClienteError(
                    f"Respuesta no esperada del servicio externo (HTTP {codigo}).",
                    codigo_http=codigo,
                )

            except ApiClienteError:
                raise
            except Timeout:
                if intento < self.max_intentos:
                    time.sleep(self._calcular_backoff(intento))
                    continue
                raise ApiClienteError(
                    "Tiempo de espera agotado al consultar el servicio externo.",
                    es_red=True,
                )
            except RequestException:
                if intento < self.max_intentos:
                    time.sleep(self._calcular_backoff(intento))
                    continue
                raise ApiClienteError(
                    "No fue posible establecer conexión con el servicio externo.",
                    es_red=True,
                )

        raise ApiClienteError("No se pudo completar la consulta tras agotar los reintentos.", es_red=True)