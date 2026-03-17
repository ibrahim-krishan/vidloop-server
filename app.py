import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/get_url', methods=['GET'])
def get_url():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL"}), 400

    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats_list = []
            for f in info.get('formats', []):
                # نختار فقط روابط الفيديو التي تحتوي على صوت وصورة وتعمل مباشرة
                if f.get('ext') == 'mp4' and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                    formats_list.append({
                        "resolution": f.get('height'),
                        "label": f"{f.get('height')}p (Direct)",
                        "url": f.get('url') # هذا الرابط المباشر
                    })
            
            formats_list.sort(key=lambda x: x['resolution'] if x['resolution'] else 0, reverse=True)
            return jsonify({"formats": formats_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
