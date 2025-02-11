from config import KafkaConfig
# from producer import KafkaProducer
from consumer import KafkaConsumer
import time
from logger import logger

def example_message_handler(message):
    logger.info("Received message", message=message)

def main():
    config = KafkaConfig()
    
    # Producer example
    # producer = KafkaProducer(config)
    # for i in range(5):
    #     message = {"id": i, "timestamp": time.time(), "data": f"Message {i}"}
    #     producer.produce(message)
    # producer.flush()
    
    # Consumer example
    consumer = KafkaConsumer(config, example_message_handler,topic="pranitkalebere")
    consumer.start_consuming()

if __name__ == "__main__":
    main()