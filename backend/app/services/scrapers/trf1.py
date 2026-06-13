"""Scraper TRF1 via API REST do PJe (Processo Judicial eletrônico)."""
from datetime import datetime, timezone

import httpx

from app.services.scrapers.base import MovimentacaoScraping, ResultadoScraping, ScraperBase, normaliza_cnj


class TRF1Scraper(ScraperBase):
    TRIBUNAL = "TRF1"
    # PJe TRF1 expõe endpoint público de consulta por número CNJ.
    _BASE_URL = "https://pje.trf1.jus.br/pje/ConsultaPublica/listView.seam"
    _API_URL = "https://pje.trf1.jus.br/pje-legado/seam/resource/consulta/processo/numeroProcesso"

    async def consultar(self, numero_cnj: str) -> ResultadoScraping:
        try:
            numero_limpo = normaliza_cnj(numero_cnj)
            resp = await self._client.get(
                self._API_URL,
                params={"numero": numero_cnj},
            )
            if resp.status_code == 404:
                # Tenta endpoint alternativo do PJe legado
                resp = await self._client.get(
                    f"https://pje.trf1.jus.br/pje/ConsultaPublica/movimento/{numero_limpo}",
                )

            if resp.status_code not in (200, 201):
                return self._erro(f"HTTP {resp.status_code} ao consultar TRF1")

            data = resp.json()
            return self._parse_pje_response(data)

        except httpx.TimeoutException:
            return self._erro("Timeout ao consultar TRF1")
        except Exception as exc:
            return self._erro(f"Erro inesperado TRF1: {exc}")

    def _parse_pje_response(self, data: dict | list) -> ResultadoScraping:
        movimentacoes: list[MovimentacaoScraping] = []

        # A API PJe retorna estrutura variável; tentamos as chaves mais comuns.
        if isinstance(data, list):
            items = data
        else:
            items = (
                data.get("movimentos")
                or data.get("andamentos")
                or data.get("movimentacoes")
                or []
            )

        vara = None
        classe = None
        if isinstance(data, dict):
            vara = data.get("orgaoJulgador") or data.get("vara")
            classe = data.get("classeProcessual") or data.get("classe")

        for item in items:
            data_str = item.get("dataMovimento") or item.get("data") or item.get("dtMovimento")
            descricao = item.get("descricao") or item.get("movimento") or item.get("texto") or ""
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
