import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

# Tipos de andamento mapeados por palavras-chave (ordem importa: mais específico primeiro).
_TIPO_KEYWORDS: list[tuple[str, list[str]]] = [
    ("SENTENCA",   ["sentença", "julgou procedente", "julgou improcedente", "extinguiu", "julgo"]),
    ("ACORDAO",    ["acórdão", "acordao", "turma recursal", "câmara", "julgamento do recurso"]),
    ("INTIMACAO",  ["intimação", "intime-se", "intimado", "cumpra-se", "notifique"]),
    ("RECURSO",    ["recurso", "apelação", "agravo", "embargos de declaração", "remessa"]),
    ("PETICAO",    ["petição", "manifestação", "contestação", "réplica", "juntada"]),
    ("DESPACHO",   ["despacho", "determino", "determine-se", "oficie-se", "designo"]),
]


@dataclass
class MovimentacaoScraping:
    data_movimentacao: datetime
    descricao: str
    documento_url: str | None = None

    @property
    def tipo(self) -> str:
        texto = self.descricao.lower()
        for tipo, keywords in _TIPO_KEYWORDS:
            if any(kw in texto for kw in keywords):
                return tipo
        return "OUTROS"

    @property
    def hash_conteudo(self) -> str:
        conteudo = f"{self.data_movimentacao.isoformat()}|{self.descricao}"
        return hashlib.sha256(conteudo.encode()).hexdigest()


@dataclass
class ResultadoScraping:
    sucesso: bool
    movimentacoes: list[MovimentacaoScraping] = field(default_factory=list)
    erro: str | None = None
    vara: str | None = None
    classe_processual: str | None = None


_NUMERO_CNJ_RE = re.compile(r"(\d{7})-?(\d{2})\.?(\d{4})\.?(\d)\.?(\d{2})\.?(\d{4})")


def normaliza_cnj(numero: str) -> str:
    """Garante formato sem pontuação para uso em URLs de API."""
    m = _NUMERO_CNJ_RE.search(numero.replace("-", "").replace(".", ""))
    if not m:
        return numero
    return "".join(m.groups())


class ScraperBase(ABC):
    TRIBUNAL: str = ""
    TIMEOUT_SEGUNDOS: int = 30

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=self.TIMEOUT_SEGUNDOS,
            headers={"User-Agent": "Juprev/1.0 (rastreamento processual automatico)"},
            follow_redirects=True,
        )

    async def __aenter__(self) -> "ScraperBase":
        return self

    async def __aexit__(self, *_) -> None:
        await self._client.aclose()

    @abstractmethod
    async def consultar(self, numero_cnj: str) -> ResultadoScraping:
        """Consulta o tribunal e retorna as movimentações encontradas."""

    def _erro(self, mensagem: str) -> ResultadoScraping:
        logger.warning("Scraper %s falhou: %s", self.TRIBUNAL, mensagem)
        return ResultadoScraping(sucesso=False, erro=mensagem)
