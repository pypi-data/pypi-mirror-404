import typing as t

InstrumentRecord = t.TypedDict(
    'InstrumentRecord',
    {
        'name': str,
        'type': t.Literal['txt', 'cname'],
        'value': str,
    },
)
InstrumentInfo = t.TypedDict(
    'InstrumentInfo',
    {
        'errors': t.List[str],
        'messages': t.List[str],
        'ownership_status': t.Literal['active', 'pending', 'failed'],
        'ssl_status': t.Literal['active', 'pending', 'failed'],
        'records': t.List[InstrumentRecord],
    },
    total=False,
)
