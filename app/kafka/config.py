import os
from pydantic_settings import BaseSettings

class KafkaConfig(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    KAFKA_TOPIC: str = os.getenv('KAFKA_TOPIC', 'example_topic')
    
    # Producer configs
    PRODUCER_ACKS: str = 'all'
    PRODUCER_RETRIES: int = 3
    PRODUCER_MAX_IN_FLIGHT: int = 1
    
    # Consumer configs
    CONSUMER_GROUP: str = 'example_group'
    AUTO_OFFSET_RESET: str = 'earliest'
    ENABLE_AUTO_COMMIT: bool = False

