from yt_dlp.extractor.common import InfoExtractor
import re
import json
import time
from bs4 import BeautifulSoup
from yt_dlp.utils import (
    OnDemandPagedList,
    parse_iso8601,
    traverse_obj,
    int_or_none,
    try_get,
    urlencode_postdata,
)
import urllib.parse

class PMVHavenVideoIE(InfoExtractor):
    IE_NAME = 'pmvhaven:video'
    _VALID_URL = r'https?://(?:www\.)?pmvhaven\.com/video/[^_]+_(?P<id>[a-zA-Z0-9]+)'
    
    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        soup = BeautifulSoup(webpage, 'html.parser')

        title = self._extract_title(soup)
        uploader = self._extract_uploader(soup)
        categories = self._extract_categories(soup)
        tags = self._extract_tags(soup)
        music = self._extract_music(soup)
        creator = self._extract_creator(soup)
        stars = self._extract_stars(soup)
        description = self._extract_description(soup)
        duration = self._extract_duration(soup)
        view_count = self._extract_view_count(soup)
        upload_date = self._extract_upload_date(soup)
        thumbnail = self._extract_thumbnail(soup)
        formats = self._extract_formats(soup, url)
        video_meta = self._extract_video_meta(soup)

        return {
            'id': video_id,
            'title': title,
            'age_limit': 18,
            'uploader': uploader,
            'categories': categories,
            'tags': tags,
            'music': music,
            'creator': creator,
            'stars': stars,
            'description': description,
            'duration': duration,
            'view_count': view_count,
            'upload_date': upload_date,
            'thumbnail': thumbnail,
            'formats': formats,
            **video_meta
        }

    def _extract_title(self, soup):
        title_meta = soup.find('meta', attrs={'property': 'og:title'})
        if title_meta:
            return title_meta['content']
        title_meta = soup.find('meta', attrs={'name': 'twitter:title'})
        if title_meta:
            return title_meta['content']
        return None

    def _extract_uploader(self, soup):
        # Implement your method to extract categories here
        return None

    def _extract_categories(self, soup):
        # Implement your method to extract categories here
        return []

    def _extract_tags(self, soup):
        tags_meta = soup.find('meta', attrs={'property': 'og:video:tag'})
        if tags_meta:
            return tags_meta['content'].split(', ')
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta:
            return keywords_meta['content'].split(', ')
        return []

    def _extract_music(self, soup):
        # Implement your method to extract music here
        return []

    def _extract_creator(self, soup):
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        if desc_meta:
            description = desc_meta['content']
            creator = description.split()[-1]
            return creator
        return None


    def _extract_stars(self, soup):
        # Implement your method to extract stars here
        return []

    def _extract_description(self, soup):
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        if desc_meta:
            return desc_meta['content']
        desc_meta = soup.find('meta', attrs={'property': 'og:description'})
        if desc_meta:
            return desc_meta['content']
        return None

    def _extract_duration(self, soup):
        duration_meta = soup.find('meta', attrs={'property': 'og:video:duration'})
        if duration_meta:
            return int(duration_meta['content'])
        return None

    def _extract_view_count(self, soup):
        # Implement your method to extract view count here
        return None

    def _extract_upload_date(self, soup):
        # Implement your method to extract upload date here
        return None

    def _extract_thumbnail(self, soup):
        thumbnail_meta = soup.find('meta', attrs={'property': 'og:image'})
        if thumbnail_meta:
            return thumbnail_meta['content']
        thumbnail_meta = soup.find('meta', attrs={'name': 'twitter:image'})
        if thumbnail_meta:
            return thumbnail_meta['content']
        return None

    def _extract_formats(self, soup, url):
        video_meta = soup.find('meta', attrs={'property': 'og:video:secure_url'})
        if not video_meta:
            video_meta = soup.find('meta', attrs={'name': 'twitter:player'})
        video_url = video_meta['content'] if video_meta else None
        width = self._extract_width(soup)
        height = self._extract_height(soup)
        resolution = f'{width}x{height}' if width and height else 'unknown'
        if video_url:
            return [{
                'url': video_url, 
                'ext': 'mp4', 
                'http_headers': {'Referer': f'{url}'},
                #'vcodec': '',
                #'acodec': '',
                'resolution': resolution
            }]
        return []

    def _extract_video_meta(self, soup):
        meta = {}
        width_meta = soup.find('meta', attrs={'property': 'og:video:width'})
        height_meta = soup.find('meta', attrs={'property': 'og:video:height'})
        if not width_meta:
            width_meta = soup.find('meta', attrs={'name': 'twitter:player:width'})
        if not height_meta:
            height_meta = soup.find('meta', attrs={'name': 'twitter:player:height'})

        if width_meta and height_meta:
            meta['width'] = int(width_meta['content'])
            meta['height'] = int(height_meta['content'])
        
        if 'width' in meta and 'height' in meta:
            meta['resolution'] = f"{meta['width']}x{meta['height']}"
        
        return meta

    def _extract_width(self, soup):
        width_meta = soup.find('meta', attrs={'property': 'og:video:width'})
        if not width_meta:
            width_meta = soup.find('meta', attrs={'name': 'twitter:player:width'})
        if width_meta:
            return int(width_meta['content'])
        return None

    def _extract_height(self, soup):
        height_meta = soup.find('meta', attrs={'property': 'og:video:height'})
        if not height_meta:
            height_meta = soup.find('meta', attrs={'name': 'twitter:player:height'})
        if height_meta:
            return int(height_meta['content'])
        return None

