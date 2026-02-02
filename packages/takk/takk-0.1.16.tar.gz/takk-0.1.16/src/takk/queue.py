from dataclasses import dataclass
from typing import Protocol, Any

from pydantic import BaseModel

from takk.secrets import SqsConfig, SqsQueueSettings


@dataclass
class QueueMessage:
    message: Any
    body: str


class NamedQueueBroker(Protocol):

    async def receive(self) -> list[QueueMessage]:
        ...

    async def send(self, message: str | dict | BaseModel) -> None:
        ...

    async def delete(self, message: QueueMessage) -> None:
        ...

class QueueBroker(Protocol):
    def with_name(self, name: str) -> NamedQueueBroker:
        ...



class SqsQueue:

    config: SqsQueueSettings

    def __init__(self, queue, config: SqsQueueSettings):
        self.queue = queue
        self.config = config

    async def receive(self) -> list[Any]:
        messages = self.queue.receive_messages(
            AttributeNames=['All'],
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=self.config.max_number_of_messages,
            WaitTimeSeconds=self.config.wait_time_seconds,
        )
        return [ 
            QueueMessage(
                message,
                message.body
            )
            for message in messages 
        ]

    async def send(self, message: str | dict | BaseModel) -> None:
        import json

        if isinstance(message, BaseModel):
            body = message.model_dump_json()
        elif isinstance(message, str):
            body = message
        else:
            body = json.dumps(message)

        self.queue.send_message(MessageBody=body)

    async def delete(self, message: QueueMessage) -> None:
        message.message.delete()

@dataclass
class SqsQueueBroker:

    config: SqsConfig
    queue_settings: SqsQueueSettings

    def with_name(self, name: str) -> NamedQueueBroker:
        import boto3

        sqs = boto3.resource(
            'sqs',
            endpoint_url=self.config.sqs_endpoint.encoded_string(),
            aws_access_key_id=self.config.sqs_access_key,
            aws_secret_access_key=self.config.sqs_secret_key.get_secret_value(),
            region_name=self.config.sqs_region_name,
        )

        try:
            return SqsQueue(
                sqs.get_queue_by_name(QueueName=name), # type: ignore
                config=self.queue_settings
            )
        except Exception:
            new_queue = sqs.create_queue( # type: ignore
                QueueName=name,
                Attributes=self.queue_settings.attributes()
            )

            if isinstance(new_queue, dict):
                if "QueueUrl" not in new_queue:
                    raise ValueError(f"Unable to find queue url in {new_queue}")

                return SqsQueue(
                    sqs.get_queue_by_name(QueueName=name), # type: ignore

                )

            return SqsQueue(
                new_queue, 
                config=self.queue_settings
            )



