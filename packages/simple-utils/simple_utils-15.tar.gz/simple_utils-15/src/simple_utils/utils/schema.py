# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

"""스키마 모듈.

이 모듈은 파케이 파일의 스키마를 읽고, Arrow 타입을 변환하는 기능을 제공합니다.
"""
from typing import Any, Dict, List

import pyarrow.parquet as pq
from pyarrow import fs


class TypeConverter:
    """타입 변환기 클래스.

    Arrow 타입을 Spark SQL 타입으로 변환하는 메서드를 제공합니다.
    """

    @staticmethod
    def from_arrow_type(at: Any) -> str:  # noqa: PLR0912
        """Arrow 타입을 변환합니다.

        Args:
            at (Any): Arrow 타입 객체

        Returns:
            str: 변환된 타입 문자열
        """
        from pyarrow import types

        if types.is_boolean(at):
            type_ = "boolean"
        elif types.is_int8(at):
            type_ = "tinyint"
        elif types.is_int16(at):
            type_ = "smallint"
        elif types.is_int32(at):
            type_ = "int"
        elif types.is_int64(at):
            type_ = "bigint"
        elif types.is_float32(at):
            type_ = "float"
        elif types.is_float64(at):
            type_ = "double"
        elif types.is_decimal(at):
            type_ = f"decimal({at.precision},{at.scale})"
        elif types.is_string(at):
            type_ = "string"
        elif types.is_binary(at):
            type_ = "binary"
        elif types.is_date32(at):
            type_ = "date"
        elif types.is_timestamp(at):
            type_ = "timestamp"
        elif types.is_list(at):
            type_ = "array"
        elif types.is_null(at):
            type_ = "string"
        elif types.is_map(at):
            type_ = f"map<{at.key_type},{at.item_type}>"
        else:
            raise TypeError("Unsupported type in conversion from Arrow: " + str(at))
        return type_


def read_parquet_columns(bucket_name: str, key: str) -> List[Dict[str, str]]:
    """파케이 파일의 컬럼을 읽습니다.

    주어진 S3 버킷과 키를 사용하여 파케이 파일의 스키마를 읽고,
    각 컬럼의 이름과 타입을 반환합니다.

    Args:
        bucket_name (str): S3 버킷 이름
        key (str): S3 키

    Returns:
        List[Dict[str, str]]: 컬럼 정보 리스트
    """
    schema = pq.ParquetDataset(
        f"{bucket_name}/{key}",
        filesystem=fs.S3FileSystem(region="ap-northeast-1"),
    ).schema

    columns = []
    if schema:
        for column in schema:
            columns.append(
                {
                    "name": column.name,
                    "type": TypeConverter.from_arrow_type(column.type),
                },
            )

    return columns
