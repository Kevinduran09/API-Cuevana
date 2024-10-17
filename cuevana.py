from dataclasses import dataclass, field
from urllib.parse import urlencode
from typing import Dict, List, Optional, Tuple, Type, Union
from types import TracebackType
from bs4 import BeautifulSoup, Tag, ResultSet
from dataclasses import dataclass
import config
import cloudscraper
import json
import re
from exception import PeliParseError


@dataclass
class Movie:
    id: Union[str, int] = field(default=None)
    title: str = field(default='Unknown')
    year: int = field(default=0)
    duration: str = field(default='0:00h')
    description: str = field(default='')
    genre: List[str] = field(default_factory=list)
    actors: List[str] = field(default_factory=list)
    image_url: Optional[str] = field(default=None)


class CuevanaAPI(object):

    def __init__(self, *args, **kwargs):
        session = kwargs.get("session", None)
        self._scraper = cloudscraper.create_scraper(session)

    def close(self) -> None:
        self._scraper.close()

    def __enter__(self) -> "CuevanaAPI":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def search_per_page(self, url: str, page: int = None):
        url = f"{url}/page/{page}"
        print(url)
        return self._scraper.get(url)

    def search(self, url: str = config.SEARCH_URL, q: str = None, page: int = None):
        params = dict()
        if q is not None:
            params['q'] = q
        params = urlencode(params)
        if params != '':
            url = f"{url}?{params}"
        response = ''
        if q is None and page is not None and isinstance(page, int):
            response = self.search_per_page(url=url, page=page)
        else:
            response = self._scraper.get(url=url)
        print(url)
        soup = BeautifulSoup(response.text, "lxml")

        with open("output.xml", "w", encoding="utf-8") as file:
            file.write(str(soup.prettify()))
        return soup.select("div.apt ul.MovieList li div.TPost")

    def search_movie(self, q: str = None, page: int = None):
        url = config.MOVIES_URL
        elements = self.search(url, q, page)
        print(self.get_movies_info(elements))

    def search_series(self, page: int = None):
        url = config.SERIES_URL
        return self.search(url, page)

    def get_movies_info(self, elements: ResultSet):
        list = []
        for element in elements:
            try:
                movie_id = element.select_one(
                    "a")["href"][1:].removeprefix('pelicula/')
                title = element.select_one("span.Title").string
                year = element.select_one("span.Year").string
                duration = element.select_one(
                    "span.Time").string if element.select_one(
                    "span.Time") else '0:00h'

                desc = element.select_one(
                    "div.Description p")
                description = desc.string if desc is not None else 'unknown'

                genres_e = element.select_one(
                    "p.Genre.AAIco-movie_creation")
                genres = [genre.get_text(strip=True) for genre in genres_e if genre.get_text(
                    strip=True) and genre.get_text(strip=True) != ','] if genres_e else 'unknown'
                actors_e = element.select_one("p.Actors AAIco-person")
                actors = [actor.get_text(strip=True)
                          for actor in actors_e if actor.get_text(strip=True) and actor.get_text(strip=True) != ','] if actors_e else 'unknown'
                img_e = element.select_one(
                    "div.Image img")
                image_url = img_e.get('src', None) if img_e else 'not src'
                list.append(
                    Movie(
                        movie_id,
                        title,
                        year,
                        duration,
                        description,
                        genres,
                        actors,
                        image_url
                    )
                )
            except Exception as ex:
                raise PeliParseError(ex)
        return list


if __name__ == '__main__':

    with CuevanaAPI() as api:
        api.search_movie()
