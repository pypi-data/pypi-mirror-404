from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Self

from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import PydanticBaseSettingsSource

from . import utils
from .enums import AppEnv

if TYPE_CHECKING:
    import mypy_boto3_ssm


type SettingPreprocessor = Callable[[str], str]
type SettingPreprocessors = dict[str, SettingPreprocessor]


class ParameterStoreParameterPrefix(str):
    @classmethod
    def create(cls, service_name: str, app_env: AppEnv) -> Self:
        return cls(f"/{service_name}/{app_env.lower()}/")


def get_parameters_from_ssm(
    ssm_client: mypy_boto3_ssm.SSMClient,
    prefix: str,
    preprocessors: SettingPreprocessors | None = None,
) -> dict[str, Any]:
    preprocessors = preprocessors or {}

    result = {}
    has_next = True
    next_token = None
    while has_next:
        params = {
            "Path": prefix,
            "WithDecryption": True,
            "Recursive": True,
        }
        if next_token is not None:
            params["NextToken"] = next_token

        response = ssm_client.get_parameters_by_path(**params)
        for parameter in response["Parameters"]:
            key = parameter["Name"].split("/")[-1].lower()
            value = parameter["Value"]
            result[key] = preprocessors.get(key, utils.ident)(value)

        next_token = response.get("NextToken")
        has_next = next_token is not None
    return result


class AWSParameterStoreSettingsSource(PydanticBaseSettingsSource):
    def __init__(
        self,
        settings_cls: type[PydanticBaseSettings],
        ssm_client: mypy_boto3_ssm.SSMClient,
        prefix: str,
        preprocessors: dict[str, Callable[[str], str]] = None,
    ):
        super().__init__(settings_cls=settings_cls)

        self.ssm_client = ssm_client
        self.prefix = prefix
        self.preprocessors = preprocessors or {}

        self._parameters = get_parameters_from_ssm(
            ssm_client=self.ssm_client,
            prefix=self.prefix,
            preprocessors=self.preprocessors,
        )

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        return self._parameters.get(field_name), field_name, False

    def __call__(self) -> dict[str, Any]:
        result = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, is_value_complex = self.get_field_value(
                field=field, field_name=field_name
            )
            field_value = self.prepare_field_value(
                field_name=field_name,
                field=field,
                value=field_value,
                value_is_complex=is_value_complex,
            )
            if field_value is None:
                continue

            result[field_name] = field_value

        return result

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(prefix={self.prefix})"


def create_base_settings(
    ssm_client: mypy_boto3_ssm.SSMClient,
    prefix: str,
    preprocessors: SettingPreprocessors | None = None,
) -> type[PydanticBaseSettings]:
    class BaseSettings(PydanticBaseSettings):
        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return (
                init_settings,
                AWSParameterStoreSettingsSource(
                    settings_cls=settings_cls,
                    ssm_client=ssm_client,
                    prefix=prefix,
                    preprocessors=preprocessors,
                ),
                env_settings,
                file_secret_settings,
            )

    return BaseSettings
