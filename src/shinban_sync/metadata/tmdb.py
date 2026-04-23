from typing import Optional

import httpx

from src.shinban_sync.core.logger import logger
from src.shinban_sync.models.tmdb import TMDBTVSearchResult, TMDBSeriesDetails, TMDBAlternativeTitles


class TMDBProvider:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url = "https://api.themoviedb.org/3",
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json"
            },
            timeout = 15.0
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _api_get(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        if not self.client:
            raise RuntimeError("TMDB Client is not initialized. Please use 'async with TMDBProvider(...) as provider:'")

        try:
            resp = await self.client.get(url = endpoint, params = params)
            resp.raise_for_status()
            return resp.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"TMDB [Errno {e.response.status_code}] Req: {endpoint} -> {e.response.text}")
        except Exception as e:
            logger.error(f"TMDB request failed: {e}")

        return None

    async def search_tv(self, query: str, language: str = "zh-CN") -> Optional[TMDBTVSearchResult]:
        data = await self._api_get("/search/tv", {"query": query, "language": language})
        if not data:
            return None

        try:
            return TMDBTVSearchResult.from_json(data)
        except Exception as e:
            logger.error(f"Failed to parse TMDB search result: {e}")

    async def get_series_details(self, series_id: int, language: str = "zh-CN") -> Optional[TMDBSeriesDetails]:
        data = await self._api_get(f"/tv/{series_id}", {"language": language})
        if not data:
            return None

        try:
            return TMDBSeriesDetails.from_json(data)
        except Exception as e:
            logger.error(f"Failed to parse TMDB series (ID:{series_id}): {e}")

    async def get_alternative_titles(self, series_id: int) -> Optional[TMDBAlternativeTitles]:
        data = await self._api_get(f"/tv/{series_id}/alternative_titles")
        if not data:
            return None

        try:
            return TMDBAlternativeTitles.from_json(data)
        except Exception as e:
            logger.error(f"Failed to parse TMDB alternative titles (ID:{series_id}): {e}")
