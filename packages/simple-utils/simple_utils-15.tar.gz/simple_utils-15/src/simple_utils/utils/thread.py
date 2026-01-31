# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py:light
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

"""스레드 모듈."""
import concurrent.futures
from typing import Any, Callable, Dict, List


class ThreadPool:
    """스레드 풀 클래스."""

    def __init__(self, max_workers: int) -> None:
        """ThreadPool 초기화 메서드.

        Args:
            max_workers (int): 최대 작업자 수
        """
        self.max_workers = max_workers

    def execute(self, *, func: Callable[..., Any], items: List[Dict[str, Any]]) -> List[Any]:
        """주어진 함수와 항목 리스트를 사용하여 스레드 풀에서 작업을 실행합니다.

        Args:
            func (Callable[..., Any]): 실행할 함수
            items (List[Dict[str, Any]]): 함수에 전달할 인자들의 리스트

        Returns:
            List[Any]: 함수 실행 결과 리스트
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            result = list(executor.map(lambda kwargs: func(**kwargs), items))

        return result
