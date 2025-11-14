"""
Adapter Fincaraiz: expone la clase FincaraizScraper para el cargador dinámico.
Este adaptador envuelve la clase FincaraizRealScraper y expone el nombre de clase
esperado por el cargador dinámico en main.py.
"""

from .fincaraiz_real import FincaraizRealScraper

# El cargador dinámico depende de este nombre:
__all__ = ["FincaraizScraper"]


class FincaraizScraper:
    """
    Adaptador estándar entre el backend y el scraper real.
    Mantiene el nombre uniforme que espera main.py.
    """

    def __init__(self):
        # Inicializamos tu scraper real
        self.scraper = FincaraizRealScraper()

    async def scrape(self, limit=10, negocio="venta", ciudad="bucaramanga"):
        """
        Delegamos completamente la ejecución al scraper real.
        """
        return await self.scraper.scrape(
            limit=limit,
            negocio=negocio,
            ciudad=ciudad
        )
