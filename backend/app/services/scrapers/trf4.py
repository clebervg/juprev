"""Scraper TRF4 via API pública eproc."""
from datetime import datetime, timezone

import httpx

from app.services.scrapers.base import MovimentacaoScraping, ResultadoScraping, ScraperBase, normaliza_cnj


class TRF4Scraper(ScraperBase):
    TRIBUNAL = "TRF4"
    # TRF4 utiliza o sistema eproc com endpoint público.
    _API_URL = "https://eproc.trf4.jus.br/eproc2trf4/controlador_ajax.php"

    async def consultar(self, numero_cnj: str) -> ResultadoScraping:
        try:
            numero_limpo = normaliza_cnj(numero_cnj)
            resp = await self._client.post(
                self._API_URL,
                data={
                    "acao": "consultar_processo_ajax",
                    "num_processo": numero_limpo,
                    "tipo_pesquisa": "numero_cnj",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if resp.status_code == 404:
                return ResultadoScraping(sucesso=True, movimentacoes=[])
            if resp.status_code != 200:
                return self._erro(f"HTTP {resp.status_code} ao consultar TRF4")

            # eproc pode retornar JSON ou HTML dependendo do endpoint
            try:
                data = resp.json()
                return self._parse_json(data)
            except Exception:
                return self._parse_html(resp.text)

        except httpx.TimeoutException:
            return self._erro("Timeout ao consultar TRF4")
        except Exception as exc:
            return self._erro(f"Erro inesperado TRF4: {exc}")

    def _parse_json(self, data: dict | list) -> ResultadoScraping:
        movimentacoes: list[MovimentacaoScraping] = []
        items = []
        vara = None
        classe = None

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("movimentos") or data.get("eventos") or []
            vara = data.get("orgaoJulgador") or data.get("vara")
            classe = data.get("classeProcessual") or data.get("classe")

        for item in items:
            data_str = item.get("dataEvento") or item.get("data") or ""
            descricao = item.get("descricao") or item.get("evento") or ""
            if not data_str or not descricao:
                continue
            try:
                dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                try:
                    dt = datetime.strptime(data_str[:10], "%d/%m/%Y").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            movimentacoes.append(MovimentacaoScraping(
                data_movimentacao=dt,
                descricao=str(descricao),
            ))

        return ResultadoScraping(sucesso=True, movimentacoes=movimentacoes, vara=vara, classe_processual=classe)

    def _parse_html(self, html: str) -> ResultadoScraping:
        """Fallback para parsing HTML do eproc (estrutura de tabela de eventos)."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            movimentacoes: list[MovimentacaoScraping] = []

            for row in soup.select("table.infraTable tr.infraTrClara, table.infraTable tr.infraTrEscura"):
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue
                data_str = cols[0].get_text(strip=True)
                descricao = cols[2].get_text(strip=True)
                if not data_str or not descricao:
                    continue
                try:
                    dt = datetime.strptime(data_str[:10], "%d/%m/%Y").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                movimentacoes.append(MovimentacaoScraping(data_movimentacao=dt, descricao=descricao))

            return ResultadoScraping(sucesso=True, movimentacoes=movimentacoes)
        except Exception as exc:
            return self._erro(f"Falha no parsing HTML TRF4: {exc}")
