import datetime as dt
import logging
import os
import sys
from typing import Mapping
import zlib

import orjson
import pika
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError
import structlog

from edfh_data.db.crud import create_update_station
from edfh_data.db.crud import create_update_station_market
from edfh_data.db.crud import create_update_system
from edfh_data.db.utils import init_db
from edfh_data.exceptions import EventTooOldError
from edfh_data.models import Station
from edfh_data.models import StationMarket
from edfh_data.models import System

JOURNAL_V1_SCHEMA = "https://eddn.edcd.io/schemas/journal/1"
COMMODITY_V3_SCHEMA = "https://eddn.edcd.io/schemas/commodity/3"

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        os.getenv("LOG_LEVEL", logging.INFO)
    )
)
logger = structlog.get_logger(__name__)


def handle_journal_v1_fsdjump(message: Mapping) -> None:
    """Handle the journal/1 messages with event==FSDJump."""

    system = System(**message)

    logger.info("Handling FSDJump journal event", system_name=system.system_name)

    create_update_system(system)


def handle_journal_v1_docked(message: Mapping) -> None:
    """Handle the journal/1 message with event==Docked."""

    station = Station(**message)

    logger.info(
        "Handling Docked journal event",
        system_name=station.system_name,
        station_name=station.station_name,
    )

    create_update_station(station)


def handle_commodity_v3(message: Mapping) -> None:
    """Handle the commodity/3 message."""

    market = StationMarket(**message)

    logger.info("Handling commodity event", market_id=market.market_id)

    create_update_station_market(market)
    pass


def handle_eddn_event(
    event: dict, max_age: dt.timedelta = dt.timedelta(hours=1)
) -> bool:
    """Handle any eddn event."""
    handled = False
    message = event["message"]

    now = dt.datetime.now(tz=dt.timezone.utc)
    message_datetime = dt.datetime.fromisoformat(message["timestamp"]).replace(
        tzinfo=dt.timezone.utc
    )
    messag_age = now - message_datetime

    if messag_age > max_age:
        raise EventTooOldError(
            f"The event timestamp is too old: {message['timestamp']}"
        )

    if event["$schemaRef"] == JOURNAL_V1_SCHEMA and message.get("event") == "FSDJump":
        handle_journal_v1_fsdjump(message)
        handled = True

    elif event["$schemaRef"] == JOURNAL_V1_SCHEMA and message.get("event") == "Docked":
        handle_journal_v1_docked(message)
        handled = True

    elif event["$schemaRef"] == COMMODITY_V3_SCHEMA:
        handle_commodity_v3(message)
        handled = True

    else:
        logger.debug(
            "Ignored schema or event type",
            schema=event["$schemaRef"],
            msg_event=event["message"].get("event"),
        )

    return handled


def run():

    logger.info("Setup Database")
    init_db()

    RMQ_EXCHANGE_NAME = "eddn_raw"
    RMQ_QUEUE_NAME = "eddn_raw_queue"

    rmq_connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv("RMQ_HOST", "localhost"),
            credentials=pika.PlainCredentials(
                username=os.getenv("RMQ_USER", "guest"),
                password=os.getenv("RMQ_PASSWD", "guest"),
            ),
        )
    )

    logger.info("Connecting to RMQ exchange", exchange=RMQ_EXCHANGE_NAME)
    rmq_channel = rmq_connection.channel()
    rmq_channel.exchange_declare(exchange=RMQ_EXCHANGE_NAME, exchange_type="fanout")

    logger.info(
        "Binding to RMQ queue", exchange=RMQ_EXCHANGE_NAME, queue=RMQ_QUEUE_NAME
    )
    rmq_channel.queue_declare(queue=RMQ_QUEUE_NAME, durable=True)
    rmq_channel.queue_bind(exchange=RMQ_EXCHANGE_NAME, queue=RMQ_QUEUE_NAME)

    def callback(ch, method, properties, body):
        try:
            event_json = zlib.decompress(body)
            event = orjson.loads(event_json)

            logger.debug("Handling EDDN event", event_=event)
            handle_eddn_event(event, max_age=dt.timedelta(days=7))

            logger.debug("Acknowledging event")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except OperationalError as e:
            if e.orig and e.orig.args[0] == 1020:
                # OperationalError(1020, "Record has changed since last read in
                # table 'systems'") may occur when processing the same event
                # concurrently in two handler instances.
                # Do not aknowledge and requeue for re-processing
                logger.warning(
                    "DB Operational error, requeuing message for reprocessing"
                )
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            else:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.exception(e)

        except EventTooOldError as e:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Message handling skipped", reason=e)

        except ValidationError as e:
            if e.error_count() == 1 and e.errors()[0]["loc"] in (
                ("StationType",),
                ("StationName",),
            ):
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info("Colonization construction ship/site ignored")
            else:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.warning(e, errors=e.errors(), event_json=event_json.decode())

        except Exception as e:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.exception(
                f"An error occured while processing event: {e}",
                event_json=event_json.decode(),
            )

    rmq_channel.basic_qos(prefetch_count=int(os.getenv("RMQ_HANDLER_PREFETCH", 1)))
    rmq_channel.basic_consume(queue=RMQ_QUEUE_NAME, on_message_callback=callback)

    try:
        logger.info("Starting consumption of messages from queue", queue=RMQ_QUEUE_NAME)
        rmq_channel.start_consuming()

    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt received")
        logger.info("Stopping consumption of messages from queue", queue=RMQ_QUEUE_NAME)
        rmq_channel.stop_consuming()

    except Exception as e:
        logger.exception(e)

    finally:
        try:
            logger.info("Closing connection to RMQ")
            rmq_connection.close()
        except Exception:
            pass

        logger.info("Exiting application")
        sys.exit()


if __name__ == "__main__":
    run()
