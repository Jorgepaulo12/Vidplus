from flask import Flask, render_template, request as flask_request, send_file
from pytube import YouTube, Playlist
import re
import random
import youtube_dl

app = Flask(__name__)

def clean_query(query):
    return re.sub(r'\s+', ' ', query).strip()

def is_youtube_link(query):
    return 'youtube.com' in query

def perform_automatic_search(query):
    try:
        search_results = YouTube.search(query)
        videos = [{'title': video.title, 'url': f"https://www.youtube.com/watch?v={video.video_id}", 'thumbnail': video.thumbnail_url}
                  for video in search_results[:20]]  # Lista os 20 primeiros resultados
        return videos
    except Exception as e:
        print(f"Erro ao realizar a pesquisa automática: {e}")
        return []

def download_video_youtube(url, quality):
    try:
        yt = YouTube(url)
        if 'video' in quality:
            if 'best' in quality:
                video = yt.streams.get_highest_resolution()
            else:
                video = yt.streams.get_lowest_resolution()
            return video.download()
        elif 'audio' in quality:
            if 'best' in quality:
                audio = yt.streams.filter(only_audio=True).order_by('abr').last()
            else:
                audio = yt.streams.filter(only_audio=True).order_by('abr').first()
            return audio.download(output_path="audio/")
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
            return video_path
    except Exception as e:
        print(f"Erro ao baixar vídeo do YouTube: {e}")
        return None

def download_playlist_youtube(url, quality):
    try:
        playlist = Playlist(url)
        playlist.download_all()
        return "Playlist baixada com sucesso!"
    except Exception as e:
        print(f"Erro ao baixar playlist do YouTube: {e}")
        return None

def download_video_other_sites(url, quality):
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s'
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            return filename
    except Exception as e:
        print(f"Erro ao baixar vídeo de outros sites: {e}")
        return None

@app.route('/')
def index():
    cores = ["população", "cursos", "idiomas", "filmes", "nutrição", "últimas notícias", "tecnologia", "melhores videos"]
    r = random.choice(cores)
    initial_query = r  # Consulta inicial pode ser ajustada conforme necessário
    videos = perform_automatic_search(initial_query)
    return render_template('index.html', videos=videos)

@app.route('/process', methods=['POST'])
def process():
    query = flask_request.form['query']
    quality = flask_request.form.get('quality')

    if is_youtube_link(query):
        # É um link do YouTube
        if 'playlist' in query:
            try:
                message = download_playlist_youtube(query, quality)
                return render_template('message.html', message=message)
            except Exception as e:
                return render_template('error.html', error=str(e))
        else:
            try:
                video_path = download_video_youtube(query, quality)
                if video_path:
                    return send_file(video_path, as_attachment=True)
                else:
                    return render_template('error.html', error="Erro ao baixar vídeo do YouTube.")
            except Exception as e:
                return render_template('error.html', error=str(e))
    else:
        # É um link de outro site
        try:
            video_path = download_video_other_sites(query, quality)
            if video_path:
                return send_file(video_path, as_attachment=True)
            else:
                return render_template('error.html', error="Erro ao baixar vídeo de outros sites.")
        except Exception as e:
            return render_template('error.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
