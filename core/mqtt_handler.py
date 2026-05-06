"""
Módulo de comunicación MQTT para JARVIS
Todos los componenetes se comunican a través de este bus de mensajes
"""

import paho.mqtt.client as mqtt
import json
import yaml
import logging
from typing import Callable, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("JARVIS.MQTT")

class MQTTHandler:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.mqtt_config = self.config['mqtt']
        self.client = mqtt.Client(client_id="JARVIS_Core")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.handlers = {}
        self.connected = False
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info("Conectado al broker MQTT")
        else:
            logger.error(f"Error al conectar al broker MQTT: {rc}")
    
    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()

        if topic in self.handlers:
            try:
                data = json.loads(payload) if payload else {}
                self.handlers[topic](data)
            except json.JSONDecodeError:
                self.handlers[topic](payload)

    def connect(self):
        """Conectar al broker MQTT"""
        try:
            self.client.connect(
                self.mqtt_config['broker'],
                self.mqtt_config['port'],
                60
            )
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Error al conectar al broker MQTT: {e}")
            return False
        
    def publish(self, topic_key: str, data: dict = None):
        """Publicar mensaje en un topic"""
        topic = self.mqtt_config['topics'].get(topic_key, topic_key)
        payload = json.dumps(data) if data else ""
        self.client.publish(topic, payload)
        logger.debug(f"Publicado en {topic}: {payload[:100]}")

    def subscribe(self, topic_key: str, handler: Callable):
        """Suscribirse a un topic con un handler"""
        topic = self.mqtt_config['topics'].get(topic_key, topic_key)
        self.handlers[topic] = handler
        self.client.subscribe(topic)
        logger.info(f"Suscrito a {topic}")

    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()