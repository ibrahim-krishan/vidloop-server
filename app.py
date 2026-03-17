@app.route('/get_direct', methods=['GET'])
def get_direct():
    video_url = request.args.get('url')
    format_id = request.args.get('format_id', 'best')

    if not video_url:
        return jsonify({"error": "No URL"}), 400

    video_url = normalize_url(video_url)

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        # 🔥 البحث عن الفورمات المطلوب
        selected_url = None

        for f in info.get('formats', []):
            if f.get('format_id') == format_id:
                selected_url = f.get('url')
                break

        # fallback
        if not selected_url:
            selected_url = info.get('url')

        return jsonify({
            "direct_url": selected_url,
            "title": info.get("title", "video")
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
