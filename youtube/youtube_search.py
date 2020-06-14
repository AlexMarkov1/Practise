from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class Youtube_search:

    API_KEY = 'AIzaSyAOt9-bdIh1PyqH6vNmsn9X97MvH-8FYdM'
    SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'

    def search(self, q, max_results):
        youtube = build(self.SERVICE_NAME, self.API_VERSION,
                        developerKey=self.API_KEY)

        search_response = youtube.search().list(
            q=q,
            part='id,snippet',
            maxResults=max_results
        ).execute()

        videos = []

        for search_result in search_response.get('items', []):
            if search_result['id']['kind'] == 'youtube#video':
                videos.append('Title: %s;\nId:%s;\nPublication date:%s.\n\n' % (search_result['snippet']['title'], 
                                           search_result['id']['videoId'], search_result['snippet']['publishedAt']))
                found_video = Found_video(id = search_result['id']['videoId'], title = search_result['snippet']['title'], date = search_result['snippet']['publishedAt'], user_query = q)
                try:
                    db.session.add(found_video)
                    db.session.commit()
                except: "Произошла ошибка с базой данных!"
                    
            else:
                pass #НАЙДЕНО НЕ ВИДЕО, А YOUTUBE-КАНАЛ ИЛИ ПЛЕЙЛИСТ

        print('Videos:\n', '\n'.join(videos))
        
        print("\n\n\n")
    
        return [videos]
