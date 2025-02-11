from confluent_kafka import Consumer, KafkaException, KafkaError
from config import KafkaConfig
import json
from logger import logger
from typing import Callable

class KafkaConsumer:
    def __init__(self, config: KafkaConfig, message_handler: Callable,topic=None):
        self.config = config
        self.message_handler = message_handler
        self.consumer = Consumer({
            'bootstrap.servers': config.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': config.CONSUMER_GROUP,
            'auto.offset.reset': config.AUTO_OFFSET_RESET,
            'enable.auto.commit': config.ENABLE_AUTO_COMMIT,
            'error_cb': self._error_callback,
        })
        
        self.consumer.subscribe([topic])
    
    def _error_callback(self, err):
        logger.error("Kafka error", error=str(err))
    
    def start_consuming(self):
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info("Reached end of partition")
                    else:
                        logger.error("Consumer error", error=str(msg.error()))
                    continue
                
                try:
                    value = json.loads(msg.value().decode('utf-8'))
                    self.message_handler(value)
                    print(value)
                    self.consumer.commit(msg)
                    
                except Exception as e:
                    logger.error("Message processing failed", error=str(e))
                    
        except KeyboardInterrupt:
            logger.info("Shutting down consumer")
        
        finally:
            self.consumer.close() 