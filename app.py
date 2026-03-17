import os
import tempfile
import traceback
from flask import Flask, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

@app.route('/')
def home():
    return "Server is Running!"


# ✅ تنظيف الرابط
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


# ✅ جلب الجودات
@app.route('/get_url', methods=['GET'])
def get_url():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    video_url = normalize_url(video_url)

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        formats_list = []
        seen_res = set()

        for f in info.get('formats', []):
            vcodec = f.get('vcodec', 'none')
            res = f.get('height')
            format_id = f.get('format_id', '')

            if vcodec == 'none' or not res or not format_id:
                continue
            if res in seen_res:
                continue

            seen_res.add(res)

            formats_list.append({
                "resolution": res,
                "label": f"{res}p",
                "format_id": format_id
            })

        formats_list.sort(key=lambda x: x['resolution'], reverse=True)

        if not formats_list:
            formats_list.append({
                "resolution": 0,
                "label": "Best Available",
                "format_id": "best"
            })

        return jsonify({
            "formats": formats_list,
            "normalized_url": video_url
        })

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# ✅ تحميل الفيديو (نسخة قوية)
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

        # 🔥 fallback مهم
        if not format_id or format_id == "null":
            format_id = "best"

        ydl_opts = {
            # ✅ صيغة مستقرة بدون انفجار
            'format': f'{format_id}+bestaudio/best',

            'outtmpl': output_template,
            'merge_output_format': 'mp4',

            'quiet': True,
            'no_warnings': True,

            # 🔥 استقرار عالي
            'retries': 5,
            'fragment_retries': 5,
            'socket_timeout': 60,

            # 🔥 مهم جدًا لتفادي حظر يوتيوب
            'http_headers': {
                'User-Agent': 'Mozilla/5.0'
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)

            # تأكد من mp4
            if not os.path.exists(filename):
                filename = filename.rsplit('.', 1)[0] + '.mp4'

        # 🔍 fallback لو ما انشأ الملف
        if not os.path.exists(filename):
            files = os.listdir(tmp_dir)
            if not files:
                return jsonify({"error": "file not created"}), 500
            filename = os.path.join(tmp_dir, files[0])

        file_size = os.path.getsize(filename)

        # 🔥 حماية من انهيار السيرفر
        if file_size > 150 * 1024 * 1024:
            return jsonify({"error": "file too large"}), 400

        # ✅ إرسال الملف مباشرة (أفضل من streaming)
        return send_file(
            filename,
            as_attachment=True,
            download_name="video.mp4",
            mimetype="video/mp4"
        )

    except Exception as e:
        print("🔥 ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
