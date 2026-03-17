import os
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from flask import Flask, request, jsonify
import yt_dlp
import re

app = Flask(__name__)
VERSION = "v7.0"

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

def extract_video_id(url):
    patterns = [
        r'youtu\.be/([^?&]+)',
        r'youtube\.com/watch\?v=([^&]+)',
        r'youtube\.com/shorts/([^?&]+)',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

def get_via_invidious(video_id):
    """جلب روابط الفيديو عبر Invidious API — بدون bot detection"""
    instances = [
        "https://inv.nadeko.net",
        "https://invidious.nerdvpn.de",
        "https://invidious.privacydev.net",
    ]
    for instance in instances:
        try:
            r = requests.get(f"{instance}/api/v1/videos/{video_id}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                formats = []
                for fmt in data.get('adaptiveFormats', []) + data.get('formatStreams', []):
                    mime = fmt.get('type', '')
                    url = fmt.get('url', '')
                    quality = fmt.get('qualityLabel', '')
                    if 'video/mp4' in mime and url and quality:
                        height = int(quality.replace('p', '').split('.')[0]) if 'p' in quality else 0
                        formats.append({
                            "resolution": height,
                            "label": quality,
                            "url": url
                        })
                if formats:
                    formats.sort(key=lambda x: x['resolution'], reverse=True)
                    return formats
        except:
            continue
    return None

@app.route('/debug')
def debug():
    return jsonify({"version": VERSION, "yt_dlp": yt_dlp.version.__version__})

@app.route('/get_url', methods=['GET'])
def get_url():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL"}), 400

    video_url = clean_url(video_url)

    # ✅ لو يوتيوب جرب Invidious أولاً
    video_id = extract_video_id(video_url)
    if video_id:
        formats = get_via_invidious(video_id)
        if formats:
            return jsonify({"formats": formats, "source": "invidious"})

    # ✅ Fallback: yt-dlp مع كل الـ clients
    clients = ['android', 'ios', 'web_creator', 'mweb']
    last_error = ""

    for client in clients:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
            'extractor_args': {
                'youtube': {'player_client': [client]},
                'tiktok': {
                    'app_name': ['trill'],
                    'app_version': ['34.1.2'],
                    'manifest_app_version': ['2023401020'],
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip',
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
                    if vcodec and vcodec != 'none' and acodec and acodec != 'none' and f_url:
                        formats_list.append({
                            "resolution": height or 0,
                            "label": f"{height}p" if height else ext.upper(),
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
                if formats_list:
                    formats_list.sort(key=lambda x: x['resolution'], reverse=True)
                    return jsonify({"formats": formats_list, "source": "ytdlp"})
        except Exception as e:
            last_error = str(e)
            continue

    return jsonify({"error": last_error}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
