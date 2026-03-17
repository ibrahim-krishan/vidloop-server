import os
import tempfile
import shutil
from flask import Flask, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

@app.route('/get_url', methods=['GET'])
def get_url():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "رابط الفيديو مطلوب"}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats_list = []
            # استخراج الجودات التي تحتوي على فيديو وصوت معاً بصيغة mp4
            for f in info.get('formats', []):
                if f.get('ext') == 'mp4' and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                    res = f.get('height')
                    if res:
                        formats_list.append({
                            "resolution": res,
                            "label": f"{res}p High Quality",
                            "format_id": f.get('format_id')
                        })
            
            formats_list.sort(key=lambda x: x['resolution'], reverse=True)
            return jsonify({"formats": formats_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['GET'])
def download_video():
    video_url = request.args.get('url')
    format_id = request.args.get('format_id', 'best')
    
    if not video_url:
        return jsonify({"error": "رابط الفيديو مطلوب"}), 400

    # استخدام مجلد مؤقت آمن
    tmp_dir = tempfile.mkdtemp()
    try:
        output_path = os.path.join(tmp_dir, 'video.mp4')
        ydl_opts = {
            'format': format_id,
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        return send_file(output_path, as_attachment=True, download_name="video.mp4")
    
    except Exception as e:
        return jsonify({"error": f"فشل التحميل: {str(e)}"}), 500
    # ملاحظة: سيتم تنظيف المجلدات المؤقتة بواسطة نظام التشغيل لاحقاً

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
                       
