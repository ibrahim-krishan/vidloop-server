import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/get_url', methods=['GET'])
def get_url():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL"}), 400

    # ✅ إعدادات خاصة لتيك توك
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        # ✅ هذا هو الحل الرئيسي لتيك توك
        'extractor_args': {
            'tiktok': {
                'app_name': ['trill'],
                'app_version': ['34.1.2'],
                'manifest_app_version': ['2023401020'],
            }
        },
        # ✅ تجاهل أخطاء الـ geo-restriction
        'geo_bypass': True,
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

            # ✅ Fallback: لو ما لقينا شيء خذ أي URL مباشر
            if not formats_list:
                # جرب تاخذ url مباشر من الـ info
                direct = info.get('url')
                if direct:
                    formats_list.append({
                        "resolution": info.get('height', 0),
                        "label": "Best Available",
                        "url": direct
                    })
                else:
                    # ✅ آخر حل: استخدم format selector تلقائي
                    ydl_opts2 = {
                        'quiet': True,
                        'format': 'best',
                        'geo_bypass': True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts2) as ydl2:
                        info2 = ydl2.extract_info(video_url, download=False)
                        best_url = info2.get('url', '')
                        if best_url:
                            formats_list.append({
                                "resolution": info2.get('height', 0),
                                "label": "Best Available",
                                "url": best_url
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
