import json
import logging
from confluent_kafka import Producer
from app.config import settings

logger = logging.getLogger(__name__)

class KafkaPublisher:
    def __init__(self):
        conf = {
            'bootstrap.servers': settings.KAFKA_BROKER_URL,
            'client.id': settings.PROJECT_NAME
        }
        self.producer = Producer(conf)

    def publish_event(self, topic: str, key: str, payload: dict):
        try:
            self.producer.produce(
                topic,
                key=key,
                value=json.dumps(payload),
                callback=self._delivery_report
            )
            self.producer.poll(0)
        except Exception as e:
            logger.error(f"Failed to publish event to {topic}: {e}")

    def _delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def flush(self):
        self.producer.flush()
