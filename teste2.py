from flask import Flask, render_template, request as flask_request, redirect, url_for,send_file,Response,session
from pytube import YouTube, Playlist, Search
import youtube_dl
import re
import random
from io import BytesIO

app = Flask(__name__)
app.config["SECRET_KEY"] = "jorgesss"
def clean_query(query):
    return re.sub(r'\s+', ' ', query).strip()

def is_youtube_link(query):
    youtube_regex = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|playlist\?list=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return bool(youtube_regex.match(query))

def perform_automatic_search(query):
    try:
        search_results = Search(query)
        videos = [{'title': video.title, 'url': f"https://www.youtube.com/watch?v={video.video_id}", 'thumbnail': video.thumbnail_url}
                  for video in search_results.results[:14]]  # Lista os 3 primeiros resultados
        return videos
    except Exception as e:
        print(f"Erro ao realizar a pesquisa automática: {e}")
        return []

@app.route('/',methods=["GET","POST"])
def index():
      # Inicializa a chave 'link'
    if flask_request.method=="POST":
        session["link"] = flask_request.form.get("url")
        url = YouTube(session["link"])
        url.check_availability()
        return render_template("download.html", url=url)

    cores=["população","cursos","idiomas","filmes","nutrição","últimas notícias","tecnologia","melhores videos","pyhon","como ser programdor","segredos","moçambicano"]
    r=random.choice(cores)
    initial_query = r  # Consulta inicial pode ser ajustada conforme necessário
    videos = perform_automatic_search(initial_query)
    return render_template('index.html', videos=videos)
    

# Restante do código permanece o mesmo...

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
            
            
            
@app.route("/download",methods=["POST"])
def download():
    if flask_request.method == "POST":
        if session.get("link") is None:
            return "Erro: Nenhum link do YouTube fornecido."

        buffer = BytesIO()
        itag = flask_request.form.get("itag")
        url = YouTube(session["link"])
        video = url.streams.get_by_itag(itag)
        
        #Buffer comes in
        video.stream_to_buffer(buffer)
        buffer.seek(0)
               
        return send_file(buffer, as_attachment=True, download_name=video.title, mimetype=video.mime_type)
        
    return redirect("/index")





@app.route('/playlist', methods=['GET'])
def playlist():
    playlist_url = flask_request.args.get('playlist_url')
    try:
        pl = Playlist(playlist_url)
        videos = [{'id': idx, 'title': video.title, 'thumbnail': video.thumbnail_url} for idx, video in enumerate(pl.videos)]
        return render_template('playlist.html', videos=videos, playlist_url=playlist_url)
    except Exception as e:
        return render_template('error.html', error=str(e))
        
        
        
        
        


@app.route('/download_playlist', methods=['POST'])
def download_playlist():
    playlist_url = flask_request.form.get('playlist_url')
    video_index = int(flask_request.form.get('video_index'))
    format = flask_request.form.get('format')

    try:
        pl = Playlist(playlist_url)
        video = pl.videos[video_index]

        if format == 'video':
            # Baixa o vídeo em resolução mais alta e formato mp4
            return send_file(video.streams.get_highest_resolution().download(), as_attachment=True)
        elif format == 'audio':
            # Baixa apenas o áudio do vídeo em formato mp3
            return send_file(video.streams.get_audio_only().download(output_path="audios/", filename_prefix="mp3"), as_attachment=True)
        else:
            # Formato inválido
            return render_template('error.html', error="Formato inválido")
    except Exception as e:
        return render_template('error.html', error=str(e))




if __name__ == '__main__':
    app.run(debug=True, port=5005)
