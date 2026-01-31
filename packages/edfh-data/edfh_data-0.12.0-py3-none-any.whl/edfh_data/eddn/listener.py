import logging
import os
from pathlib import Path
import sys
import time
import zlib

import orjson
import pika
import structlog
import zmq

RETRY_SLEEP_SECONDS = 15

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        os.getenv("LOG_LEVEL", logging.INFO)
    )
)
logger = structlog.get_logger(__name__)


def run():

    if Path(".env").is_file():
        from dotenv import load_dotenv

        logger.info(".env file present, loading environment variables from file")
        load_dotenv()

    EDDN_RELAY_URL = "tcp://eddn.edcd.io:9500"
    EDDN_SOCKET_TIMEOUT = 600000
    RMQ_EXCHANGE_NAME = "eddn_raw"

    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    subscriber.setsockopt(zmq.SUBSCRIBE, b"")
    subscriber.setsockopt(zmq.RCVTIMEO, EDDN_SOCKET_TIMEOUT)

    rmq_credentials = pika.PlainCredentials(
        username=os.getenv("RMQ_USER", "guest"),
        password=os.getenv("RMQ_PASSWD", "guest"),
    )
    rmq_connect_params = pika.ConnectionParameters(
        host=os.getenv("RMQ_HOST", "localhost"),
        credentials=rmq_credentials,
        heartbeat=20,
    )

    while True:
        try:
            logger.info("Connecting to EDDN relay", relay_url=EDDN_RELAY_URL)
            subscriber.connect(EDDN_RELAY_URL)

            logger.info("Connecting to RMQ exchange", exchange=RMQ_EXCHANGE_NAME)
            rmq_connection = None
            rmq_connection = pika.BlockingConnection(rmq_connect_params)
            rmq_channel = rmq_connection.channel()
            rmq_channel.exchange_declare(
                exchange=RMQ_EXCHANGE_NAME, exchange_type="fanout"
            )

            while True:
                try:
                    logger.debug("Receiving EDDN event")
                    event_raw = subscriber.recv()

                    if event_raw is False:
                        logger.info("No event available, disconnecting from EDDN relay")
                        subscriber.disconnect(EDDN_RELAY_URL)
                        break

                    event_json = zlib.decompress(event_raw)
                    event = orjson.loads(event_json)
                    logger.debug("EDDN Event received", event_json=event_json.decode())

                    logger.debug(
                        "Publishing event to RMQ exchange", exchange=RMQ_EXCHANGE_NAME
                    )
                    rmq_channel.basic_publish(
                        exchange=RMQ_EXCHANGE_NAME,
                        routing_key="",
                        body=event_raw,
                        properties=pika.BasicProperties(
                            delivery_mode=pika.DeliveryMode.Persistent
                        ),
                    )
                    logger.info(
                        "Event published to exchange",
                        schema=event["$schemaRef"],
                        msg_event=event["message"].get("event"),
                    )

                except KeyError as e:
                    logger.exception(e)

        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt received")

            logger.info("Disconnecting from EDDN relay")
            subscriber.disconnect(EDDN_RELAY_URL)

            logger.info("Closing connection to RMQ")
            rmq_connection.close()

            logger.info("Exiting application")
            sys.exit()

        except Exception as e:
            logger.exception(e)
            try:
                logger.info("Disconnecting from EDDN relay")
                subscriber.disconnect(EDDN_RELAY_URL)
            except Exception:
                pass

            try:
                logger.info("Closing connection to RMQ")
                if rmq_connection and rmq_connection.is_open:
                    rmq_connection.close()
            except Exception:
                pass

            logger.info(
                "Sleeping until next connection attempt", sleep_time=RETRY_SLEEP_SECONDS
            )
            time.sleep(RETRY_SLEEP_SECONDS)


if __name__ == "__main__":
    run()
