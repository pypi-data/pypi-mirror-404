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

"""노트북 모듈.

이 모듈은 현재 실행 환경이 Jupyter 노트북인지 확인하는 기능을 제공합니다.
"""

def is_notebook() -> bool:
    """현재 실행 환경이 Jupyter 계열 노트북(ipynb)인지 판별해주는 함수"""
    try:
        from IPython import get_ipython
        ip = get_ipython()
        if not ip:
            return False

        # ZMQInteractiveShell 계열 잡기
        cls_name = ip.__class__.__name__
        return cls_name == "ZMQInteractiveShell"
    except Exception:
        return False
