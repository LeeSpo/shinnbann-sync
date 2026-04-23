from typing import List, Optional, Any

from pydantic import BaseModel


class TMDBGenre(BaseModel):
    id: int
    name: str


class TMDBEpisode(BaseModel):
    id: int
    name: str
    overview: str
    vote_average: float
    vote_count: int
    air_date: str
    episode_number: int
    episode_type: str
    production_code: str
    season_number: int
    show_id: int
    runtime: Optional[int] = None
    still_path: Optional[str] = None


class TMDBCompany(BaseModel):
    id: int
    name: str
    origin_country: str
    logo_path: Optional[str] = None


class TMDBCountry(BaseModel):
    iso_3166_1: str
    name: str


class TMDBSeason(BaseModel):
    id: int
    name: str
    overview: str
    episode_count: int
    season_number: int
    vote_average: float
    air_date: Optional[str] = None
    poster_path: Optional[str] = None


class TMDBSpokenLanguage(BaseModel):
    english_name: str
    iso_639_1: str
    name: str


class TMDBSeriesDetails(BaseModel):
    id: int
    name: str
    original_name: str
    original_language: str
    overview: str
    tagline: str
    status: str
    type: str
    homepage: str
    first_air_date: str
    last_air_date: str
    in_production: bool
    popularity: float
    vote_average: float
    vote_count: int
    adult: bool
    number_of_episodes: int
    number_of_seasons: int
    episode_run_time: List[int]
    languages: List[str]
    origin_country: List[str]
    backdrop_path: Optional[str] = None
    poster_path: Optional[str] = None

    genres: List[TMDBGenre] = []
    networks: List[TMDBCompany] = []
    production_companies: List[TMDBCompany] = []
    production_countries: List[TMDBCountry] = []
    seasons: List[TMDBSeason] = []
    spoken_languages: List[TMDBSpokenLanguage] = []
    created_by: List[Any] = []

    last_episode_to_air: Optional[TMDBEpisode] = None
    next_episode_to_air: Optional[TMDBEpisode] = None

    @classmethod
    def from_json(cls, raw_data: str | dict):
        return cls.model_validate(raw_data) if isinstance(raw_data, dict) else cls.model_validate_json(raw_data)


class TMDBAlternativeTitleItem(BaseModel):
    iso_3166_1: str
    title: str
    type: str = ""


class TMDBAlternativeTitles(BaseModel):
    id: int
    results: List[TMDBAlternativeTitleItem] = []

    @classmethod
    def from_json(cls, raw_data: str | dict):
        return cls.model_validate(raw_data) if isinstance(raw_data, dict) else cls.model_validate_json(raw_data)

    def get_titles_by_country(self, country_codes: List[str]) -> List[str]:
        return [
            item.title
            for item in self.results
            if item.iso_3166_1.upper() in [code.upper() for code in country_codes]
        ]


class TMDBTVSearchItem(BaseModel):
    id: int
    name: str
    original_name: str
    original_language: str
    overview: str
    popularity: float
    vote_average: float
    vote_count: int
    adult: bool = False

    genre_ids: List[int] = []
    origin_country: List[str] = []

    backdrop_path: Optional[str] = None
    poster_path: Optional[str] = None
    first_air_date: Optional[str] = ""


class TMDBTVSearchResult(BaseModel):
    page: int
    results: List[TMDBTVSearchItem] = []
    total_pages: int
    total_results: int

    @classmethod
    def from_json(cls, raw_data: str | dict):
        return cls.model_validate(raw_data) if isinstance(raw_data, dict) else cls.model_validate_json(raw_data)

    def get_best_match(self) -> Optional[TMDBTVSearchItem]:
        return self.results[0] if self.results else None
