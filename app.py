@app.route('/get_url', methods=['GET'])
def get_url():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats_list = []
            seen_resolutions = set()

            for f in info.get('formats', []):
                # نركز على الصيغ التي تعمل مباشرة على الأندرويد (mp4)
                # ونقبل الصيغ التي تحتوي فيديو وصوت (مدمجة)
                if f.get('ext') == 'mp4' and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    res = f.get('height')
                    if res and res not in seen_resolutions:
                        seen_resolutions.add(res)
                        formats_list.append({
                            "resolution": res,
                            "label": f"{res}p (HD)" if res >= 720 else f"{res}p",
                            "format_id": f.get('format_id'), # تأكد أن هذا المفتاح يرسل دائماً
                            "url": f.get('url')
                        })

            # إذا كانت القائمة فارغة (لم نجد mp4 مدمج)، نأخذ أفضل صيغة متاحة عامة
            if not formats_list:
                formats_list.append({
                    "resolution": info.get('height') or 0,
                    "label": "Best Quality (Auto)",
                    "format_id": "bestvideo+bestaudio/best",
                    "url": info.get('url')
                })

            formats_list.sort(key=lambda x: x['resolution'], reverse=True)
            return jsonify({"formats": formats_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
