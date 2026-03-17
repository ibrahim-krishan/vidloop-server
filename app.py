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
            for f in info.get('formats', []):
                # نختار الصيغ التي تحتوي على فيديو وصوت معاً لضمان الجودة والعمل على أندرويد
                if f.get('ext') == 'mp4' and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                    res = f.get('height')
                    if res:
                        formats_list.append({
                            "resolution": res,
                            "label": f"{res}p High Quality",
                            "format_id": f.get('format_id'),
                            "url": f.get('url')
                        })
            
            # ترتيب الجودات من الأعلى للأقل
            formats_list.sort(key=lambda x: x['resolution'], reverse=True)
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
        output_template = os.path.join(tmp_dir, 'video.mp4')
        ydl_opts = {
            'format': format_id,
            'outtmpl': output_template,
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        return send_file(output_template, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # مهم جداً لـ Railway: استخدام المنفذ من متغيرات البيئة
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
            
