"""Scraper TNU via SISTCON (portal de consulta pública)."""
from datetime import datetime, timezone

import httpx

from app.services.scrapers.base import MovimentacaoScraping, ResultadoScraping, ScraperBase


class TNUScraper(ScraperBase):
    TRIBUNAL = "TNU"
    _API_URL = "https://www.cjf.jus.br/juris/sistcon/pesquisar.php"

    async def consultar(self, numero_cnj: str) -> ResultadoScraping:
        try:
            resp = await self._client.get(
                self._API_URL,
                params={"numeroProcesso": numero_cnj, "formato": "json"},
            )

            if resp.status_code == 404:
                return ResultadoScraping(sucesso=True, movimentacoes=[])
            if resp.status_code != 200:
                return self._erro(f"HTTP {resp.status_code} ao consultar TNU")

            try:
                data = resp.json()
                return self._parse(data)
            except Exception:
                return self._parse_html(resp.text)

        except httpx.TimeoutException:
            return self._erro("Timeout ao consultar TNU")
        except Exception as exc:
            return self._erro(f"Erro inesperado TNU: {exc}")

    def _parse(self, data: dict | list) -> ResultadoScraping:
        movimentacoes: list[MovimentacaoScraping] = []
        items = data if isinstance(data, list) else (data.get("movimentos") or data.get("andamentos") or [])
        vara = data.get("orgaoJulgador") if isinstance(data, dict) else None

        for item in items:
            data_str = item.get("data") or item.get("dataMovimento") or ""
            descricao = item.get("descricao") or item.get("texto") or ""
            if not data_str or not descricao:
                continue
            try:
                dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                try:
                    dt = datetime.strptime(data_str[:10], "%d/%m/%Y").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            movimentacoes.append(MovimentacaoScraping(data_movimentacao=dt, descricao=str(descricao)))

        return ResultadoScraping(sucesso=True, movimentacoes=movimentacoes, vara=vara)

    def _parse_html(self, html: str) -> ResultadoScraping:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            movimentacoes: list[MovimentacaoScraping] = []

            for row in soup.select("table tr"):
                cols = row.find_all("td")
                if len(cols) < 2:
                    continue
                data_str = cols[0].get_text(strip=True)
                descricao = cols[1].get_text(strip=True)
                if not data_str or not descricao:
                    continue
                try:
                    dt = datetime.strptime(data_str[:10], "%d/%m/%Y").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                movimentacoes.append(MovimentacaoScraping(data_movimentacao=dt, descricao=descricao))

            return ResultadoScraping(sucesso=True, movimentacoes=movimentacoes)
        except Exception as exc:
            return self._erro(f"Falha no parsing HTML TNU: {exc}")
