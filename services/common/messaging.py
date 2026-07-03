import json
import logging
from typing import Callable, Any, Dict
from confluent_kafka import Producer, Consumer, KafkaError
from .config import settings

logger = logging.getLogger(__name__)

class KafkaEventPublisher:
    """Publishes domain events to Kafka topics."""
    
    def __init__(self):
        conf = {
            'bootstrap.servers': settings.KAFKA_BROKER_URL,
            'client.id': settings.PROJECT_NAME
        }
        self.producer = Producer(conf)

    def publish(self, topic: str, key: str, payload: Dict[str, Any]):
        """Publishes a JSON payload to a Kafka topic."""
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
        """Wait for all messages to be delivered."""
        self.producer.flush()


class KafkaEventConsumer:
    """Consumes domain events from Kafka topics."""

    def __init__(self, group_id: str, topics: list[str]):
        conf = {
            'bootstrap.servers': settings.KAFKA_BROKER_URL,
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        }
        self.consumer = Consumer(conf)
        self.consumer.subscribe(topics)

    def consume(self, callback: Callable[[Dict[str, Any]], None], timeout: float = 1.0):
        """Polls for a single message and invokes the callback on success."""
        msg = self.consumer.poll(timeout)

        if msg is None:
            return
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                logger.debug(f"End of partition reached {msg.topic()}/{msg.partition()}")
            else:
                logger.error(f"Error while consuming message: {msg.error()}")
        else:
            try:
                payload = json.loads(msg.value().decode('utf-8'))
                callback(payload)
            except Exception as e:
                logger.error(f"Failed to process message from {msg.topic()}: {e}")

    def close(self):
        self.consumer.close()

def get_event_publisher() -> KafkaEventPublisher:
    return KafkaEventPublisher()
