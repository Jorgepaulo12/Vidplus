from flask import Flask, render_template, request as flask_request, redirect, url_for, send_file, Response
from pytube import YouTube, Playlist, Search
import youtube_dl
import re
import random

app = Flask(__name__)

def clean_query(query):
    return re.sub(r'\s+', ' ', query).strip()

def is_youtube_link(query):
    youtube_regex = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|playlist\?list=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return bool(youtube_regex.match(query))

def perform_automatic_search(query):
    try:
        search_results = Search(query)
        videos = [{'title': video.title, 'url': f"https://www.youtube.com/watch?v={video.video_id}", 'thumbnail': video.thumbnail_url}
                  for video in search_results.results[:8]]  # Lista os 14 primeiros resultados
        return videos
    except Exception as e:
        print(f"Erro ao realizar a pesquisa automática: {e}")
        return []

@app.route('/')
def index():
    cores = ["população", "cursos", "idiomas", "filmes", "nutrição", "últimas notícias", "tecnologia", "melhores videos", "python", "como ser programador", "segredos", "moçambicano"]
    r = random.choice(cores)
    initial_query = r  # Consulta inicial pode ser ajustada conforme necessário
    videos = perform_automatic_search(initial_query)
    return render_template('index.html', videos=videos)

@app.route('/process', methods=['POST'])
def process():
    query = clean_query(flask_request.form['query'])

    if is_youtube_link(query):
        # É um link do YouTube
        if 'playlist?list=' in query:
            return redirect(url_for('playlist', playlist_url=query))
        else:
            try:
                yt = YouTube(query)
                embed_url = f"https://www.youtube.com/embed/{yt.video_id}"
                videos = [{'title': yt.title, 'thumbnail': yt.thumbnail_url, 'url': yt.watch_url, 'embed_url': embed_url, 'video_id': yt.video_id}]
                return render_template('index.html', videos=videos)
            except Exception as e:
                return render_template('error.html', error=str(e))
    else:
        # Não é um link do YouTube, então pesquisaremos usando PyTube
        try:
            search_results = Search(query)
            videos = [{'title': video.title, 'thumbnail': video.thumbnail_url, 'url': video.watch_url, 'embed_url': f"https://www.youtube.com/embed/{video.video_id}", 'video_id': video.video_id}
                      for video in search_results.results]
            return render_template('index.html', videos=videos)
        except Exception as e:
            return render_template('error.html', error=str(e))
            
import youtube_dl

@app.route('/download', methods=['POST'])
def download():
    url = flask_request.form.get('url')
    quality = flask_request.form.get('quality')

    try:
        if is_youtube_link(url):
            yt = YouTube(url)
            if 'video' in quality:
                if 'best' in quality:
                    video = yt.streams.get_highest_resolution()
                else:
                    video = yt.streams.get_lowest_resolution()
                return send_file(video.download(), as_attachment=True)
            elif 'audio' in quality:
                if 'best' in quality:
                    audio = yt.streams.filter(only_audio=True).order_by('abr').last()
                else:
                    audio = yt.streams.filter(only_audio=True).order_by('abr').first()
                return send_file(audio.download(output_path="audio/"), as_attachment=True)
            elif 'both' in quality:
                if 'best' in quality:
                    video = yt.streams.get_highest_resolution()
                    audio = yt.streams.filter(only_audio=True).order_by('abr').last()
                else:
                    video = yt.streams.get_lowest_resolution()
                    audio = yt.streams.filter(only_audio=True).order_by('abr').first()
                video_path = video.download()
                audio_path = audio.download(output_path="audio/")
                # Combine o vídeo e o áudio em um único arquivo ZIP antes de enviar
                return send_file(video_path, as_attachment=True)
        else:
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'downloads/%(title)s.%(ext)s'
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info_dict)
                return send_file(filename, as_attachment=True)
    except Exception as e:
        return render_template('error.html', error=str(e))


if __name__ == '__main__':
    app.run(debug=True, port=5005)
