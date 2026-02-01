from . import api_pb2


class Mcp:
    def __init__(self, proto: api_pb2.McpInfo):
        self._proto = proto

    @property
    def status(self) -> str:
        return api_pb2.McpStatus.Name(self._proto.status)

    def __getattr__(self, name):
        return getattr(self._proto, name)
