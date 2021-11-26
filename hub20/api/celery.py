import json
import uuid
import os

from decimal import Decimal

from celery import Celery
from celery.schedules import crontab
from hexbytes import HexBytes
from kombu.serialization import register
from web3.datastructures import AttributeDict


class Web3Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, AttributeDict):
            return {
                "__type__": "attrdict",
                "value": json.dumps({k: v for k, v in obj.items()}, cls=self.__class__),
            }
        elif isinstance(obj, HexBytes):
            return {"__type__": "hexbytes", "value": obj.hex()}
        elif isinstance(obj, uuid.UUID):
            return {"__type__": "uuid", "value": str(obj)}
        elif isinstance(obj, Decimal):
            return {"__type__": "decimal", "value": str(obj)}
        else:
            return json.JSONEncoder.default(self, obj)


def web3_decoder(obj):
    try:
        if obj["__type__"] == "attrdict":
            return AttributeDict(json.loads(obj["value"], object_hook=web3_decoder))
        elif obj["__type__"] == "hexbytes":
            return HexBytes(obj["value"])
        elif obj["__type__"] == "uuid":
            return uuid.UUID(obj["value"])
        elif obj["__type__"] == "decimal":
            return Decimal(obj["value"])
        else:
            return obj
    except KeyError:
        return obj


def web3_serializer(obj):
    return json.dumps(obj, cls=Web3Encoder)


def web3_deserializer(obj):
    return json.loads(obj, object_hook=web3_decoder)


register(
    "web3",
    web3_serializer,
    web3_deserializer,
    content_type="application/json",
    content_encoding="utf-8",
)


class Hub20CeleryConfig:
    name = "Hub20"

    broker_url = "memory" if "HUB20_TEST" in os.environ else os.getenv("HUB20_BROKER_URL")
    broker_use_ssl = "HUB20_BROKER_USE_SSL" in os.environ
    beat_schedule = {
        "clear-expired-sessions": {
            "task": "hub20.apps.core.tasks.clear_expired_sessions",
            "schedule": crontab(minute="*/30"),
        },
        "execute-transfers": {
            "task": "hub20.apps.core.tasks.execute_pending_transfers",
            "schedule": crontab(),
        },
    }
    task_always_eager = "HUB20_TEST" in os.environ
    task_eager_propagates = "HUB20_TEST" in os.environ
    task_serializer = "web3"
    accept_content = ["web3", "json"]


app = Celery()
app.config_from_object(Hub20CeleryConfig)
app.autodiscover_tasks()
