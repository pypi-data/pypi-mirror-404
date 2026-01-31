import enum
import http

from fastapi import FastAPI, Response


class SpecialEndpoint(enum.StrEnum):
    HEALTH_CHECK = "/health-check"
    METRICS = "/metrics"


def health_check() -> Response:
    return Response(status_code=http.HTTPStatus.OK)


def add_health_check_endpoint(app: FastAPI) -> None:
    app.get(SpecialEndpoint.HEALTH_CHECK, include_in_schema=False)(health_check)
