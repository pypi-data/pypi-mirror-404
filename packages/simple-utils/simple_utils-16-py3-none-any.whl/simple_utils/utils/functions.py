"""함수 모듈."""
import types
from typing import Any, Callable, List, Optional, Tuple, Union

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_timedelta64_dtype
import subprocess

def list_chunks(target: List[Any], n: int) -> List[List[Any]]:
    """리스트를 청크로 나누는 함수.

    Args:
        target (List[Any]): 나눌 리스트.
        n (int): 청크 크기.

    Returns:
        List[List[Any]]: 나눠진 리스트 청크들.
    """
    return [target[i : i + n] for i in range(0, len(target), n)]


def walk_iterator(source: Union[dict, list], callback: Callable) -> Union[dict, list]:
    """리스트나 딕셔너리를 순회하며 마지막 값이 발견되었을 때 콜백 함수를 실행하는 함수.

    Args:
        source (Union[dict, list]): 순회할 소스.
        callback (Callable): 마지막 값에서 실행할 콜백 함수.

    Returns:
        Union[dict, list]: 적용된 결과값.

    Examples:
        def callback(parent: Optional[Union[dict, list]], key: Any, value: Any):
            if isinstance(value, str):
                parent[key] = value + "_ok"

        result = walk_iterator(source, callback=callback)
    """

    def walk(
        value: Any,
        parent: Optional[Union[dict, list]] = None,
        key: Any = None,
    ) -> Any:
        if isinstance(value, dict):
            for dict_key, dict_value in value.items():
                walk(dict_value, parent=value, key=dict_key)

        elif isinstance(value, list):
            for list_index, list_value in enumerate(value):
                walk(list_value, parent=value, key=list_index)

        elif parent is not None:
            callback(parent, key, value)

        return value

    return walk(source.copy())


def import_code(code: str, name: str) -> types.ModuleType:
    """문자열로 된 코드를 모듈로 임포트하는 함수.

    Args:
        code (str): 임포트할 코드 문자열.
        name (str): 모듈 이름.

    Returns:
        types.ModuleType: 임포트된 모듈.

    Examples:
        code = '''
        exports = {"hello":"world"}
        '''

        m = import_code(code, 'test')
        print(m.exports["hello"])
    """
    module = types.ModuleType(name)
    exec(code, module.__dict__)
    return module


def is_datetime_or_timedelta_dtype(data: pd.core.series.Series) -> bool:
    """데이터가 datetime 또는 timedelta 타입인지 확인하는 함수.

    Args:
        data (pd.core.series.Series): 확인할 데이터 시리즈.

    Returns:
        bool: 데이터가 datetime 또는 timedelta 타입이면 True, 그렇지 않으면 False.
    """
    return is_datetime64_any_dtype(data) or is_timedelta64_dtype(data)



def run_command(command: str, raise_on_error: bool = True) -> Tuple[str, int]:
    try:
        out = subprocess.check_output(
            command,
            shell=True,
            stderr=subprocess.STDOUT,
            text=True
        )
        return out, 0
    except subprocess.CalledProcessError as e:
        if not raise_on_error:
            return e.output, e.returncode
        else:
            raise RuntimeError(f"Command '{command}' failed with exit code {e.returncode}: {e.output}") from e
