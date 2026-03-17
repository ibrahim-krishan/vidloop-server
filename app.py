app.route('/get_direct', methods=['GET'])
def get_direct():
    video_url = request.args.get('url')
    format_id = request.args.get('format_id', 'best')

    if not video_url:
        return jsonify({"error": "No URL"}), 400

    video_url = normalize_url(video_url)

    try:
        # ✅ أضف هذه الخيارات لتجاوز مشاكل YouTube
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],  # ← مهم جداً
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36'
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        selected_url = None
        selected_format = None

        # ✅ البحث بـ format_id أو fallback لأقرب جودة
        for f in info.get('formats', []):
            if f.get('format_id') == format_id:
                selected_url = f.get('url')
                selected_format = f
                break

        # fallback: ابحث عن أفضل فورمات mp4 مدمجة (video+audio)
        if not selected_url:
            for f in info.get('formats', []):
                if (f.get('vcodec') != 'none' and 
                    f.get('acodec') != 'none' and
                    f.get('ext') == 'mp4'):
                    selected_url = f.get('url')
                    break

        # fallback نهائي
        if not selected_url:
            selected_url = info.get('url')

        if not selected_url:
            return jsonify({"error": "لم يتم العثور على رابط مباشر"}), 404

        return jsonify({
            "direct_url": selected_url,
            "title": info.get("title", "video"),
            "ext": selected_format.get('ext', 'mp4') if selected_format else 'mp4'
        })

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        # ✅ أرجع تفاصيل الخطأ للتشخيص
        return jsonify({
            "error": str(e),
            "details": tb.split('\n')[-3]  # السطر المسبب للخطأ
        }), 500
