from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp


def to_google_timestamp(dt: datetime) -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts
