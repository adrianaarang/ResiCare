"""
Agregacion en memoria de metricas de uso por proveedor (coste, tokens,
latencia media), para que el dashboard pueda mostrar totales acumulados
sin tener que recalcularlos el mismo en cada peticion.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class MetricasProveedor:
    peticiones: int = 0
    tokens_entrada_total: int = 0
    tokens_salida_total: int = 0
    coste_total_usd: float = 0.0
    latencia_total_ms: float = 0.0

    @property
    def latencia_media_ms(self) -> float:
        if self.peticiones == 0:
            return 0.0
        return round(self.latencia_total_ms / self.peticiones, 1)


class RegistroMetricas:
    def __init__(self):
        self._por_proveedor: Dict[str, MetricasProveedor] = {}

    def registrar(
        self,
        proveedor: str,
        tokens_entrada: int,
        tokens_salida: int,
        latencia_ms: float,
        coste_usd: float,
    ) -> None:
        metricas = self._por_proveedor.setdefault(proveedor, MetricasProveedor())
        metricas.peticiones += 1
        metricas.tokens_entrada_total += tokens_entrada
        metricas.tokens_salida_total += tokens_salida
        metricas.coste_total_usd += coste_usd
        metricas.latencia_total_ms += latencia_ms

    def resumen(self) -> dict:
        return {
            proveedor: {
                "peticiones": m.peticiones,
                "tokens_entrada_total": m.tokens_entrada_total,
                "tokens_salida_total": m.tokens_salida_total,
                "coste_total_usd": round(m.coste_total_usd, 6),
                "latencia_media_ms": m.latencia_media_ms,
            }
            for proveedor, m in self._por_proveedor.items()
        }


registro_global = RegistroMetricas()