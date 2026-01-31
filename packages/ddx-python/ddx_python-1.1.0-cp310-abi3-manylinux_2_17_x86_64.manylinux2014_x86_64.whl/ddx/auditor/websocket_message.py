"""
WebsocketMessage module
"""

from enum import Enum
from typing import Dict, Union

from attrs import define


class WebsocketMessageType(str, Enum):
    GET = "Get"
    SUBSCRIBE = "Subscribe"
    REQUEST = "Request"
    INFO = "Info"
    SEQUENCED = "Sequenced"
    SAFETY_FAILURE = "SafetyFailure"


class WebsocketEventType(str, Enum):
    PARTIAL = "Partial"
    UPDATE = "Update"
    SNAPSHOT = "Snapshot"
    HEAD = "Head"
    TAIL = "Tail"


@define
class WebsocketMessage:
    """
    Defines a WebsocketMessage.
    """

    message_type: Union[WebsocketMessageType, str]
    message_content: str

    @classmethod
    def decode_value_into_cls(cls, raw_websocket_message: Dict):
        """
        Decode a raw websocket message into class

        Parameters
        ----------
        raw_websocket_message : Dict
            Raw websocket message
        """

        return cls(
            raw_websocket_message["t"],
            raw_websocket_message["c"],
        )

    def repr_json(self):
        return {"t": self.message_type, "c": self.message_content}
