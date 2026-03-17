from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/get_url', methods=['GET'])
def get_url():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    # إعدادات yt-dlp لجلب الروابط فقط بدون تحميل
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            formats_list = []
            # استخراج الجودات المتوفرة (التي تحتوي على فيديو وصوت معاً لسهولة التحميل)
            for f in info.get('formats', []):
                # نفلتر الروابط التي تحتوي على فيديو وصوت معاً وامتدادها mp4
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4':
                    formats_list.append({
                        "resolution": f.get('height'),
                        "format_note": f.get('format_note') or f.get('resolution'),
                        "url": f.get('url')
                    })

            # إذا لم نجد mp4 مدمج، نأخذ أفضل رابط متاح
            if not formats_list:
                formats_list.append({
                    "resolution": info.get('height'),
                    "format_note": "Best Quality",
                    "url": info.get('url')
                })

            return jsonify({"formats": formats_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