class PMVHavenUserIE(InfoExtractor):
    IE_NAME = 'pmvhaven:user'
    _VALID_URL = r'https?://(?:www\.)?pmvhaven\.com/profile/(?P<id>[\w.-]+)'

    _API = 'https://pmvhaven.com/api/v2/profileInput'
    _PAGE_SIZE = 20  # API currently returns 20 items per page

    _TESTS = [{
        'url': 'https://pmvhaven.com/profile/wezzam',
        'info_dict': {'id': 'wezzam', 'title': 'wezzam'},
        'playlist_mincount': 20,
    }]

    def _call_api(self, user, page):
        """
        Page 0 (first page) is fetched without 'index'.
        Page 1 -> index: 2, Page 2 -> index: 3, etc.
        """
        payload = {'mode': 'getProfileVideos', 'user': user}
        if page > 0:
            payload['index'] = page + 1  # 1->2, 2->3...

        headers = {
            'Content-Type': 'text/plain;charset=UTF-8',
            'Origin': 'https://pmvhaven.com',
            'Referer': f'https://pmvhaven.com/profile/{user}',
        }
        return self._download_json(
            self._API, user,
            note=f'Downloading profile JSON page {page + 1}',
            headers=headers,
            data=json.dumps(payload).encode('utf-8'))

    @staticmethod
    def _slugify(title):
        """
        PMVHaven-safe slug to match PMVHavenVideoIE URL regex:
        keep [A-Za-z0-9 ] -> hyphens; strip others.
        """
        if not title:
            return 'video'
        cleaned = re.sub(r'[^A-Za-z0-9 ]+', '', title)
        slug = re.sub(r'\s+', '-', cleaned).strip('-')
        return slug or 'video'

    def _entries_page(self, user, page):
        data = self._call_api(user, page)

        # Stop paging once we've covered total count
        total = int_or_none(data.get('count'))
        if total is not None and page * self._PAGE_SIZE >= total:
            return

        videos = traverse_obj(data, ('videos', {list})) or []
        for v in videos:
            vid = traverse_obj(v, ('_id', {str}))
            title = traverse_obj(v, ('title', {str})) or vid
            slug = self._slugify(title)
            webpage_url = f'https://pmvhaven.com/video/{slug}_{vid}'

            ie_result = self.url_result(
                webpage_url,
                ie=PMVHavenVideoIE.ie_key(),
                video_id=vid,
                video_title=title,
            )

            iso = traverse_obj(v, ('isoDate', {str}))
            thumb_list = traverse_obj(v, ('thumbnails', {list})) or []
            thumbs = [{'url': t} for t in thumb_list if isinstance(t, str)]
            views = int_or_none(traverse_obj(v, ('views', {int, str})))
            uploader = traverse_obj(v, ('uploader', {str})) or traverse_obj(v, ('creator', {str}))

            ie_result.update({
                'thumbnails': thumbs or None,
                'timestamp': parse_iso8601(iso),
                'uploader': uploader,
                'view_count': views,
            })
            yield ie_result

    def _real_extract(self, url):
        user = self._match_id(url)

        def page_func(page):
            return list(self._entries_page(user, page))

        return self.playlist_result(
            OnDemandPagedList(page_func, self._PAGE_SIZE),
            playlist_id=user, playlist_title=user)
