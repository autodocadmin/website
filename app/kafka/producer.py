from confluent_kafka import Producer
from kafka.config import KafkaConfig
import json
from kafka.logger import logger

class KafkaProducer:
    def __init__(self, config: KafkaConfig):
        self.config = config
        self.producer = Producer({
            'bootstrap.servers': config.KAFKA_BOOTSTRAP_SERVERS,
            'acks': config.PRODUCER_ACKS,
            'retries': config.PRODUCER_RETRIES,
            'max.in.flight.requests.per.connection': config.PRODUCER_MAX_IN_FLIGHT,
            'error_cb': self._error_callback,
        })
        
    def _delivery_callback(self, err, msg):
        if err:
            logger.error("Message delivery failed", error=str(err), topic=msg.topic())
        else:
            logger.info("Message delivered", topic=msg.topic(), partition=msg.partition(), offset=msg.offset())
    
    def _error_callback(self, err):
        logger.error("Kafka error", error=str(err))
    
    def produce(self, message: dict,topic=None):
        try:
            self.producer.produce(
                topic=topic,
                value=json.dumps(message).encode('utf-8'),
                callback=self._delivery_callback
            )
            self.producer.poll(0)  # Trigger delivery reports
            
        except Exception as e:
            logger.error("Production error", error=str(e))
            raise
    
    def flush(self, timeout=10):
        self.producer.flush(timeout)