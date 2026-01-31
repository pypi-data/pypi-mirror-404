# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

"""로그 모듈."""
import datetime
import logging
from typing import Any

import jsonschema
import pendulum
import structlog

from simple_utils.utils.notebook import is_notebook


class Logger:
    """로거 클래스."""

    def __init__(self, client: str = None, sign: str = "STL1"):
        """로거 초기화 메서드.

        Args:
            client (str, optional): 클라이언트 이름. 기본값은 None.
            sign (str, optional): 로그 식별자. 기본값은 "STL1".
        """
        self.logging_log_level = logging.INFO
        self.client = client
        self.sign = sign
        self._is_interface = bool(is_notebook())
        self._logger = self._init_logger()
        self._schemas = {}

        self.set_level("INFO")

    def _init_logger(self) -> Any:
        structlog.reset_defaults()

        shared_processors = [
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
        ]

        processors = shared_processors

        if self._is_interface:
            processors += [structlog.dev.ConsoleRenderer()]
        else:
            processors += [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(ensure_ascii=False),
            ]

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        )

        log = structlog.get_logger()
        if self.client:
            log = log.bind(client=self.client)

        if not self._is_interface:
            log = log.bind(sign=self.sign)

        return log

    def _get_event(self, *args: list) -> str:
        """이벤트 문자열 생성 메서드.

        Args:
            *args (list): 이벤트를 구성하는 문자열 리스트.

        Returns:
            str: 생성된 이벤트 문자열.
        """
        return " ".join([str(s) for s in args])

    def set_client(self, client: str) -> None:
        """클라이언트 설정 메서드.

        Args:
            client (str): 클라이언트 이름.
        """
        self.client = client

        self._logger = self._logger.bind(client=self.client)

    def _validate(self, kind: str, data: dict) -> None:
        """로그 데이터 검증 메서드.

        Args:
            kind (str): 로그 종류.
            data (dict): 로그 데이터.

        Raises:
            ValueError: 검증 실패 시 예외 발생.
        """
        if (kind or data) and (not kind or not data):
            raise ValueError("kind와 data는 함께 사용해야 합니다.")

        if (kind or data) and not self.client:
            raise ValueError(
                """kind, data를 입력하기 위해서는 client를 설정해야 합니다.
                1. 클라이언트가 존재하는지 확인합니다.
                    - logger.is_client_exist(<client_name>)
                2. 클라이언트를 둘 중 하나의 방식으로 설정합니다.
                    - logger.set_client(<client_name>)
                    - logger = Logger(client=<client_name>)
                """
            )

        if kind and not isinstance(kind, str):
            raise ValueError("kind는 str 타입이어야 합니다.")

        if data and not isinstance(data, dict):
            raise ValueError("data는 dict 타입이어야 합니다.")

        if kind in self._schemas:
            jsonschema.validate(data, self._schemas[kind])

    def log(self, log_level: str, kind: str, data: dict, *args: list) -> None:
        """로그 기록 메서드.

        Args:
            log_level (str): 로그 레벨.
            kind (str): 로그 종류.
            data (dict): 로그 데이터.
            *args (list): 추가 로그 메시지.
        """
        data = data if data else {}

        self._validate(kind, data)

        event = self._get_event(*args)
        logging_log_level = self._get_logging_log_level(log_level)
        parameters = {
            "event": event,
            "level": logging_log_level,
        }

        if kind:
            parameters["kind"] = kind

        if data:
            parameters["data"] = data

        if logging_log_level >= self.logging_log_level:
            if self._is_interface or (kind and data):
                self._logger.log(**parameters)
            else:
                print(self._format_message(log_level=log_level, message=event))

    def _format_message(self, log_level: str, message: str) -> str:
        """로그 메시지 포맷팅 메서드.

        Args:
            log_level (str): 로그 레벨.
            message (str): 로그 메시지.

        Returns:
            str: 포맷팅된 로그 메시지.
        """
        now = datetime.datetime.now(pendulum.timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
        frag = message.split("\n")
        logs = [f"[{log_level}][{now} KST] {f}" for f in frag]
        return "\n".join(logs)

    def debug(self, *args, kind: str = None, data: dict = None) -> None:
        """DEBUG 레벨 로그 기록 메서드.

        Args:
            *args (list): 추가 로그 메시지.
            kind (str, optional): 로그 종류. 기본값은 None.
            data (dict, optional): 로그 데이터. 기본값은 None.
        """
        self.log("DEBUG", kind, data, *args)

    def info(self, *args, kind: str = None, data: dict = None) -> None:
        """INFO 레벨 로그 기록 메서드.

        Args:
            *args (list): 추가 로그 메시지.
            kind (str, optional): 로그 종류. 기본값은 None.
            data (dict, optional): 로그 데이터. 기본값은 None.
        """
        self.log("INFO", kind, data, *args)

    def warning(self, *args, kind: str = None, data: dict = None) -> None:
        """WARNING 레벨 로그 기록 메서드.

        Args:
            *args (list): 추가 로그 메시지.
            kind (str, optional): 로그 종류. 기본값은 None.
            data (dict, optional): 로그 데이터. 기본값은 None.
        """
        self.log("WARNING", kind, data, *args)

    def error(self, *args, kind: str = None, data: dict = None) -> None:
        """ERROR 레벨 로그 기록 메서드.

        Args:
            *args (list): 추가 로그 메시지.
            kind (str, optional): 로그 종류. 기본값은 None.
            data (dict, optional): 로그 데이터. 기본값은 None.
        """
        self.log("ERROR", kind, data, *args)

    def critical(self, *args, kind: str = None, data: dict = None) -> None:
        """CRITICAL 레벨 로그 기록 메서드.

        Args:
            *args (list): 추가 로그 메시지.
            kind (str, optional): 로그 종류. 기본값은 None.
            data (dict, optional): 로그 데이터. 기본값은 None.
        """
        self.log("CRITICAL", kind, data, *args)

    def _get_logging_log_level(self, log_level: str) -> int:
        """로그 레벨 변환 메서드.

        Args:
            log_level (str): 로그 레벨 문자열.

        Returns:
            int: 변환된 로그 레벨.
        """
        return {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }[log_level]

    def set_level(self, log_level: str) -> None:
        """로그 레벨 설정 메서드.

        Args:
            log_level (str): 설정할 로그 레벨. "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" 중 하나.
        """
        self.logging_log_level = self._get_logging_log_level(log_level)
        structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(self.logging_log_level))

    def set_schema(self, kind: str, schema: dict) -> None:
        """로그 스키마 설정 메서드.

        Args:
            kind (str): 로그 종류.
            schema (dict): jsonschema 스키마.

        Examples:
            >>> logger.set_schema(kind="sample", schema={
                "required": ["latitude"],
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "minimum": -90,
                        "maximum": 90
                    },
                    "longitude": {
                        "type": "number",
                        "minimum": -180,
                        "maximum": 180
                    }
                }
            })
            >>> logger.info(kind="sample", data={"latitude": 30, "longitude": 30})
            2023-09-19T10:46:11.787029Z [info] data={'latitude': 30, 'longitude': 30} kind=sample
            >>> logger.info(kind="sample", data={"longitude": 30})
            ValidationError: 'latitude' is a required property
        """
        self._schemas[kind] = schema


logger = Logger()
