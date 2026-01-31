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

"""시간 모듈."""
import datetime
from typing import List, Optional, Union

from dateutil.relativedelta import relativedelta
from pytz import timezone, utc

from simple_utils.utils.structure import dotdict


def get_kst_now(time_format: str = "%Y%m%d%H%M%S") -> Union[str, datetime.datetime]:
    """한국 기준 시간 객체(datetime 또는 str)를 가져옵니다.

    Args:
        time_format (str): datetime 형식 또는 'datetime' 또는 'date'

    Returns:
        Union[str, datetime.datetime]: datetime 형식 -> 날짜 문자열
                                       'datetime' 또는 'date' -> datetime 객체
    """
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    kst_now = utc_now.astimezone(timezone("Asia/Seoul"))
    if time_format.lower() in ["date", "datetime"]:
        return datetime.datetime.strptime(kst_now.strftime("%Y%m%d%H%M%S"), "%Y%m%d%H%M%S")
    return kst_now.strftime(time_format)


def get_kst() -> datetime.datetime:
    """한국 표준시(KST)를 가져옵니다.

    Returns:
        datetime.datetime: 한국 표준시 datetime 객체
    """
    return datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9)))


def get_kst_ymd() -> str:
    """한국 표준시(KST) 날짜를 '년-월-일' 형식으로 가져옵니다.

    Returns:
        str: '년-월-일' 형식의 날짜 문자열
    """
    return get_kst().strftime("%Y-%m-%d")


def get_month_dt_list(
    start_dt: datetime.datetime,
    last_dt: Optional[datetime.datetime] = None,
    _format: Optional[str] = None,
) -> List[Union[str, datetime.datetime]]:
    """시작 날짜부터 마지막 날짜까지의 월 단위 날짜 리스트를 가져옵니다.

    Args:
        start_dt (datetime.datetime): 시작 날짜
        last_dt (Optional[datetime.datetime], optional): 마지막 날짜. 기본값은 현재 날짜.
        _format (Optional[str], optional): 날짜 형식. 기본값은 None.

    Returns:
        List[Union[str, datetime.datetime]]: 월 단위 날짜 리스트
    """
    dt = datetime.datetime(start_dt.year, start_dt.month, 1)
    if not last_dt:
        now = datetime.datetime.now()
        last_dt = datetime.datetime(now.year, now.month, 1)
    else:
        last_dt = datetime.datetime(last_dt.year, last_dt.month, 1)

    dt_list = []
    while dt <= last_dt:
        dt_list.append(dt)
        dt += relativedelta(months=1)

    if _format:
        return [dt.strftime(_format) for dt in dt_list]

    return dt_list


def get_seconds_by_unit(str_time: str) -> int:
    """시간 단위 문자열을 초 단위로 변환합니다.

    Args:
        str_time (str): 시간 단위 문자열 (예: '1h', '30m', '45s')

    Returns:
        int: 초 단위 시간

    Raises:
        ValueError: 유효하지 않은 단위가 입력된 경우
    """
    unit = str_time[-1]
    num = int(str_time[:-1])
    seconds = -1
    if unit == "h":
        seconds = num * 60 * 60
    elif unit == "m":
        seconds = num * 60
    elif unit == "s":
        seconds = num
    else:
        raise ValueError(f"invalid unit {unit}")

    return seconds


def get_relevant_times(dt: datetime.datetime, interval: relativedelta) -> dotdict:
    """주어진 날짜와 간격을 기준으로 관련된 날짜들을 가져옵니다.

    Args:
        dt (datetime.datetime): 기준 날짜
        interval (relativedelta): 간격

    Returns:
        dotdict: 관련된 날짜들을 포함한 dotdict 객체
    """
    times = dotdict({})

    times.dt = dt
    times.ds = times.dt.strftime("%Y-%m-%d")
    times.ds_nodash = times.dt.strftime("%Y%m%d")

    times.prev_dt = times.dt - interval
    times.prev_ds = times.prev_dt.strftime("%Y-%m-%d")
    times.prev_ds_nodash = times.prev_dt.strftime("%Y%m%d")

    times.next_dt = times.dt + interval
    times.next_ds = times.next_dt.strftime("%Y-%m-%d")
    times.next_ds_nodash = times.next_dt.strftime("%Y%m%d")

    times.tomorrow_dt = times.dt + relativedelta(days=1)
    times.tomorrow_ds = times.tomorrow_dt.strftime("%Y-%m-%d")
    times.tomorrow_ds_nodash = times.tomorrow_dt.strftime("%Y%m%d")

    times.yesterday_dt = times.dt - relativedelta(days=1)
    times.yesterday_ds = times.yesterday_dt.strftime("%Y-%m-%d")
    times.yesterday_ds_nodash = times.yesterday_dt.strftime("%Y%m%d")

    times.next_yesterday_dt = times.next_dt - relativedelta(days=1)
    times.next_yesterday_ds = times.next_yesterday_dt.strftime("%Y-%m-%d")
    times.next_yesterday_ds_nodash = times.next_yesterday_dt.strftime("%Y%m%d")

    return times
