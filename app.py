import os
import re
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

def clean_url(url):
    """تنظيف الرابط وإزالة البارامترات الزائدة"""
    url = url.strip()
    
    # ✅ إزالة lc= (رابط تعليق يوتيوب) وأي بارامتر بعده
    url = re.sub(r'[&?]lc=[^&]*', '', url)
    
    # ✅ إزالة بارامترات زائدة شائعة
    url = re.sub(r'[&?]si=[^&]*', '', url)
    url = re.sub(r'[&?]feature=[^&]*', '', url)
    url = re.sub(r'[&?]pp=[^&]*', '', url)
    
    # ✅ تنظيف & أو ? في نهاية الرابط
    url = re.sub(r'[&?]+$', '', url)
    
    return url

@app.route('/get_url', methods=['GET'])
def get_url():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL"}), 400

    # ✅ نظف الرابط أولاً
    video_url = clean_url(video_url)

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'extractor_args': {
            'tiktok': {
                'app_name': ['trill'],
                'app_version': ['34.1.2'],
                'manifest_app_version': ['2023401020'],
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats_list = []

            for f in info.get('formats', []):
                url = f.get('url', '')
                acodec = f.get('acodec', 'none')
                vcodec = f.get('vcodec', 'none')
                height = f.get('height')
                ext = f.get('ext', '')

                has_video = vcodec and vcodec != 'none'
                has_audio = acodec and acodec != 'none'

                if has_video and has_audio and url:
                    formats_list.append({
                        "resolution": height or 0,
                        "label": f"{height}p" if height else ext.upper() or "Best",
                        "url": url
                    })

            # Fallback
            if not formats_list:
                direct = info.get('url')
                if direct:
                    formats_list.append({
                        "resolution": info.get('height', 0),
                        "label": "Best Available",
                        "url": direct
                    })

            if not formats_list:
                return jsonify({"error": "لم نجد أي رابط للفيديو"}), 404

            formats_list.sort(key=lambda x: x['resolution'], reverse=True)
            return jsonify({"formats": formats_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
