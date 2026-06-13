"""Scraper STJ via API REST pública do portal de jurisprudência."""
from datetime import datetime, timezone

import httpx

from app.services.scrapers.base import MovimentacaoScraping, ResultadoScraping, ScraperBase


class STJScraper(ScraperBase):
    TRIBUNAL = "STJ"
    # STJ expõe API REST para consulta de processos.
    _API_URL = "https://ww2.stj.jus.br/processo/pesquisa/apiAcompanhamento/api/processos/buscar"

    async def consultar(self, numero_cnj: str) -> ResultadoScraping:
        try:
            resp = await self._client.get(
                self._API_URL,
                params={"numero": numero_cnj},
            )

            if resp.status_code == 404:
                return ResultadoScraping(sucesso=True, movimentacoes=[])
            if resp.status_code != 200:
                return self._erro(f"HTTP {resp.status_code} ao consultar STJ")

            data = resp.json()
            return self._parse(data)

        except httpx.TimeoutException:
            return self._erro("Timeout ao consultar STJ")
        except Exception as exc:
            return self._erro(f"Erro inesperado STJ: {exc}")

    def _parse(self, data: dict | list) -> ResultadoScraping:
        movimentacoes: list[MovimentacaoScraping] = []
        vara = None
        classe = None

        processo = data[0] if isinstance(data, list) and data else (data if isinstance(data, dict) else {})
        vara = processo.get("orgaoJulgador") or processo.get("relator")
        classe = processo.get("classe")

        items = processo.get("andamentos") or processo.get("movimentos") or []

        for item in items:
            data_str = item.get("dataAndamento") or item.get("data") or ""
            descricao = item.get("descricao") or item.get("andamento") or ""
            if not data_str or not descricao:
                continue

            try:
                dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                try:
                    dt = datetime.strptime(data_str[:19], "%d/%m/%Y %H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    try:
                        dt = datetime.strptime(data_str[:10], "%d/%m/%Y").replace(tzinfo=timezone.utc)
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
