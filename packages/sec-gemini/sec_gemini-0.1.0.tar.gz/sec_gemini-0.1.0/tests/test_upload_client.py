import unittest
from unittest.mock import MagicMock, AsyncMock
from typing import cast, Any
import os
import sys

# Ensure we can import sec_gemini
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sec_gemini import SecGemini, Session
from sec_gemini import api_pb2


class TestUploadClient(unittest.IsolatedAsyncioTestCase):
    async def test_upload_file(self):
        client = SecGemini("fake-key")
        client.rpc.stub = MagicMock()
        client.rpc.stub.UploadFile = cast(Any, AsyncMock())  # type: ignore

        response = api_pb2.UploadFileResponse(success=True)
        cast(Any, client.rpc.stub).UploadFile.return_value = response

        session = Session("session1")
        session.bind(client)

        # Create dummy file
        filename = "temp_test_file.txt"
        with open(filename, "w") as f:
            f.write("test content")

        try:
            await session.upload_file(filename)

            # Verify call
            cast(Any, client.rpc.stub).UploadFile.assert_called_once()

        finally:
            if os.path.exists(filename):
                os.remove(filename)

    async def test_delete_file(self):
        client = SecGemini("fake-key")
        client.rpc = MagicMock()
        client.rpc.send_request = AsyncMock()

        # Mock response
        response = api_pb2.ServerMessage(
            delete_file_response=api_pb2.DeleteFileResponse(success=True)
        )
        cast(AsyncMock, client.rpc.send_request).return_value = response

        session = Session("session1")
        session.bind(client)

        result = await session.delete_file("test.txt")
        self.assertTrue(result)

        # Verify call
        cast(AsyncMock, client.rpc.send_request).assert_called_once()
        _, kwargs = cast(AsyncMock, client.rpc.send_request).call_args
        self.assertEqual(kwargs["session_id"], "session1")


if __name__ == "__main__":
    unittest.main()
