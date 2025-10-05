from re import U
from typing import Any, Dict, List, Optional, Union

 
class PexelsType:
    """Base class for all pexels objects"""
 
    def __str__(self) -> str:
        return f'<{self.__class__.__name__}: {self.__dict__}'
    
    def __repr__(self) -> str:
        return self.__str__()
 
class Src(PexelsType):
 
    original: str
    "The image without any size changes. It will be the same as the width and height attributes."
    large: str
    "The image resized to W 940px X H 650px DPR 1."
    large2x: str
    "The image resized W 940px X H 650px DPR 2."
    medium: str
    "The image resized W 940px X H 650px DPR 2."
    small: str
    "The image scaled proportionally so that it's new height is 130px."
    portrait: str
    "The image cropped to W 800px X H 1200px."
    landscape: str
    "The image cropped to W 1200px X H 627px."
    tiny: str
    "The image cropped to W 280px X H 200px."
 
    def __init__(
        self,
        original: str,
        large: str,
        large2x: str,
        medium: str,
        small: str,
        portrait: str,
        landscape: str,
        tiny: str,
        **kwargs
    ) -> None:
 
        self.original = original
        self.large = large
        self.large2x = large2x
        self.medium = medium
        self.small = small
        self.portrait = portrait
        self.landscape = landscape
        self.tiny = tiny
 
class User(PexelsType):

    id: int
    "The id of the videographer."
    name: str
    "The name of the videographer."
    url: str
    "The URL of the videographer's Pexels Profile."

    def __init__(self, id: int, name: str, url: str, **kwargs):

        self.id = id
        self.name = name
        self.url = url

class Photo(PexelsType):
    
    type: str
    "The type of media to be shown in collections."
    id: int
    "The id of the photo."
    width: int
    "The real width of the photo in pixels."
    height: int
    "The real height of the photo in pixels."
    url: str
    "The Pexels URL where the photo is located."
    photographer: str
    "The name of the photographer who took the photo."
    photographer_url: str
    "The URL of the photographer's Pexels profile."
    photographer_id: str
    "The id of the photographer."
    avg_color: str
    "The average color of the photo. Useful for a placeholder while the image loads"
    src: Src
    "An assortment of different image sizes that can be used to display this Photo."
    alt: str
    "Text description of the photo for use in the alt attribute."
 
    def __init__(
        self,
        id: int,
        width: int,
        height: int,
        url: str,
        photographer: str,
        photographer_url: str,
        photographer_id: int,
        avg_color: str,
        src: Src,
        alt: str,
        type: str = "Photo",
        **kwargs
    ) -> None:
 
        self.id = id
        self.width = width
        self.height = height
        self.url = url
        self.photographer = photographer
        self.photographer_url = photographer_url
        self.photographer_id = photographer_id
        self.avg_color = avg_color
        self.src = Src(**src)
        self.alt = alt
 
class VideoFiles(PexelsType):

    id: int
    "The id of the `video_file`"
    quality: str
    "The video quality of the `video_file`"
    file_type: str
    "The video format of the `video_file`"
    width: int
    "The width of the `video_file` in pixels."
    height: int
    "The height of the `video_file` in pixels."
    link: str
    "A link to where the `video_file` is hosted."

    def __init__(
        self,
        id: int,
        quality: str,
        file_type: str,
        width: int,
        height: int,
        link:str,
        **kwargs
    ):

        self.id = id
        self.quality = quality
        self.file_type = file_type
        self.width = width
        self.height = height
        self.link = link

class VideoPicture(PexelsType):

    id: int
    "The id of the `video_picture`"
    picture: str
    "A link to the preview image."
    nr: int

    def __init__(self, id: int, picture: str, nr:int, **kwargs):

        self.id = id
        self.picture = picture
        self.nr = nr 

class PhotoResponse(PexelsType):
 
    photos = List[Photo]
    "A list of `Photo` object"
    page = int
    "The current page number"
    per_page = int
    "The number of results returned with each page"
    total_results = int
    "The total number of results for the request"
    prev_page = str
    "URL for the previous page of results, if applicable"
    next_page = str
    "URL for the next page of results, if applicable"
 
    def __init__(
        self,
        photos: List[Photo],
        page: int,
        per_page: int,
        total_results: int,
        prev_page: str = "",
        next_page: str = "",
        **kwargs
        ):
        #assign photos dict to self.photos
        self.photos = [Photo(**photo) for photo in photos]
        self.page = page
        self.per_page = per_page
        self.total_results = total_results
        self.prev_page = prev_page
        self.next_page = next_page

