from aio_pika import ExchangeType, connect_robust

from architectonics.rabbit_mq.config.rabbit_mq_settings import BaseRabbitMQSettings


class BaseRabbitMQConsumer:
    _settings = BaseRabbitMQSettings()

    _exchange_name: str = NotImplemented
    _exchange_type: ExchangeType = NotImplemented
    _queue_name: str = NotImplemented
    _routing_key: str = NotImplemented

    _prefetch_count: int = 1

    async def connect(self):
        self.connection = await connect_robust(
            host=self._settings.RABBITMQ_HOST,
            port=self._settings.RABBITMQ_PORT,
            login=self._settings.RABBITMQ_USER,
            password=self._settings.RABBITMQ_PASSWORD,
            virtualhost=self._settings.RABBITMQ_VHOST,
        )

        self.channel = await self.connection.channel()
        await self.channel.set_qos(
            prefetch_count=self._prefetch_count,
        )

        self.exchange = await self.channel.declare_exchange(
            name=self._exchange_name,
            type=self._exchange_type,
            durable=True,
        )

        self.queue = await self.channel.declare_queue(
            name=self._queue_name,
            durable=True,
        )

        await self.queue.bind(
            exchange=self.exchange,
            routing_key=self._routing_key,
        )

    async def consume(self):
        async with self.connection:
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        await self.process_message(message.body)

    async def process_message(self, message: bytes) -> None:

        return NotImplemented
