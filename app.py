import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/get_url', methods=['GET'])
def get_url():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL"}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats_list = []

            for f in info.get('formats', []):
                url = f.get('url', '')
                ext = f.get('ext', '')
                acodec = f.get('acodec', 'none')
                vcodec = f.get('vcodec', 'none')
                height = f.get('height')

                # ✅ قبول أي format يحتوي صوت + فيديو (مش بس mp4)
                has_video = vcodec and vcodec != 'none'
                has_audio = acodec and acodec != 'none'

                if has_video and has_audio and url:
                    formats_list.append({
                        "resolution": height or 0,
                        "label": f"{height}p" if height else ext.upper(),
                        "url": url
                    })

            # ✅ لو ما لقينا شيء، نجيب أفضل جودة متاحة تلقائياً
            if not formats_list:
                best_url = info.get('url') or ''
                if best_url:
                    formats_list.append({
                        "resolution": 0,
                        "label": "Best Available",
                        "url": best_url
                    })

            formats_list.sort(key=lambda x: x['resolution'], reverse=True)
            return jsonify({"formats": formats_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
