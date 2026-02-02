import pytest


class TestParityAPIs:
    @pytest.mark.asyncio
    async def test_drivers_call_non_stream(self, client, mock_client_session, mock_response):
        mock_client_session.request.return_value.__aenter__.return_value = mock_response
        mock_response.json.return_value = {"success": True, "result": {"ok": True}}

        result = await client.drivers_call("iface", "driver", "method", args={"a": 1})
        assert result["success"] is True

        call_args = mock_client_session.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1].endswith("/drivers/call")
        assert call_args[1]["json"]["interface"] == "iface"

    @pytest.mark.asyncio
    async def test_fs_ops(self, client, mock_client_session, mock_response):
        mock_client_session.request.return_value.__aenter__.return_value = mock_response
        mock_response.json.return_value = {"success": True, "result": {"path": "a"}}

        await client.fs_mkdir("~/tmp", options={"createMissingParents": True})
        await client.fs_readdir("~/tmp")
        await client.fs_rename("~/tmp/a.txt", "~/tmp/b.txt")
        await client.fs_copy("~/tmp/b.txt", "~/tmp/c.txt")
        await client.fs_move("~/tmp/c.txt", "~/tmp/d.txt")

        assert mock_client_session.request.call_count >= 5

    @pytest.mark.asyncio
    async def test_fs_stat_space_and_read_url(self, client, mock_client_session, mock_response):
        mock_client_session.request.return_value.__aenter__.return_value = mock_response
        mock_response.json.return_value = {"success": True, "url": "https://example.com/read"}

        url = await client.fs_get_read_url("~/tmp/a.txt")
        assert url.startswith("https://")

        mock_response.json.return_value = {"success": True, "result": {"type": "file"}}
        await client.fs_stat("~/tmp/a.txt")

        mock_response.json.return_value = {"success": True, "result": {"total": 1, "used": 1}}
        await client.fs_space()

    @pytest.mark.asyncio
    async def test_kv_advanced_ops(self, client, mock_client_session, mock_response):
        mock_client_session.request.return_value.__aenter__.return_value = mock_response
        mock_response.json.return_value = {"success": True, "value": {"a": 1}}

        assert await client.kv_add("k", 1) == {"a": 1}
        assert await client.kv_incr("k", 1) == {"a": 1}
        assert await client.kv_decr("k", 1) == {"a": 1}
        assert await client.kv_update("k", {"x": 1}) == {"a": 1}
        assert await client.kv_remove("k", "a.b") == {"a": 1}

        mock_response.json.return_value = {"success": True}
        await client.kv_expire("k", 10)
        await client.kv_expire_at("k", 123)
        await client.kv_flush("*")

    @pytest.mark.asyncio
    async def test_kv_list_variants(self, client, mock_client_session, mock_response):
        mock_client_session.request.return_value.__aenter__.return_value = mock_response
        mock_response.json.return_value = {"success": True, "keys": ["a", "b"]}
        keys = await client.kv_list()
        assert keys == ["a", "b"]

        mock_response.json.return_value = {"success": True, "items": [{"key": "a", "value": 1}]}
        pairs = await client.kv_list(return_values=True)
        assert isinstance(pairs, list)
        assert pairs[0]["key"] == "a"

        mock_response.json.return_value = {"success": True, "items": [{"key": "a"}], "cursor": "c"}
        page = await client.kv_list(limit=1)
        assert page["cursor"] == "c"

    @pytest.mark.asyncio
    async def test_ai_helpers(self, client, mock_client_session, mock_response):
        mock_client_session.request.return_value.__aenter__.return_value = mock_response
        mock_client_session.get.return_value.__aenter__.return_value = mock_response
        mock_response.json.return_value = {"success": True, "models": [{"id": "m", "provider": "p"}]}

        providers = await client.ai_list_model_providers(force_refresh=True)
        assert providers == ["p"]

        mock_response.json.return_value = {"success": True, "text": "ok"}
        text = await client.ai_speech2txt("https://example.com/a.mp3", options={"response_format": "text"})
        assert text == "ok"

        mock_response.json.return_value = {"success": True, "result": {"url": "https://example.com/v"}}
        result = await client.ai_txt2vid("hi")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_auth_helpers(self, client, mock_client_session, mock_response):
        mock_client_session.request.return_value.__aenter__.return_value = mock_response
        mock_response.json.return_value = {"success": True, "signedIn": True}
        assert await client.auth_is_signed_in() is True

        mock_response.json.return_value = {"success": True, "user": {"id": "1"}}
        user = await client.auth_get_user()
        assert "user" in user
