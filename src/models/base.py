# External import
from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime
from typing import Any

class dbModel(BaseModel):
    user: str
    password: str
    host: str
    port: int
    service_name: str

    @model_validator(mode="before")
    def verificar_variables_entorno(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        variables = {
            "user": "ORAPY_PARAM1",
            "password": "ORAPY_PARAM2",
            "host": "ORAPY_PARAM3",
            "port": "ORAPY_PARAM4",
            "service_name": "ORAPY_PARAM5",
        }

        faltantes = []

        for field, env_name in variables.items():
            value = values.get(field)

            if value is None:
                faltantes.append(env_name)
            elif isinstance(value, str) and not value.strip():
                faltantes.append(env_name)

        if faltantes:
            raise ValueError(
                "Variables de entorno ausentes o vacías: "
                + ", ".join(faltantes)
            )

        return values