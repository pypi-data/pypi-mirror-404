from typing import Protocol

from .. import model


class MessageConsumerType(Protocol):
    async def run(self) -> None: ...

    async def consume(self, message: model.EventMessage) -> None: ...

    def shutdown(self) -> None: ...
