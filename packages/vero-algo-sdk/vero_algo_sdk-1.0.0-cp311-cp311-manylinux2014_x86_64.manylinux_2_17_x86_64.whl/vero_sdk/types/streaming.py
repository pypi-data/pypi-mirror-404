from dataclasses import dataclass
from typing import Any

@dataclass
class SubscribeData:
    """Data for subscribing to a channel."""
    channel_name: str
    channel: str
    data_type: str
    data_id: str
    listener_guid: str


@dataclass
class StreamMessage:
    """Message received from stream."""
    channel: str
    data_type: str
    data_id: str
    data: Any
    seq: int = 0
    message_id: str = ""
