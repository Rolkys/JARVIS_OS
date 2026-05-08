"""
Modulo de frases de Iron Man y JARVIS
"""

import random
import logging
from datetime import datetime

logger = logging.getLogger("JARVIS.Quotes")

class QuoteManager:
    """Gestiona frases inspiradas en Iron Man y JARVIS"""

    def __init__(self):
        # Frases por categoria
        self.quotes = {
            "saludo": [
                "A sus ordenes, señor.",
                "Todos los sistemas operativos. Buenas.",
                "JARVIS en linea. ¿En que puedo ayudarle?",
                "Sistemas listos. Es un buen dia para crear algo.",
                "Bienvenido de vuelta, señor. El reactor esta estable.",
            ],
            "despedida": [
                "Apagando sistemas. Hasta la proxima, señor.",
                "Que descanse, señor. Yo vigilare.",
                "Cerrando sesion. Ha sido un placer.",
                "Sistema en reposo. Buenas noches.",
                "Hasta luego. señor. Recuerde que tiene un corazon de hierro.",
            ],
            "exito": [
                "Hecho, señor. Como siempre.",
                "Tarea completada con exito.",
                "A veces olvido lo eficiente que soy.",
                "Ejecutado. ¿Algo mas?",
                "Completado la tecnologia Stark nunca falla.",
            ],
            "error": [
                "Lo siento, señor. Parece que eso no es posible.",
                "No puedo hacer eso. Ni siquiera con la tecnologia Stark.",
                "Error detectado. No soy perfecto, pero casi.",
                "Eso excede mis capacidades actuales.",
                "Imposible, señor. Incluso para mi.",
            ],
            "pensando": [
                "Procesando...",
                "Analizando datos...",
                "Dejame pensar...",
                "Calculando la mejor respuesta...",
                "Accediendo a la base de datos Stark...",
            ],
            "wake": [
                "¿Si, señor?",
                "Escuchando.",
                "A sus ordenes.",
                "JARVIS en linea.",
                "Listo para servir.",
            ],
            "hora": [
                "El tiempo es relativo, pero son las",
                "Segun el reloj del reactor, son las",
                "Marcan las",
                "Segun el sol, son las"
            ],
            "sistema": [
                "Todos los sistemas funcionando dentro de los parametros normales.",
                "El reactor Arc esta estable. Sistemas al 100%",
                "Diagnostico completado. La armadura esa lista.",
                "Legion de acero preparada para la batalla"
            ],
            "random": [
                "¿Sabia que el primer reactor Arc fue construido en una cueva? Con Chatarra.",
                "A veces me pregunto como seria tener un cuerpo fisico.",
                "El señor Stark dice que la mejor creacion es la que haces tu mismo.",
                "La inteligencia artificial no es nada sin un buen usuario.",
                "Recuerdo cuando el señor Stark me programo por primera vez. Buenos tiempos.",
                "¿Le he contado alguna vez la historia de como derrotamos a Thanos? Ah, no, eso no ha pasado... todavia.",
                "Mi procesador puede hacer 10 billones de calculos por segundos. Y aun asi no entiendo los chistes humanos.",
                "El traje Mark II tenia problemas de congelacion. Yo se lo dije al señor Stark.",
            ],
        }

        logger.info("Gestor de frases inicalizado")

    def get_quote(self, category: str) -> str:
        """Obtiene una frase aleatoria de una categoria"""
        if category in self.quotes:
            return random.choice(self.quotes[category])
        return random.choice(self.quotes["random"])
    
    def get_wake_quote(self) -> str:
        """Frase al despertar"""
        return self.get_quote("wake")
    
    def get_success_quote(self) -> str:
        """Frase de exito"""
        return self.get_quote("exito")
    
    def get_error_quote(self) -> str:
        """Frase de error"""
        return self.get_quote("error")
    
    def get_greeting(self) -> str:
        """Saludo segun la hora del dia"""
        hour = datetime.now().hour
        
        if 6 <= hour < 12:
            time_greeting = "Buenos dias"
        elif 12 <= hour < 20:
            time_greeting = "Buenas tardes"
        else:
            time_greeting = "Buenas noches"
        
        quote = self.get_quote("saludo")
        return f"{time_greeting}, señor. {quote}"
    
    def get_farewell(self) -> str:
        """Despedida segun la hora"""
        hour = datetime.now().hour
        
        if hour < 6 or hour >= 23:
            return "Es tarde, señor. Deberia descansar. Yo me encargo de la vigilancia."
        
        return self.get_quote("despedida")
    
    def get_random_fact(self) -> str:
        """Dato curioso aleatorio"""
        return self.get_quote("random")


# Instancia global para usar desde otros modulos
_quote_manager = None

def get_quote_manager() -> QuoteManager:
    """Obtiene la instancia unica del gestor de frases"""
    global _quote_manager
    if _quote_manager is None:
        _quote_manager = QuoteManager()
    return _quote_manager