import unittest
from unittest.mock import MagicMock, AsyncMock
from typing import cast

from sec_gemini import SecGemini, Session
from sec_gemini import constants
from sec_gemini import api_pb2


class TestSecGeminiClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = SecGemini(api_key="test-key")
        self.client.rpc = MagicMock()
        self.client.rpc.start = AsyncMock()
        self.client.rpc.close = AsyncMock()
        self.client.rpc.send_request = AsyncMock()

    async def test_start_registers_client(self):
        # Mock response for register
        response = api_pb2.ServerMessage()
        response.register_response.success = True
        cast(AsyncMock, self.client.rpc.send_request).return_value = response

        await self.client.start()

        cast(AsyncMock, self.client.rpc.start).assert_called_once()
        cast(AsyncMock, self.client.rpc.send_request).assert_called_with(
            constants.MSG_REGISTER,
            api_pb2.RegisterRequest(api_key="test-key"),
            wait_for_response=True,
        )

    async def test_create_session(self):
        # Mock response for create session
        response = api_pb2.ServerMessage()
        response.create_session_response.success = True
        response.create_session_response.session_id = "sess-123"
        cast(AsyncMock, self.client.rpc.send_request).return_value = response

        session = await self.client.create_session()

        self.assertIsInstance(session, Session)
        self.assertEqual(session.id, "sess-123")
        self.assertIn("sess-123", self.client._sessions)

    async def test_create_session_fail(self):
        response = api_pb2.ServerMessage()
        response.create_session_response.success = False
        cast(AsyncMock, self.client.rpc.send_request).return_value = response

        with self.assertRaisesRegex(RuntimeError, "Failed to create session"):
            await self.client.create_session()

    async def test_list_sessions(self):
        response = api_pb2.ServerMessage()
        s1 = response.list_sessions_response.sessions.add()
        s1.session_id = "s1"
        s1.status = api_pb2.JobStatus.PENDING

        cast(AsyncMock, self.client.rpc.send_request).return_value = response

        sessions = await self.client.sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].id, "s1")
        self.assertEqual(sessions[0].status, "PENDING")


if __name__ == "__main__":
    unittest.main()
