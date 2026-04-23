import asyncio
import base64

from fake_useragent import UserAgent
from httpx import AsyncClient, HTTPStatusError

from src.shinban_sync.core.logger import logger
from src.shinban_sync.models.config import Aria2Config


class Aria2Downloader:
    def __init__(self, config: Aria2Config):
        self._config = config
        self._client = AsyncClient(headers = {"User-Agent": UserAgent().random}, timeout = 10.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()

    async def _rpc_call(self, method: str, params: list, task_id: str = "bot"):
        token_str = self._config.token
        if not token_str.startswith("token:"):
            token_str = f"token:{token_str}"

        payload = {
            "jsonrpc": "2.0",
            "id": task_id,
            "method": method,
            "params": [token_str] + params
        }

        response = await self._client.post(self._config.base_url, json = payload)

        try:
            response.raise_for_status()
        except HTTPStatusError:
            logger.error(f"Aria2 HTTP Error: {response.status_code} - {response.text}")
            return None

        json_resp = response.json()
        if "error" in json_resp:
            logger.error(f"Aria2 RPC Error: {json_resp['error']}")
            return None

        return json_resp

    async def add_torrent(self, torrent_url: str, task_name: str) -> str:
        """
        :param torrent_url: 种子链接
        :param task_name: 任务名称
        :return: Aria2 任务 Gid
        """
        torrent_raw = await self._client.get(torrent_url)
        torrent_raw.raise_for_status()
        torrent_b64 = base64.b64encode(torrent_raw.content).decode('utf-8')

        resp = await self._rpc_call("aria2.addTorrent", [torrent_b64, [], {}], task_name)
        return resp["result"] if resp else ""

    async def wait_for_completion(self, gid: str) -> str | None:
        while True:
            resp = await self._rpc_call("aria2.tellStatus", [gid, ["status", "dir", "bittorrent"]])
            if resp:
                status = resp["result"]
                if status["status"] == "complete":
                    name = status.get("bittorrent", {}).get("info", {}).get("name", "")
                    return name
                elif status["status"] in ["error", "removed"]:
                    return None

            await asyncio.sleep(60)  # 一分钟间隔够了，种子一般下的也不快
