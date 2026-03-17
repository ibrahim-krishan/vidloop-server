import os
from flask import Flask, request, jsonify, send_file
import yt_dlp
import tempfile

app = Flask(__name__)

@app.route('/')
def home():
    return "Server is Running!"


@app.route('/get_url', methods=['GET'])
def get_url():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    ydl_opts = {'quiet': True, 'no_warnings': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats_list = []
            seen_res = set()

            for f in info.get('formats', []):
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                res = f.get('height')
                format_id = f.get('format_id', '')
                ext = f.get('ext', '')

                # نتجاهل الصوت فقط بدون فيديو
                if vcodec == 'none':
                    continue
                if not res or not format_id:
                    continue
                if res in seen_res:
                    continue
                seen_res.add(res)

                # نحدد إذا الصيغة تحتاج دمج أم لا
                needs_merge = (acodec == 'none')

                formats_list.append({
                    "resolution": res,
                    "label": f"{res}p",
                    "format_id": format_id,
                    "needs_merge": needs_merge,
                    "ext": ext
                })

            formats_list.sort(key=lambda x: x['resolution'], reverse=True)

            if not formats_list:
                formats_list.append({
                    "resolution": 0,
                    "label": "Best Available",
                    "format_id": "best",
                    "needs_merge": False,
                    "ext": "mp4"
                })

            return jsonify({"formats": formats_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download', methods=['GET'])
def download_video():
    video_url = request.args.get('url')
    format_id = request.args.get('format_id', 'best')

    if not video_url:
        return jsonify({"error": "No URL"}), 400

    try:
        tmp_dir = tempfile.mkdtemp()
        output_template = os.path.join(tmp_dir, 'video.%(ext)s')

        # إذا الصيغة تحتاج دمج نضيف bestaudio، وإلا نحملها مباشرة
        fmt = f'{format_id}+bestaudio[ext=m4a]/best[ext=mp4]/best'

        ydl_opts = {
            'format': fmt,
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            # بعد الدمج الامتداد يصبح mp4
            if not os.path.exists(filename):
                filename = filename.rsplit('.', 1)[0] + '.mp4'

        # إذا ما زال غير موجود، ابحث في المجلد المؤقت
        if not os.path.exists(filename):
            files = [f for f in os.listdir(tmp_dir) if f.endswith('.mp4')]
            if not files:
                files = os.listdir(tmp_dir)
            if files:
                filename = os.path.join(tmp_dir, files[0])
            else:
                return jsonify({"error": "الملف لم يُنشأ"}), 500

        return send_file(
            filename,
            as_attachment=True,
            download_name='video.mp4',
            mimetype='video/mp4'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
