import time


def time_ago(tm):
    if isinstance(tm, str):
        return tm
    secs = int(time.time() - tm)
    mn, hr, day, week, month, year = (
        60,
        3600,
        86_400,
        604_800,
        2_592_000,
        31_104_000,
    )
    if secs < mn:
        v = secs // 1
        return f"{v} sec{'s' if v > 1 else ''} ago"
    if secs < hr:
        v = secs // mn
        return f"{v} min{'s' if v > 1 else ''} ago"
    if secs < day:
        v = secs // hr
        return f"{v} hr{'s' if v > 1 else ''} ago"
    if secs < week:
        v = secs // day
        return f"{v} day{'s' if v > 1 else ''} ago"
    if secs < month:
        v = secs // week
        return f"{v} wk{'s' if v > 1 else ''} ago"
    if secs < year:
        v = secs // month
        return f"{v} mon{'s' if v > 1 else ''} ago"
    v = secs // year
    return f"{v} yr{'s' if v > 1 else ''} ago"


def fmt_secs(tm):
    if isinstance(tm, str):
        return tm
    mins, secs = divmod(tm, 60)
    hrs, mins = divmod(mins, 60)
    if hrs > 23:
        return time_ago(tm)
    return f"{hrs:02,.0f}:{mins:02.0f}:{secs:02.0f}"
