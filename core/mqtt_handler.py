"""
Modulo de comunicacion MQTT para JARVIS
"""
import paho.mqtt.client as mqtt
import json
import yaml
import logging
from typing import Callable

logger = logging.getLogger("JARVIS.MQTT")

class MQTTHandler:
    """Maneja toda la comunicacion entre modulos de JARVIS"""

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.mqtt_config = self.config['mqtt']
        self.topics = self.mqtt_config['topics']

        self.client = mqtt.Client(
            client_id="JARVIS_Core",
            protocol=mqtt.MQTTv311
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self.handlers = {}
        self.connected = False

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info("Conectado al broker MQTT")
            for topic in self.handlers:
                self.client.subscribe(topic)
        else:
            logger.error(f"Error conexion MQTT (codigo {rc})")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        if topic in self.handlers:
            try:
                data = json.loads(payload) if payload else {}
                self.handlers[topic](data)
            except json.JSONDecodeError:
                self.handlers[topic](payload)
            except Exception as e:
                logger.error(f"Error procesando mensaje en {topic}: {e}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            logger.warning("Desconexion inesperada del broker MQTT")

    def connect(self) -> bool:
        try:
            self.client.connect(
                self.mqtt_config['broker'],
                self.mqtt_config['port'],
                keepalive=60
            )
            self.client.loop_start()
            return True
        except ConnectionRefusedError:
            logger.error("Broker MQTT no disponible")
            return False
        except Exception as e:
            logger.error(f"Error conectando a MQTT: {e}")
            return False

    def publish(self, topic_key: str, data: dict = None):
        if not self.connected:
            return

        topic = self.topics.get(topic_key, topic_key)
        payload = json.dumps(data) if data else "{}"
        self.client.publish(topic, payload)

    def subscribe(self, topic_key: str, handler: Callable):
        topic = self.topics.get(topic_key, topic_key)
        self.handlers[topic] = handler
        if self.connected:
            self.client.subscribe(topic)
        logger.info(f"Suscrito a: {topic}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Desconectado de MQTT")