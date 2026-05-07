"""
NIVEL 3 - El Cerebro
IA conversacional local con Ollama
"""
import requests
import yaml
import logging
from typing import Optional, Dict, Any
from core.mqtt_handler import MQTTHandler

logger = logging.getLogger("JARVIS.Brain")

class Brain:
    """
    Nivel 3: El Cerebro
    Gestiona la IA conversacional usando Ollama como backend local.
    """
    
    def __init__(self, mqtt_handler: Optional[MQTTHandler] = None, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.ollama_config = self.config['ollama']
        self.host = self.ollama_config['host']
        self.model = self.ollama_config['model']
        self.system_prompt = self.ollama_config['system_prompt']
        
        self.mqtt = mqtt_handler if mqtt_handler else MQTTHandler(config_path)
        if not mqtt_handler:
            self.mqtt.connect()
        
        self.conversation_history = []
        self.max_history = 10
        
        logger.info(f"Nivel 3 - Cerebro inicializado (modelo: {self.model})")
    
    def is_available(self) -> bool:
        """Verifica si Ollama esta ejecutandose"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def generate_response(self, prompt: str) -> str:
        """
        Genera una respuesta usando Ollama.
        Incluye historial de conversacion para contexto.
        """
        if not self.is_available():
            logger.error("Ollama no esta disponible")
            return "El cerebro no esta disponible. Asegurate de que Ollama este ejecutandose."
        
        logger.info(f"Procesando: {prompt[:100]}...")
        self.mqtt.publish('processing', {'status': 'thinking', 'message': 'Procesando...'})
        
        messages = [{"role": "system", "content": self.system_prompt}]
        
        for entry in self.conversation_history[-self.max_history:]:
            messages.append(entry)
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 150
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_response = result['message']['content'].strip()
                
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": assistant_response})
                
                if len(self.conversation_history) > self.max_history * 2:
                    self.conversation_history = self.conversation_history[-self.max_history * 2:]
                
                logger.info(f"Respuesta: {assistant_response[:100]}...")
                self.mqtt.publish('response', {
                    'text': assistant_response,
                    'source': 'ollama'
                })
                
                return assistant_response
            else:
                logger.error(f"Error Ollama: {response.status_code}")
                return "Lo siento, no pude procesar tu solicitud."
        
        except requests.exceptions.Timeout:
            logger.error("Timeout en Ollama")
            return "Estoy tardando demasiado en pensar. Se mas especifico."
        except requests.exceptions.ConnectionError:
            logger.error("No se pudo conectar a Ollama")
            return "No puedo conectar con el cerebro. Ejecuta 'ollama serve' en una terminal."
        except Exception as e:
            logger.error(f"Error en Brain: {e}")
            return f"Error de conexion con el cerebro: {str(e)}"
    
    def process(self, command_text: str, skill_result: Optional[Dict[str, Any]] = None) -> str:
        """
        Procesa un comando. Si ya fue manejado por skills, lo confirma.
        Si no, lo envia a Ollama.
        """
        if skill_result and skill_result.get('success'):
            return skill_result.get('response', 'Accion completada')
        
        return self.generate_response(command_text)
    
    def clear_history(self):
        """Limpia el historial de conversacion"""
        self.conversation_history = []
        logger.info("Historial de conversacion limpiado")
    
    def get_context(self) -> str:
        """Obtiene un resumen del contexto actual"""
        if not self.conversation_history:
            return "Sin conversacion previa"
        
        last = self.conversation_history[-4:]
        context = "Ultima conversacion:\n"
        for msg in last:
            role = "Usuario" if msg['role'] == 'user' else "JARVIS"
            context += f"{role}: {msg['content'][:80]}...\n"
        return context
    
    def change_model(self, model_name: str) -> bool:
        """Cambia el modelo de Ollama"""
        self.model = model_name
        logger.info(f"Modelo cambiado a: {model_name}")
        self.clear_history()
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("JARVIS OS - NIVEL 3: El Cerebro")
    print("=" * 60)
    print()
    
    brain = Brain()
    
    if not brain.is_available():
        print("ERROR: Ollama no esta disponible.")
        print("Ejecuta el script de instalacion: install_jarvis.ps1")
        exit(1)
    
    print(f"Ollama detectado. Modelo: {brain.model}")
    print()
    
    test_prompts = [
        "Hola, quien eres?",
        "Dime un dato curioso sobre el espacio",
        "Que puedes hacer?",
    ]
    
    for prompt in test_prompts:
        print(f"Usuario: {prompt}")
        response = brain.generate_response(prompt)
        print(f"JARVIS: {response}")
        print()
    
    print("Prueba completada")