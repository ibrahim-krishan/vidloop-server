import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)
VERSION = "v5.0"

def clean_url(url):
    url = url.strip()
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        remove_keys = {'lc', 'si', 'feature', 'pp', 'ab_channel', 'app'}
        filtered = {k: v for k, v in params.items() if k not in remove_keys}
        new_query = urlencode(filtered, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
    except:
        return url

@app.route('/debug')
def debug():
    return jsonify({"version": VERSION, "yt_dlp": yt_dlp.version.__version__})

@app.route('/get_url', methods=['GET'])
def get_url():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL"}), 400

    video_url = clean_url(video_url)

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        # ✅ الحل الرئيسي لخطأ bot detection
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'android'],
                'player_skip': ['webpage', 'config'],
            },
            'tiktok': {
                'app_name': ['trill'],
                'app_version': ['34.1.2'],
                'manifest_app_version': ['2023401020'],
            }
        },
        # ✅ headers تشبه المتصفح الحقيقي
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats_list = []

            for f in info.get('formats', []):
                f_url = f.get('url', '')
                acodec = f.get('acodec', 'none')
                vcodec = f.get('vcodec', 'none')
                height = f.get('height')
                ext = f.get('ext', '')

                has_video = vcodec and vcodec != 'none'
                has_audio = acodec and acodec != 'none'

                if has_video and has_audio and f_url:
                    formats_list.append({
                        "resolution": height or 0,
                        "label": f"{height}p" if height else ext.upper() or "Best",
                        "url": f_url
                    })

            if not formats_list:
                direct = info.get('url')
                if direct:
                    formats_list.append({
                        "resolution": info.get('height', 0) or 0,
                        "label": "Best Available",
                        "url": direct
                    })

            if not formats_list:
                return jsonify({"error": "لم نجد أي رابط"}), 404

            formats_list.sort(key=lambda x: x['resolution'], reverse=True)
            return jsonify({"formats": formats_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
