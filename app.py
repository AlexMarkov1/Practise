from flask import Flask, json
from flask_sqlalchemy import  SQLAlchemy
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


#ЗАПРОС К API
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
                    found_video = Found_video(id = search_result['id']['videoId'], title = search_result['snippet']['title'], date = search_result['snippet']['publishedAt'], used_query = q)
                    try:
                        db.session.add(found_video)
                        db.session.commit()
                    except: "Произошла ошибка с базой данных!"
                        
                else:
                    pass #НАЙДЕНО НЕ ВИДЕО, А YOUTUBE-КАНАЛ ИЛИ ПЛЕЙЛИСТ

            print('Videos:\n', '\n'.join(videos))
            return [videos]
    def __init__(self):
        pass


# МОДЕЛИ

#запрос
class User_query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(50), unique=True)
    def __repr__(self):
        return '<User_query %r>' % self.id

#понравившиеся видео
class Favorite_video(db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String(100), nullable = False)
    date = db.Column(db.DateTime, nullable=False)
    def __repr__(self):
        return '<Favorite_video %r>' % self.id

#найденные видео
class Found_video(db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    used_query = db.Column(db.String(50), nullable = False)
    def __repr__(self):
        return '<Found_video %r>' % self.id


# ПОНРАВИВШИЕСЯ ВИДЕО
@app.route('/look-at-favorite_videos')
def show_favorite_videos():
    videos = Favorite_video.query.order_by(Favorite_video.date.desc()).all()
    if len(videos) == 0:
        print("\nНет понравившихся видео!\n")
    else:
        print("Понравившиеся видео:\n")    
        for v in videos:
            print("id: " + v.id)
            print("title: " + v.title)
            print("date: " + str(v.date))
            print()
    return "Работает, смотрите в командной строке"


# ДАННЫЕ О ПОНРАВИВШЕМСЯ ВИДЕО
@app.route('/look-at-favorite_video <video_id>')
def show_video_details(video_id):
    try:
        video = Favorite_video.query.get(video_id)
        print("id: " + video.id + "; title: " + video.title)
        print("date: " + str(video.date))
    except:
        return "Ошибка при просмотре данных! Проверьте id видео"
    return "Работает, смотрите в командной строке"


# ДОБАВЛЕНИЕ В ПОНРАВИВШИЕСЯ
@app.route('/add-to-favorite_videos <video_id>')
def add(video_id):
    try:
        video = Found_video.query.get(video_id)
        print('\nВ "Понравившиеся" добавлено видео с параметрами: ')
        print("id: " + video.id + "; title: " + video.title)
        print("date: " + str(video.date))
        new_favorite_video = Favorite_video(id = video.id, title = video.title, date = video.date)
        db.session.add(new_favorite_video)
        db.session.commit()
        videos = Favorite_video.query.order_by(Favorite_video.date.desc()).all()
        print("\nПонравившиеся видео:\n")    
        for v in videos:
            print("id: " + v.id)
            print("title: " + v.title)
            print("date: " + str(v.date))
            print()
    except:
        return 'Ошибка при добавлении в "Понравившиеся"! Проверьте id видео'
    return "Работает, смотрите в командной строке"


# УДАЛЕНИЕ ИЗ ПОНРАВИВШИХСЯ
@app.route('/delete-from-favorite_videos <video_id>/')
def delete_video(video_id):
    try:
        video = Favorite_video.query.get(video_id)
        print('\nИз "Понравившихся" удалено видео с параметрами:')
        print("id: " + video.id + "; title: " + video.title)
        print("date: " + str(video.date) + ";")
        db.session.delete(video)
        db.session.commit()
        print()
        show_favorite_videos()
    except:
        return 'Ошибка при удалении из "Понравившихся"! Проверьте id видео'        
    return "Работает, смотрите в командной строке"     


# ПОИСК

youtube_search = Youtube_search()

@app.route("/I-search <q>")
def search_videos(q):
    saved_queries = db.session.query(User_query.text)
    
    tmp = ()
    
    for i in saved_queries:
        tmp += i    
    
    if q in list(tmp): # ЕСЛИ ЗАПРОС НЕ НОВЫЙ, РЕЗУЛЬТАТ ИЗВЛЕКАЕТСЯ ИЗ БД
        try:
            videos = db.session.query(Found_video).filter(Found_video.used_query == q).order_by(Found_video.date).all()
            print ('\nРезультаты поиска по запросу ' + '"' + q + '":\n')
            for v in videos:
               print("id: " + v.id + "; title: " + v.title)
               print("date: " + str(v.date) + "\n")        
        except:
            return "Произошла ошибка с базой данных!"
    else: #ИНАЧЕ ПОИСК С ЗАПРОСОМ К YOUTUBE API
        youtube_search = Youtube_search()
        
        data = youtube_search.search(q, 15) # кол-во результатов
        app.response_class(response=json.dumps(data),
        status = 200, content_type = "application/json")
    return "Работает, смотрите в командной строке"     

    
if __name__ == "__main__":
    app.run()