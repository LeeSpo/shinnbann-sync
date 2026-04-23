import re
from typing import Optional

import httpx

from src.shinban_sync.core.logger import logger
from src.shinban_sync.models.bangumi import BangumiInfo
from src.shinban_sync.models.config import BangumiConfig, OpenlistStorageConfig
from src.shinban_sync.storage.base import BaseProvider


class OpenlistProvider(BaseProvider):
    def __init__(self, storage: OpenlistStorageConfig) -> None:
        super().__init__(storage)
        self.storage: OpenlistStorageConfig = storage

        self.base_url = self.storage.base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json"
        }
        self.client: Optional[httpx.Client] = None

        self._login()

    def __enter__(self):
        self.client = httpx.Client(timeout = 15.0)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()

    def _login(self):
        url = f"{self.base_url}/api/auth/login"
        payload = {
            "username": self.storage.user,
            "password": self.storage.password
        }

        try:
            with httpx.Client(timeout = 15.0) as temp_client:
                resp = temp_client.post(url, json = payload)
                resp.raise_for_status()
                data = resp.json()

                if data.get("code") != 200:
                    raise ValueError(f"Login failed: {data.get('message')}")

                token = data.get("data", {}).get("token")
                if not token:
                    raise ValueError("Invalid token")

                self.headers["Authorization"] = token

        except httpx.RequestError as e:
            logger.error(f"Network request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unknown error: {e}")
            raise

    def _api_post(self, endpoint: str, json_data: dict, suppress_error: bool = False):
        url = f"{self.base_url}{endpoint}"
        try:
            data = {}
            if self.client:
                resp = self.client.post(url, headers = self.headers, json = json_data)
                resp.raise_for_status()
                data = resp.json()
            else:
                with httpx.Client(timeout = 15.0) as temp_client:
                    resp = temp_client.post(url, headers = self.headers, json = json_data)
                    resp.raise_for_status()
                    data = resp.json()

            if data.get("code") != 200:
                if not suppress_error:
                    logger.error(f"OpenList API error ({endpoint}): {data.get('message')}")
                return None

            result = data.get("data")
            return result if result is not None else True
        except Exception as e:
            if not suppress_error:
                logger.error(f"OpenList API request error {endpoint}: {e}")
            return None

    def _makedirs(self, path: str):
        folders = path.replace('\\', '/').strip('/').split('/')
        current_path = ""
        for folder in folders:
            if not folder:
                continue
            current_path += f"/{folder}"

            res = self._api_post("/api/fs/get", {"path": current_path}, suppress_error = True)
            if not res:
                self._api_post("/api/fs/mkdir", {"path": current_path}, suppress_error = True)

    def _rename(self, path: str, new_name: str) -> bool:
        res = self._api_post("/api/fs/rename", {"path": path, "name": new_name})
        if res is not None:
            return True
        return False

    def _move(self, src_dir: str, dst_dir: str, file_name: str) -> bool:
        res = self._api_post("/api/fs/move", {"src_dir": src_dir, "dst_dir": dst_dir, "names": [file_name]})
        if res is not None:
            return True
        return False

    def rename_and_move_bangumi(self, info: BangumiInfo, config: BangumiConfig, file_name: str) -> str:
        src_dir = self.storage.aria2_path.rstrip('/')
        src_path = f"{src_dir}/{file_name}"
        target_dir = self.get_target_dir(config).rstrip('/')
        self._makedirs(target_dir)

        new_filename = self.get_standardized_filename(info, config, file_name)
        if not self._rename(src_path, new_filename):
            raise IOError(f"Cannot rename file {file_name}")

        if not self._move(src_dir, target_dir, new_filename):
            raise IOError(f"Cannot move file {file_name}")

        return f"{target_dir}/{new_filename}"

    def get_latest_episode(self, config: BangumiConfig) -> int:
        target_dir = self.get_target_dir(config)

        res = self._api_post("/api/fs/list", {"path": target_dir, "page": 1, "per_page": 1000}, suppress_error = True)
        if not res:
            return 1

        contents = res.get("content") or []
        matches = [
            int(re.search(r'S\d+E(\d+)', item.get("name", "")).group(1))
            for item in contents if re.search(r'S\d+E(\d+)', item.get("name", ""))
        ]

        max_episode = max(matches) if matches else 0
        return -1 if max_episode >= config.episode_count else max_episode + 1
