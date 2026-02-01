from typing import Self

from .endpoint import SpecialEndpoint

_registry = set()


class NonInstrumentedUrls(list[str]):
    @classmethod
    def register(cls, *urls: *tuple[str, ...]) -> None:
        for url in urls:
            _registry.add(url)

    @classmethod
    def current(cls) -> Self:
        return cls(_registry)


NonInstrumentedUrls.register(*SpecialEndpoint)
