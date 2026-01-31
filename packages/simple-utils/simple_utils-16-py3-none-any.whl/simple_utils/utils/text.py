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

"""텍스트 모듈."""
import random


def get_random_string(length: int = 10) -> str:
    """주어진 길이의 랜덤 문자열을 생성합니다.

    Args:
        length (int, optional): 생성할 문자열의 길이. 기본값은 10.

    Returns:
        str: 생성된 랜덤 문자열
    """
    random_box = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    random_box_length = len(random_box)
    result = ""
    for _ in range(length):
        result += random_box[int(random.random() * random_box_length)]

    return result
