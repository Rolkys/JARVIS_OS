"""
Modulo de noticias RSS para JARVIS
"""

import feedparser
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger("JARVIS.News")

class NewsReader:
    """Lector de noticias por RSS"""

    def __init__(self):
        # Feeds RSS publicos en español
        self.feeds = {
            "nacional":[
                {"name": "El Pais",     "url":"https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"},
                {"name": "El mundo",    "url":"https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml"},
                {"name": "RTVE",        "url":"https://www.rtve.es/api/noticias.xml"},
                {"name": "20 minutos",  "url":"https://www.20minutos.es/rss/"},
            ],
            "tecnologia":[
                {"name": "Xataka",      "url":"https://www.xataka.com/index.xml"},
                {"name": "Genbeta",     "url":"https://www.genbeta.com/index.xml"},
                {"name": "MuyComputer", "url":"https://www.muycomputer.com/feed/"},
            ],
            "videojuego":[
                {"name": "Vandal",          "url":"https://vandal.elespanol.com/rss"},
                {"name": "HobbyConsolas",   "url":"https://www.hobbyconsolas.com/rss"},
                {"name": "3DJuegos",        "url":"https://www.3djuegos.com/index.xml"},
            ],
            "deportes":[
                {"name": "Marca",   "url":"https://e00-marca.uecdn.es/rss/portada.xml"},
                {"name": "AS",      "url":"https://as.com/rss.xml"},
                {"name": "Sport",   "url":"https://www.sport.es/es/rss/"},
            ],
            "ciencia":[
                {"name": "MuyInteresante", "url":"https://www.muyinteresante.com/feed/"},
                {"name": "Naukas", "url":"https://naukas.com/feed/"},
            ],
        }
    
    def get_news(self, category: str = "nacional", limit: int = 5) -> List[Dict]:
        """Obtiene noticias de una categoria"""
        if category not in self.feeds:
            return[]
        
        all_news = []

        for feed in self.feeds[category]:
            try:
                data = feedparser.parse(feed["url"])

                for entry in data.entries[:3]: # Max 3 por fuente
                    all_news.append({
                        "title": entry.get("title", "Sin titulo"),
                        "source": feed["name"],
                        "summary": self._clean_summary(entry.get("summary", "")),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", "Fecha desconocida"),
                    })
            except Exception as e:
                logger.error(f"Error leyendo {feed['name']}: {e}")
        
        # Orden y limitar
        all_news = all_news[:limit]

        return all_news
    
    def _clean_summary(self, text: str)-> str:
        """Limpia el texto HTML del resumen"""

        import re

        # Quitar etiquetas HTML
        text = re.sub(r'<[^>]+>', '', text)
        # Quitar espacios extra
        text = re.sub(r'\s+', ' ', text)
        #Limitar longitud
        if len(text) > 150:
            text = text[:147] + "..."
        return text.strip()
    
    def format_for_speech(self, category: str = "nacional", limit: int = 3) -> str:
        """Formatea noticias para ser leidas por voz"""
        news = self.get_news(category, limit)

        if not news:
            return f"No pude obtener noticies de {category}"
        
        response = f"Noticias de {category}"
        for i, item in enumerate(news, 1):
            response += f"{i}. {item['title']}."
        
        return response
    
    def format_detailed(self, category: str = "nacional", limit: int = 3) -> str:
        """Formato detellado con resumenes"""
        
        news = self.get_news(category, limit)

        if not news:
            return f"No puedes obtener noticias de {category}"
        
        response = f"Noticias de {category}"
        for i, item in enumerate(news, 1):
            response += f"{i}. {item['title']}\n"
            response += f"  Fuente: {item['source']}\n"
            response += f"  {item['summary']}\n\n"

        return response
    
    def list_categories(self) -> str:
        """Lista las cateforias disponibles"""
        return "Categorias: " + ", ".join(self.feeds.keys())
    