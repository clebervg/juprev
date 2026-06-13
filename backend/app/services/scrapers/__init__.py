from app.services.scrapers.base import ResultadoScraping, ScraperBase
from app.services.scrapers.trf1 import TRF1Scraper
from app.services.scrapers.trf3 import TRF3Scraper
from app.services.scrapers.trf4 import TRF4Scraper
from app.services.scrapers.tnu import TNUScraper
from app.services.scrapers.stj import STJScraper

__all__ = [
    "ResultadoScraping", "ScraperBase",
    "TRF1Scraper", "TRF3Scraper", "TRF4Scraper", "TNUScraper", "STJScraper",
]
