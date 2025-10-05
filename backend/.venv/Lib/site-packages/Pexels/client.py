"""
Client class for the Pexels Unofficial API Wrapper
Author: Joker Hacker
"""

from json import JSONDecodeError
import re
from typing import Any, Dict, Tuple, Optional, Union
import requests
from Pexels.constants import COLOR, LOCALE_SUPPORTED, ORIENTATION, SIZE
from Pexels.errors import PexelsError, QuotaExceedError
from Pexels.types import CollectionMediaResponse, CollectionResponse, Photo, PhotoResponse, Video, VideoResponse

class Client:
    """
    This object represents Client.

    .. code:: python

        client = Client(token="abcde12345")
    Note:
        * Whenever you are doing an API request make sure to show a prominent link to Pexels.
        You can use a text link (e.g. "Photos provided by Pexels") or a link with our logo.

        * Always credit our photographers when possible (e.g. "Photo by John Doe on Pexels" with a link to the photo page on Pexels).
    
        * Most Pexels API requests return multiple records at once. All of these endpoints are paginated, 
        and can return a maximum of 80 requests at one time. Each paginated request accepts the same parameters and returns the same pagination data in the response.

        * The `prev_page` and `next_page` response attributes will only be returned if there is a corresponding page. 

    Warning:
        * You may not copy or replicate core functionality of Pexels (including making Pexels content available as a wallpaper app).

        * Do not abuse the API. By default, the API is rate-limited to 200 requests per hour and 20,000 requests per month.

    Args:
        token (:obj:`str`): Unique authentication token.
        base_endpoint (:obj:`str`, optional): Base endpoint of the API,
            defaults to https://api.pexels.com/v1/
        video_endpoint (:obj:`str`, optional): Video endpoint of the API,
            defaults to https://api.pexels.com/videos
    """

    def __init__(
        self,
        token: str,
        base_endpoint: str = "https://api.pexels.com/v1/",
        video_endpoint: str = "https://api.pexels.com/videos"
    ):

        self._base_endpoint = base_endpoint
        self._video_endpoint = video_endpoint
        self._token = token
        self._header = {'Authorization': self._token}
        self.session = requests.Session()

    def _make_request(
        self,
        path: str,
        search_type: str,
        method: str = "get",
        query: Dict = {},
        **kwargs: Dict[Any, Any]
    ) -> Tuple[Union[Dict, str], requests.Response]:

        if search_type == 'photo':
            endpoint = self._base_endpoint
            req = self.session.request(
                    method, 
                    f'{endpoint}/{path}', 
                    headers=self._header, 
                    params=query,
                    **kwargs
                )
        elif search_type == 'video':
            endpoint = self._video_endpoint
            req = self.session.request(
                    method, 
                    f'{endpoint}/{path}', 
                    headers=self._header, 
                    params=query,
                    **kwargs,
                )
        else:
            raise PexelsError("Invalid parameter search_type given")

        if req.status_code in [200, 201]:
            try:
                return req.json(), req
            except JSONDecodeError:
                return req.text, req
        elif req.status_code == 400:
            raise PexelsError("Bad Request Caught")
        elif req.status_code == 429:
            raise QuotaExceedError("You have exceeded your rate limit.")
        else:
            raise PexelsError(f"{req.status_code} : {req.reason}")

    def search_photos(
        self, 
        query: str, 
        orientation: Optional[str] = "", 
        size: Optional[str] = "",
        color: Optional[str] = "",
        locale: Optional[str] = "", 
        page: Optional[int] = 1,
        per_page: Optional[int] = 15,
        **kwargs
    ) -> PhotoResponse:
        """
        This method enables you to search photos for any topic that you would like.
        For example your query could be something broad like `Nature`, `Tigers`, `People`.
        Or it could be something specific like Group of people working.
        
        Args:
            query (:obj:`str`): The search query. `Ocean`, `Tigers`, `Pears`, etc.
            orientation (:obj:`str`, optional): Desired photo orientation.
                list of supported orientations are available at :obj:`Pexels.constants.ORIENTATION`.
            size (:obj:`str`, optional): Minimum photo size.
                list of supported sizes are available at :obj:`Pexels.constants.SIZE`.
            color (:obj:`str`, optional): Desired photo color.
                list of supported colors are available at :obj:`Pexels.constants.COLOR`.
            locale (:obj:`str`, optional): The locale of the search you are performing.
                list of supported locales are available at :obj:`Pexels.constants.LOCALE_SUPPORTED`.
            page (:obj:`int`, optional): The page number you are requesting. Default: 1
            per_page (:obj:`int`, optional): The number of results you are requesting per page. Default: 15 Max: 80
        
        Returns:
            :class:`Pexels.types.PhotoResponse`
        
        Raises:
            PexelsError: When invalid `orientation` or `color` or `size` or `locale` given or when `per_page` is above 80.
        """

        if orientation in ORIENTATION:
            pass
        elif orientation == "":
            pass
        else:
            raise PexelsError("Invalid value given for orientation, supported ones are landscape, portrait and square.")
        
        color_match = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color)
        if color in COLOR:
            pass
        elif color_match:
            pass
        elif color == "":
            pass
        else:
            raise PexelsError("Invalid color name or hexadecimal code given.")

        if size in SIZE:
            pass
        elif size == "":
            pass
        else:
            raise PexelsError("Invalid photo size given, the supported ones are large, medium and small.")

        if locale == "":
            pass
        elif locale not in LOCALE_SUPPORTED:
            raise PexelsError("Invalid locale given.")

        if per_page > 80:
            raise PexelsError("per_page can not be more than 80")

        params = {
            'orientation': orientation, 
            'size': size, 
            'color': color, 
            'locale': locale, 
            'page': page,
            'per_page': per_page,
            **kwargs
        }

        data, req = self._make_request(f"search?query={query}", search_type='photo', query=params)
        return PhotoResponse(**data)

    def search_curated_photo(self, page: Optional[int] =1, per_page: Optional[int] = 15) -> PhotoResponse:
        """
        This method enables you to receive real-time photos curated by the Pexels team.
        We add at least one new photo per hour to our curated list so that you always get a changing selection of trending photos. 
        
        Args:
            page (:obj:`int`, optional): The page number you are requesting. Default: 1
            per_page (:obj:`int`, optional): The number of results you are requesting per page. Default: 15 Max: 80
        
        Returns:
            :class:`Pexels.types.PhotoResponse`
        
        Raises:
            PexelsError: When `per_page` is above 80.
        """
        if per_page > 80:
            raise PexelsError("per_page can not be more than 80")

        params = {'page': page, 'per_page': per_page}

        data, req = self._make_request("curated", "photo", query=params)
        return PhotoResponse(**data)

    def get_photo(self, id: int) -> Photo:
        """
        Retrieve a specific `Photo` from its id.

        Args:
            id (:obj:`int`): The id of the photo you are requesting.
        
        Returns: 
            :class:`Pexels.types.Photo`
        """

        data, req = self._make_request(f"photos/{id}", "photo")
        return Photo(**data)

    def search_videos(
        self,
        query: str,
        orientation: str = "",
        size: str = "",
        locale:str = "",
        page: Optional[int] = 3,
        per_page: Optional[int] = 15,
        **kwargs
    ) -> VideoResponse:
        """
        This method enables you to search Videos for any topic that you would like.
        For example your query could be something broad like `Nature`, `Tigers`, `People`. Or it could be something specific like Group of people working. 
        
        Args:
            query (:obj:`str`): The search query. `Ocean`, `Tigers`, `Pears`, etc.
            orientation (:obj:`str`, optional): Desired Video orientation.
                list of supported orientations are available at :obj:`Pexels.constants.ORIENTATION`.
            size (:obj:`str`, optional): Minimum Video size.
                list of supported sizes are available at :obj:`Pexels.constants.SIZE`.
            locale (:obj:`str`, optional): The locale of the search you are performing.
                list of supported locales are available at :obj:`Pexels.constants.LOCALE_SUPPORTED`.
            page (:obj:`int`, optional): The page number you are requesting. Default: 1
            per_page (:obj:`int`, optional): The number of results you are requesting per page. Default: 15 Max: 80
        
        Returns:
            :class:`Pexels.types.VideoResponse`
        
        Raises:
            PexelsError: When invalid `orientation` or `size` or `locale` given or when `per_page` is above 80.
        """

        if orientation in ORIENTATION:
            pass
        elif orientation == "":
            pass
        else:
            raise PexelsError("Invalid value given for orientation, supported ones are landscape, portrait and square.")
        
        if size in SIZE:
            pass
        elif size == "":
            pass
        else:
            raise PexelsError("Invalid photo size given, the supported ones are large, medium and small.")

        if locale == "":
            pass
        elif locale not in LOCALE_SUPPORTED:
            raise PexelsError("Invalid locale given.")

        if per_page > 80:
            raise PexelsError("per_page can not be more than 80")

        params = {
            'orientation': orientation, 
            'size': size, 
            'locale': locale, 
            'page': page,
            'per_page': per_page,
            **kwargs
        }

        data, req = self._make_request(f"search?query={query}", search_type="video", query=params)
        return VideoResponse(**data)

    def get_popular_videos(
        self,
        min_width: Optional[int],
        min_height: Optional[int],
        min_duration: Optional[int],
        max_duration: Optional[int],
        page: Optional[int] = 1,
        per_page: Optional[int] = 15,
        **kwargs
    ) -> VideoResponse:
        """
        This method enables you to receive the current popular Pexels videos. 

        Args:
            min_width (:obj:`int`, optional): The minimum width in pixels of the returned videos.
            min_height (:obj:`int`, optional): The maximum height in pixels of the returned videos.
            min_duration (:obj:`int`, optional): The minimum duration in seconds of the returned videos.
            max_duration (:obj:`int`, optional): The maximum duration in seconds of the returned videos.
            page (:obj:`int`, optional): The page number you are requesting. Default: 1
            per_page (:obj:`int`, optional): The number of results you are requesting per page. Default: 15 Max: 80
        
        Returns:
            :class:`Pexels.types.VideoResponse`
         
        Raises:
            PexelsError: When `per_page` is above 80.
        """

        if per_page > 80:
            raise PexelsError("per_page can not be more than 80")

        params = {
            'min_width': min_width,
            'min_height': min_height,
            'min_duration': min_duration,
            'max_duration': max_duration,
            'page': page,
            **kwargs
        }

        data, req = self._make_request("popular", "video", query=params)
        return VideoResponse(**data)

    def get_video(self, id: int) -> Video:
        """
        Retrieve a specific `Video` from its id. 
        
        Args:
            id (:obj:`int`): The id of the video you are requesting.
        
        Returns:
            :class:`Pexels.types.Video`
        """
        
        data, req = self._make_request(f"videos/{id}", "video")
        return Video(**data)
    
    def get_featured_collections(self, page: Optional[int] = 1, per_page: Optional[int] = 15, **kwargs) -> CollectionResponse:
        """
        This method returns all featured collections on Pexels. 
        
        Args:
            page (:obj:`int`, optional): The page number you are requesting. Default: 1
            per_page (:obj:`int`, optional): The number of results you are requesting per page. Default: 15 Max: 80
        
        Returns:
            :class:`Pexels.types.CollectionResponse`
        
        Raises:
            PexelsError: When `per_page` is above 80.
        """
        if per_page > 80:
            raise PexelsError("per_page can not be more than 80.")

        params = {'page': page, 'per_page': per_page}

        data, req = self._make_request("collections/featured", "photo", query=params)
        return CollectionResponse(**data)

    def get_my_collections(self, page: Optional[int] = 1, per_page: Optional[int] = 15, **kwargs) -> CollectionResponse:
        """
        This method returns all of your collections. 
        
        Args:
            page (:obj:`int`, optional): The page number you are requesting. Default: 1
            per_page (:obj:`int`, optional): The number of results you are requesting per page. Default: 15 Max: 80
        
        Returns:
            :class:`Pexels.types.CollectionResponse`
        
        Raises:
            PexelsError: When `per_page` is above 80."""

        if per_page > 80:
            raise PexelsError("per_page can not be more than 80.")

        params = {'page': page, 'per_page': per_page}

        data, req = self._make_request("collections", "photo", query=params)
        return CollectionResponse(**data)
    
    def get_collection_media(self,id: str, type: Optional[str] = "", page: Optional[int] = 1, per_page: Optional[int] = 15, **kwargs) -> CollectionMediaResponse:
        """
        This method returns all featured collections on Pexels. 
        
        Args:
            type (:obj:`str`, optional): The type of media you are requesting, If not given or if given with an invalid
                value, all media will be returned. Supported values are `photos` and `videos`
            page (:obj:`int`, optional): The page number you are requesting. Default: 1
            per_page (:obj:`int`, optional): The number of results you are requesting per page. Default: 15 Max: 80
        
        Returns:
            :class:`Pexels.types.CollectionResponse`
        
        Raises:
            PexelsError: When `per_page` is above 80.
        """

        if per_page > 80:
            raise PexelsError("per_page can not be more than 80.")

        params = {"type": type, "page": page, "per_page": per_page}

        data , req = self._make_request(f"collections/{id}", "photo", query=params)
        return CollectionMediaResponse(**data)
