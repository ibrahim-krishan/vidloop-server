import os
import re
import threading
from flask import Flask, request, jsonify, send_file, Response
import yt_dlp
import tempfile

app = Flask(__name__)

@app.route('/')
def home():
    return "Server is Running!"


def normalize_url(url):
    if 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[1].split('?')[0].split('/')[0]
        return f'https://www.youtube.com/watch?v={video_id}'
    if 'shorts/' in url:
        video_id = url.split('shorts/')[1].split('?')[0].split('/')[0]
        return f'https://www.youtube.com/watch?v={video_id}'
    if 'm.youtube.com' in url:
        url = url.replace('m.youtube.com', 'www.youtube.com')
    if 'music.youtube.com' in url:
        url = url.replace('music.youtube.com', 'www.youtube.com')
    return url


@app.route('/get_url', methods=['GET'])
def get_url():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    video_url = normalize_url(video_url)
    ydl_opts = {'quiet': True, 'no_warnings': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats_list = []
            seen_res = set()

            for f in info.get('formats', []):
                vcodec = f.get('vcodec', 'none')
                res = f.get('height')
                format_id = f.get('format_id', '')
                ext = f.get('ext', '')

                if vcodec == 'none' or not res or not format_id:
                    continue
                if res in seen_res:
                    continue
                seen_res.add(res)

                formats_list.append({
                    "resolution": res,
                    "label": f"{res}p",
                    "format_id": format_id,
                    "ext": ext
                })

            formats_list.sort(key=lambda x: x['resolution'], reverse=True)

            if not formats_list:
                formats_list.append({
                    "resolution": 0,
                    "label": "Best Available",
                    "format_id": "best",
                    "ext": "mp4"
                })

            return jsonify({"formats": formats_list, "normalized_url": video_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download', methods=['GET'])
def download_video():
    video_url = request.args.get('url')
    format_id = request.args.get('format_id', 'best')

    if not video_url:
        return jsonify({"error": "No URL"}), 400

    video_url = normalize_url(video_url)

    try:
        tmp_dir = tempfile.mkdtemp()
        output_template = os.path.join(tmp_dir, 'video.%(ext)s')

        ydl_opts = {
            'format': f'{format_id}+bestaudio[ext=m4a]/{format_id}+bestaudio/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            # تجنب أخطاء الشبكة
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 30,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            # بعد الدمج يصبح mp4
            if not os.path.exists(filename):
                filename = filename.rsplit('.', 1)[0] + '.mp4'

        # ابحث عن الملف إذا لم يُوجد
        if not os.path.exists(filename):
            files = [f for f in os.listdir(tmp_dir) if f.endswith('.mp4')]
            if not files:
                files = os.listdir(tmp_dir)
            if files:
                filename = os.path.join(tmp_dir, files[0])
            else:
                return jsonify({"error": "الملف لم يُنشأ"}), 500

        # إرسال الملف كـ stream لتجنب timeout
        def generate():
            with open(filename, 'rb') as f:
                while chunk := f.read(16384):
                    yield chunk

        file_size = os.path.getsize(filename)
        headers = {
            'Content-Type': 'video/mp4',
            'Content-Disposition': 'attachment; filename="video.mp4"',
            'Content-Length': str(file_size),
        }
        return Response(generate(), headers=headers)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
