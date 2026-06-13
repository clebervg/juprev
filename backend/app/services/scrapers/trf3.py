"""Scraper TRF3 via API de consulta pública do PJe."""
from datetime import datetime, timezone

import httpx

from app.services.scrapers.base import MovimentacaoScraping, ResultadoScraping, ScraperBase, normaliza_cnj


class TRF3Scraper(ScraperBase):
    TRIBUNAL = "TRF3"
    _API_URL = "https://pje.trf3.jus.br/pje/ConsultaPublica/movimento"

    async def consultar(self, numero_cnj: str) -> ResultadoScraping:
        try:
            resp = await self._client.get(
                self._API_URL,
                params={"numeroProcesso": numero_cnj},
            )
            if resp.status_code == 404:
                return ResultadoScraping(sucesso=True, movimentacoes=[])
            if resp.status_code != 200:
                return self._erro(f"HTTP {resp.status_code} ao consultar TRF3")

            data = resp.json()
            return self._parse(data)

        except httpx.TimeoutException:
            return self._erro("Timeout ao consultar TRF3")
        except Exception as exc:
            return self._erro(f"Erro inesperado TRF3: {exc}")

    def _parse(self, data: dict | list) -> ResultadoScraping:
        movimentacoes: list[MovimentacaoScraping] = []

        if isinstance(data, list):
            items = data
        else:
            items = data.get("movimentos") or data.get("andamentos") or []

        vara = data.get("orgaoJulgador") if isinstance(data, dict) else None
        classe = data.get("classeProcessual") if isinstance(data, dict) else None

        for item in items:
            data_str = item.get("dataMovimento") or item.get("data") or ""
            descricao = item.get("descricao") or item.get("movimento") or ""
            if not data_str or not descricao:
                continue

            try:
                dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                try:
                    dt = datetime.strptime(data_str[:19], "%d/%m/%Y %H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue

            movimentacoes.append(MovimentacaoScraping(
                data_movimentacao=dt,
                descricao=str(descricao),
                documento_url=item.get("urlDocumento"),
            ))

        return ResultadoScraping(
            sucesso=True,
            movimentacoes=movimentacoes,
            vara=vara,
            classe_processual=classe,
        )