class Video:
    
    type: str
    "The type of this media to be shown collections."
    id: int
    "The id of the video."
    width: int
    "The real width of the video in pixels."
    height: int
    "The real height of the video in pixels."
    url: str
    "The pexels URL where the video is located."
    image: str
    "URL to a screenshot of the video."
    duration: int
    "The duration of the video in seconds."
    user: User
    "The videographer who shot the video."
    video_files: List[VideoFiles]
    "A list of different sized versions of the video."
    video_pictures: List[VideoPicture]
    "A list of preview pictures of the video."

    def __init__(
        self,
        id: int,
        width: int,
        height: int,
        url: str,
        image: str,
        duration: int,
        user: User,
        video_files: List[VideoFiles],
        video_pictures: List[VideoPicture],
        type: str = "Video",
        **kwargs
    ):
        self.type = type
        self.id = id
        self.width = width
        self.height = height
        self.url = url
        self.image = image
        self.duration = duration
        self.user = user
        self.video_files = [VideoFiles(**vid_file) for vid_file in video_files]
        self.video_pictures = [VideoPicture(**vid_pic) for vid_pic in video_pictures]

class VideoResponse(PexelsType):

    videos: List[Video]
    "A list of `Video` objects."
    url: str
    "The Pexels URL for the current search query."
    page:int
    "The current page number."
    per_page: int
    "The number of results returned with each page."
    total_results: int
    "The total number of results for the request."
    prev_page: str
    "URL for the previous page of results, if applicable."
    next_page: str
    "URL for the next page of results, if applicable."

    def __init__(
        self,
        videos: List[Video],
        url: str,
        page: int,
        per_page: int,
        total_results: int,
        prev_page: Optional[str] = "",
        next_page: Optional[str] = "",
        **kwargs
    ):

        self.videos = [Video(**video) for video in videos]
        self.url = url
        self.page = page
        self.per_page = per_page
        self.total_results = total_results
        self.prev_page = prev_page
        self.next_page = next_page

class Collection(PexelsType):

    id: str
    "The id of the collection."
    title: str
    "The name of the collection."
    description: str
    "The description of the collection."
    private: bool
    "Whether or not  the collection is marked as private."
    media_count: int
    "The total number of media included in this collection."
    photos_count: int
    "The total number of photos included in this collection."
    videos_count: int
    "The total number of videos included in this collection."

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        private: bool,
        media_count: int,
        photos_count: int,
        videos_count: int,
        **kwargs
    ):

        self.id = id
        self.title = title
        self.description = description
        self.private = private
        self.media_count = media_count
        self.photos_count = photos_count
        self.videos_count = videos_count

class CollectionResponse(PexelsType):

    collections: List[Collection]
    "A list of collection objects."
    page: int
    "The current page number."
    per_page: int
    "The number of results returned with each page."
    total_results: int
    "The total number of results for the request."
    prev_page: Optional[str]
    "URL for the previous page of results, if applicable"
    next_page: Optional[str]
    "URL for the next page of results, if applicable."

    def __init__(
        self,
        collections: List[Collection],
        page: int,
        per_page: int,
        total_results: int,
        prev_page: Optional[str] = "",
        next_page: Optional[str] = "",
        **kwargs
    ):

        self.collections = [Collection(**collection) for collection in collections]
        self.page = page
        self.per_page = per_page
        self.total_results = total_results
        self.prev_page = prev_page
        self.next_page = next_page

class CollectionMediaResponse(PexelsType):

    id: str
    "The id of the collection you are requesting."
    media: List[Union[Photo, Video]]
    "A list of media objects. Each object has an extra type attribute to indicate the type of object."
    page: int
    "The current page number."
    per_page: int
    "The number of results returned with each page."
    total_results: int
    "The total number of results for the request."
    prev_page: Optional[str]
    "URL for the previous page of results, if applicable."
    next_page: Optional[str]
    "URL for the next page of results, if applicable."

    def __init__(
        self,
        id: str,
        media: List[Union[Photo, Video]],
        page: int,
        per_page: int,
        total_results: int,
        prev_page: Optional[str] = "",
        next_page: Optional[str] = "",
        **kwargs
    ):

        self.id = id
        self.media = []
        for _media in media:
            if _media["type"] == "Photo":
                self.media.append(Photo(**_media))
            elif _media["type"] == "Video":
                self.media.append(Video(**_media))
            else:
                pass
        
        self.page = page
        self.per_page = per_page
        self.total_results = total_results
        self.prev_page = prev_page
        self.next_page = next_page