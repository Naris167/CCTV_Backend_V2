1. load JSON from the location of the session ID backend.
2. call a function startValidatingSessionID() it will validate the session ID and return the image from each working cctv.
3. in case of session from json is not working, function startValidatingSessionID() will start to get new session ID and fetch the image by itself.
4. create another function `get_image_HLS()` in the worker.py 
5. create another function `prepare_get_image_HLS()` in the main.py. This function should return dictionary that have cctv id as key and value as a list of images data as btyes. Just like the one from BMA, but this should return exact number of images based on the setting in `img_per_cam`.
6. These 2 functino will scrape image from HLS CCTV
7. have to fetch the cctv id and hls link from database
8. `all_cctv_image_list`, dictionary that have cctv id as key and value as a list of images data as btyes. This will have at least 6 images because 1 was fetched to check the size and other 5 are for check movement. Have to precess this by get the amount of image I want based on the setting in `img_per_cam` setting.
9. Merge the image from 2 sources? Don't know yet, have to check with the model, what type of data it accept.
10. after input data to model. have to get the result and put it back to database.





1/10/2024
my php project


2/10/2024
image scraping repo
Ensure cam id in the database function is treated as string
Add a function to copy database from local to prod
Now the dataabse have 3 more columns is_online is_flooded is_usable. But the script might not be able to handle these columns. Have to check for this later

session ID backend
Organize log files and separate log directory for server and get session id script
Move python script for Rangsit and Ubon to Image Scraping project becuase this project should mainly handle Session ID preparation for Flutter app


3/10/2024
image scraping repo
Migrated cctv general and Rangsit to this project (they were from backend to get session ID)
Changed database method, next will have to fix all the code to handle this
Implemented new database method so now there are only 4 functions in database.py that can be call (fetch, insert, delete, update)
Move HLS scraper to src folder
Rename file to make them more relevant
Update database function can now handle many value in where clause
JSON manager
Update BMA scraper and updateCamInfo with the one from session ID server
Use validate_sessionID and create_sessionID from session ID server
Todo next is to implement the image scraping logic. Now prepare_validate_sessionID_workers function already return dictionary that have cctv id as key and value as a list of images data as btyes (all_cctv_image_list). Have to think next what to do with it.





```python
table = 'cctv_locations_general'
columns = ['Cam_ID', 'Stream_Link_1']
results = retrieve_data(table, columns)



```



























This function only capture one image per call from hls link, but I want it to capture any amount of image based on input. I have to be able specify the interval between each capture as well. It should return a list of image as bytes. Each element in the list should be byte data of each image. Please know that the hls url in this case is the cctv video streaming which mean it have no start or end point. Also if you know, playlist.m3u8 will have a list of video sequence right. So if you try to fetch the same url in a short time, you will always get the same video. So to avoid this, let's say you download one piece of video, it is a piece of video right, so you just slice it into the number of screenshot I want. For the interval, since it is a video, let's say I want an interval of 4 second between each capture and I want 5 images and the video piece in 10 second long. You have to capture 2 screenshot from the first video piece so the first one will happen at first second of the video, the next one will happen in the next 4 second of the video which is around fourth or fifth second of the video, the third screenshot will happen at eigth or nighth second of the video, and after this you will have to wait for the next sequence of video piece, so you can continue the screenshot.


```python
def capture_one_screenshot_from_hls(stream_url):
    """Captures a single frame from an HLS stream and saves it as an image."""

    try:
        ffmpeg_cmd = [
            'ffmpeg', '-i', stream_url, '-vframes', '1',
            '-f', 'image2pipe', '-vcodec', 'png', '-'
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
        return result.stdout

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}")
    except Exception as e:
        raise RuntimeError(f"Error capturing screenshot: {str(e)}")
```









{
  "success": true,
  "duration": "Unknown",
  "bitrate": "Unknown",
  "video_codec": "Unknown",
  "audio_codec": "Unknown",
  "fps": "Unknown",
  "full_output": "ffmpeg version N-116549-g94165d1b79-20240808 Copyright (c) 2000-2024 the FFmpeg developers\n  built with gcc 14.1.0 (crosstool-NG 1.26.0.93_a87bf7f)\n  configuration: --prefix=/ffbuild/prefix --pkg-config-flags=--static --pkg-config=pkg-config --cross-prefix=x86_64-w64-mingw32- --arch=x86_64 --target-os=mingw32 --enable-gpl --enable-version3 --disable-debug --disable-w32threads --enable-pthreads --enable-iconv --enable-zlib --enable-libfreetype --enable-libfribidi --enable-gmp --enable-libxml2 --enable-lzma --enable-fontconfig --enable-libharfbuzz --enable-libvorbis --enable-opencl --disable-libpulse --enable-libvmaf --disable-libxcb --disable-xlib --enable-amf --enable-libaom --enable-libaribb24 --enable-avisynth --enable-chromaprint --enable-libdav1d --enable-libdavs2 --enable-libdvdread --enable-libdvdnav --disable-libfdk-aac --enable-ffnvcodec --enable-cuda-llvm --enable-frei0r --enable-libgme --enable-libkvazaar --enable-libaribcaption --enable-libass --enable-libbluray --enable-libjxl --enable-libmp3lame --enable-libopus --enable-librist --enable-libssh --enable-libtheora --enable-libvpx --enable-libwebp --enable-lv2 --enable-libvpl --enable-openal --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopenh264 --enable-libopenjpeg --enable-libopenmpt --enable-librav1e --enable-librubberband --enable-schannel --enable-sdl2 --enable-libsoxr --enable-libsrt --enable-libsvtav1 --enable-libtwolame --enable-libuavs3d --disable-libdrm --enable-vaapi --enable-libvidstab --enable-vulkan --enable-libshaderc --enable-libplacebo --enable-libvvenc --enable-libx264 --enable-libx265 --enable-libxavs2 --enable-libxvid --enable-libzimg --enable-libzvbi --extra-cflags=-DLIBTWOLAME_STATIC --extra-cxxflags= --extra-libs=-lgomp --extra-ldflags=-pthread --extra-ldexeflags= --cc=x86_64-w64-mingw32-gcc --cxx=x86_64-w64-mingw32-g++ --ar=x86_64-w64-mingw32-gcc-ar --ranlib=x86_64-w64-mingw32-gcc-ranlib --nm=x86_64-w64-mingw32-gcc-nm --extra-version=20240808\n  libavutil      59. 32.100 / 59. 32.100\n  libavcodec     61. 11.100 / 61. 11.100\n  libavformat    61.  5.101 / 61.  5.101\n  libavdevice    61.  2.100 / 61.  2.100\n  libavfilter    10.  2.102 / 10.  2.102\n  libswscale      8.  2.100 /  8.  2.100\n  libswresample   5.  2.100 /  5.  2.100\n  libpostproc    58.  2.100 / 58.  2.100\nSplitting the commandline.\nReading option '-v' ... matched as option 'v' (set logging level) with argument 'debug'.\nReading option '-rtsp_transport' ... matched as AVOption 'rtsp_transport' with argument 'tcp'.\nReading option '-probesize' ... matched as AVOption 'probesize' with argument '32M'.\nReading option '-analyzeduration' ... matched as AVOption 'analyzeduration' with argument '10M'.\nReading option '-i' ... matched as input url with argument 'http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8'.\nReading option '-t' ... matched as option 't' (stop transcoding after specified duration) with argument '5'.\nReading option '-f' ... matched as option 'f' (force container format (auto-detected otherwise)) with argument 'null'.\nReading option '-' ... matched as output url.\nFinished splitting the commandline.\nParsing a group of options: global .\nApplying option v (set logging level) with argument debug.\nSuccessfully parsed a group of options.\nParsing a group of options: input url http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8.\nSuccessfully parsed a group of options.\nOpening an input file: http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8.\n[AVFormatContext @ 0000026ac7fb5840] Opening 'http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8' for reading\n[http @ 0000026ac7fb6bc0] Setting default whitelist 'http,https,tls,rtp,tcp,udp,crypto,httpproxy,data'\n[tcp @ 0000026ac7fbb940] Original list of addresses:\n[tcp @ 0000026ac7fbb940] Address 183.88.214.137 port 1935\n[tcp @ 0000026ac7fbb940] Interleaved list of addresses:\n[tcp @ 0000026ac7fbb940] Address 183.88.214.137 port 1935\n[tcp @ 0000026ac7fbb940] Starting connection attempt to 183.88.214.137 port 1935\n[tcp @ 0000026ac7fbb940] Successfully connected to 183.88.214.137 port 1935\n[http @ 0000026ac7fb6bc0] request: GET /livecctv/cctvp2c003.stream/playlist.m3u8 HTTP/1.1\n\nUser-Agent: Lavf/61.5.101\n\nAccept: */*\n\nRange: bytes=0-\n\nConnection: close\n\nHost: 183.88.214.137:1935\n\nIcy-MetaData: 1\n\n\n\n\n[hls @ 0000026ac7fb5840] Format hls probed with size=2048 and score=100\n[hls @ 0000026ac7fb5840] Skip ('#EXT-X-VERSION:3')\n[hls @ 0000026ac7fb5840] Opening 'http://183.88.214.137:1935/livecctv/cctvp2c003.stream/chunklist_w1265759454.m3u8' for reading\n[tcp @ 0000026ac7fcbd00] Original list of addresses:\n[tcp @ 0000026ac7fcbd00] Address 183.88.214.137 port 1935\n[tcp @ 0000026ac7fcbd00] Interleaved list of addresses:\n[tcp @ 0000026ac7fcbd00] Address 183.88.214.137 port 1935\n[tcp @ 0000026ac7fcbd00] Starting connection attempt to 183.88.214.137 port 1935\n[tcp @ 0000026ac7fcbd00] Successfully connected to 183.88.214.137 port 1935\n[http @ 0000026ac7fc9280] request: GET /livecctv/cctvp2c003.stream/chunklist_w1265759454.m3u8 HTTP/1.1\n\nUser-Agent: Lavf/61.5.101\n\nAccept: */*\n\nRange: bytes=0-\n\nConnection: keep-alive\n\nHost: 183.88.214.137:1935\n\nIcy-MetaData: 1\n\n\n\n\n[hls @ 0000026ac7fb5840] Skip ('#EXT-X-VERSION:3')\n[hls @ 0000026ac7fb5840] Skip ('#EXT-X-DISCONTINUITY-SEQUENCE:0')\n[hls @ 0000026ac7fb5840] HLS request for url 'http://183.88.214.137:1935/livecctv/cctvp2c003.stream/media_w1265759454_3300.ts', offset 0, playlist 0\n[hls @ 0000026ac7fb5840] Opening 'http://183.88.214.137:1935/livecctv/cctvp2c003.stream/media_w1265759454_3300.ts' for reading\n[tcp @ 0000026ac7fcd900] Original list of addresses:\n[tcp @ 0000026ac7fcd900] Address 183.88.214.137 port 1935\n[tcp @ 0000026ac7fcd900] Interleaved list of addresses:\n[tcp @ 0000026ac7fcd900] Address 183.88.214.137 port 1935\n[tcp @ 0000026ac7fcd900] Starting connection attempt to 183.88.214.137 port 1935\n[tcp @ 0000026ac7fcd900] Successfully connected to 183.88.214.137 port 1935\n[http @ 0000026ac7fcd800] request: GET /livecctv/cctvp2c003.stream/media_w1265759454_3300.ts HTTP/1.1\n\nUser-Agent: Lavf/61.5.101\n\nAccept: */*\n\nRange: bytes=0-\n\nConnection: keep-alive\n\nHost: 183.88.214.137:1935\n\nIcy-MetaData: 1\n\n\n\n\n[hls @ 0000026ac7fb5840] HLS request for url 'http://183.88.214.137:1935/livecctv/cctvp2c003.stream/media_w1265759454_3301.ts', offset 0, playlist 0\n[hls @ 0000026ac7fb5840] Opening 'http://183.88.214.137:1935/livecctv/cctvp2c003.stream/media_w1265759454_3301.ts' for reading\n[tcp @ 0000026ac7ff38c0] Original list of addresses:\n[tcp @ 0000026ac7ff38c0] Address 183.88.214.137 port 1935\n[tcp @ 0000026ac7ff38c0] Interleaved list of addresses:\n[tcp @ 0000026ac7ff38c0] Address 183.88.214.137 port 1935\n[tcp @ 0000026ac7ff38c0] Starting connection attempt to 183.88.214.137 port 1935\n[tcp @ 0000026ac7ff38c0] Successfully connected to 183.88.214.137 port 1935\n[http @ 0000026ac7fcdc00] request: GET /livecctv/cctvp2c003.stream/media_w1265759454_3301.ts HTTP/1.1\n\nUser-Agent: Lavf/61.5.101\n\nAccept: */*\n\nRange: bytes=0-\n\nConnection: keep-alive\n\nHost: 183.88.214.137:1935\n\nIcy-MetaData: 1\n\n\n\n\nFormat mpegts probed with size=2048 and score=50\n[mpegts @ 0000026ac7fcd540] stream=0 stream_type=15 pid=102 prog_reg_desc=\n[mpegts @ 0000026ac7fcd540] stream=1 stream_type=1b pid=100 prog_reg_desc=\nOption rtsp_transport not found.\nError opening input file http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8.\nError opening input files: Option not found\n[AVIOContext @ 0000026ac7fcd9c0] Statistics: 40443 bytes read, 0 seeks\n[AVIOContext @ 0000026ac7ffba00] Statistics: 0 bytes read, 0 seeks\n[AVIOContext @ 0000026ac7fcbe00] Statistics: 229 bytes read, 0 seeks\n[AVIOContext @ 0000026ac7fbd5c0] Statistics: 130 bytes read, 0 seeks\n"
}





{
  "success": true,
  "duration": "Unknown",
  "bitrate": "Unknown",
  "video_codec": "Unknown",
  "audio_codec": "Unknown",
  "fps": "Unknown",
  "full_output": "ffmpeg version N-116549-g94165d1b79-20240808 Copyright (c) 2000-2024 the FFmpeg developers\n  built with gcc 14.1.0 (crosstool-NG 1.26.0.93_a87bf7f)\n  configuration: --prefix=/ffbuild/prefix --pkg-config-flags=--static --pkg-config=pkg-config --cross-prefix=x86_64-w64-mingw32- --arch=x86_64 --target-os=mingw32 --enable-gpl --enable-version3 --disable-debug --disable-w32threads --enable-pthreads --enable-iconv --enable-zlib --enable-libfreetype --enable-libfribidi --enable-gmp --enable-libxml2 --enable-lzma --enable-fontconfig --enable-libharfbuzz --enable-libvorbis --enable-opencl --disable-libpulse --enable-libvmaf --disable-libxcb --disable-xlib --enable-amf --enable-libaom --enable-libaribb24 --enable-avisynth --enable-chromaprint --enable-libdav1d --enable-libdavs2 --enable-libdvdread --enable-libdvdnav --disable-libfdk-aac --enable-ffnvcodec --enable-cuda-llvm --enable-frei0r --enable-libgme --enable-libkvazaar --enable-libaribcaption --enable-libass --enable-libbluray --enable-libjxl --enable-libmp3lame --enable-libopus --enable-librist --enable-libssh --enable-libtheora --enable-libvpx --enable-libwebp --enable-lv2 --enable-libvpl --enable-openal --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopenh264 --enable-libopenjpeg --enable-libopenmpt --enable-librav1e --enable-librubberband --enable-schannel --enable-sdl2 --enable-libsoxr --enable-libsrt --enable-libsvtav1 --enable-libtwolame --enable-libuavs3d --disable-libdrm --enable-vaapi --enable-libvidstab --enable-vulkan --enable-libshaderc --enable-libplacebo --enable-libvvenc --enable-libx264 --enable-libx265 --enable-libxavs2 --enable-libxvid --enable-libzimg --enable-libzvbi --extra-cflags=-DLIBTWOLAME_STATIC --extra-cxxflags= --extra-libs=-lgomp --extra-ldflags=-pthread --extra-ldexeflags= --cc=x86_64-w64-mingw32-gcc --cxx=x86_64-w64-mingw32-g++ --ar=x86_64-w64-mingw32-gcc-ar --ranlib=x86_64-w64-mingw32-gcc-ranlib --nm=x86_64-w64-mingw32-gcc-nm --extra-version=20240808\n  libavutil      59. 32.100 / 59. 32.100\n  libavcodec     61. 11.100 / 61. 11.100\n  libavformat    61.  5.101 / 61.  5.101\n  libavdevice    61.  2.100 / 61.  2.100\n  libavfilter    10.  2.102 / 10.  2.102\n  libswscale      8.  2.100 /  8.  2.100\n  libswresample   5.  2.100 /  5.  2.100\n  libpostproc    58.  2.100 / 58.  2.100\nSplitting the commandline.\nReading option '-v' ... matched as option 'v' (set logging level) with argument 'debug'.\nReading option '-rtsp_transport' ... matched as AVOption 'rtsp_transport' with argument 'tcp'.\nReading option '-probesize' ... matched as AVOption 'probesize' with argument '32M'.\nReading option '-analyzeduration' ... matched as AVOption 'analyzeduration' with argument '10M'.\nReading option '-i' ... matched as input url with argument 'https://camerai1.iticfoundation.org/hls/pty71.m3u8'.\nReading option '-t' ... matched as option 't' (stop transcoding after specified duration) with argument '5'.\nReading option '-f' ... matched as option 'f' (force container format (auto-detected otherwise)) with argument 'null'.\nReading option '-' ... matched as output url.\nFinished splitting the commandline.\nParsing a group of options: global .\nApplying option v (set logging level) with argument debug.\nSuccessfully parsed a group of options.\nParsing a group of options: input url https://camerai1.iticfoundation.org/hls/pty71.m3u8.\nSuccessfully parsed a group of options.\nOpening an input file: https://camerai1.iticfoundation.org/hls/pty71.m3u8.\n[AVFormatContext @ 000001be8fd56100] Opening 'https://camerai1.iticfoundation.org/hls/pty71.m3u8' for reading\n[https @ 000001be8fd08840] Setting default whitelist 'http,https,tls,rtp,tcp,udp,crypto,httpproxy'\n[tcp @ 000001be8fd5b3c0] Original list of addresses:\n[tcp @ 000001be8fd5b3c0] Address 203.150.202.78 port 443\n[tcp @ 000001be8fd5b3c0] Interleaved list of addresses:\n[tcp @ 000001be8fd5b3c0] Address 203.150.202.78 port 443\n[tcp @ 000001be8fd5b3c0] Starting connection attempt to 203.150.202.78 port 443\n[tcp @ 000001be8fd5b3c0] Successfully connected to 203.150.202.78 port 443\n[https @ 000001be8fd08840] request: GET /hls/pty71.m3u8 HTTP/1.1\n\nUser-Agent: Lavf/61.5.101\n\nAccept: */*\n\nRange: bytes=0-\n\nConnection: close\n\nHost: camerai1.iticfoundation.org\n\nIcy-MetaData: 1\n\n\n\n\n[tls @ 000001be8fd5b100] Server closed the connection\nmime type is not rfc8216 compliant\n[hls @ 000001be8fd56100] Format hls probed with size=2048 and score=100\n[hls @ 000001be8fd56100] Skip ('#EXT-X-VERSION:3')\n[hls @ 000001be8fd56100] HLS request for url 'https://camerai1.iticfoundation.org/hls/pty712846.ts', offset 0, playlist 0\n[hls @ 000001be8fd56100] Opening 'https://camerai1.iticfoundation.org/hls/pty712846.ts' for reading\n[tcp @ 000001be8fd9bf40] Original list of addresses:\n[tcp @ 000001be8fd9bf40] Address 203.150.202.78 port 443\n[tcp @ 000001be8fd9bf40] Interleaved list of addresses:\n[tcp @ 000001be8fd9bf40] Address 203.150.202.78 port 443\n[tcp @ 000001be8fd9bf40] Starting connection attempt to 203.150.202.78 port 443\n[tcp @ 000001be8fd9bf40] Successfully connected to 203.150.202.78 port 443\n[https @ 000001be8fd080c0] request: GET /hls/pty712846.ts HTTP/1.1\n\nUser-Agent: Lavf/61.5.101\n\nAccept: */*\n\nRange: bytes=0-\n\nConnection: keep-alive\n\nHost: camerai1.iticfoundation.org\n\nIcy-MetaData: 1\n\n\n\n\n[hls @ 000001be8fd56100] HLS request for url 'https://camerai1.iticfoundation.org/hls/pty712847.ts', offset 0, playlist 0\n[hls @ 000001be8fd56100] Opening 'https://camerai1.iticfoundation.org/hls/pty712847.ts' for reading\n[tcp @ 000001be8fd76c40] Original list of addresses:\n[tcp @ 000001be8fd76c40] Address 203.150.202.78 port 443\n[tcp @ 000001be8fd76c40] Interleaved list of addresses:\n[tcp @ 000001be8fd76c40] Address 203.150.202.78 port 443\n[tcp @ 000001be8fd76c40] Starting connection attempt to 203.150.202.78 port 443\n[tcp @ 000001be8fd76c40] Successfully connected to 203.150.202.78 port 443\n[tls @ 000001be8fd76980] Received incomplete handshake, need more data\n[https @ 000001be8fd08780] request: GET /hls/pty712847.ts HTTP/1.1\n\nUser-Agent: Lavf/61.5.101\n\nAccept: */*\n\nRange: bytes=0-\n\nConnection: keep-alive\n\nHost: camerai1.iticfoundation.org\n\nIcy-MetaData: 1\n\n\n\n\nFormat mpegts probed with size=2048 and score=50\n[mpegts @ 000001be8fd74c00] stream=0 stream_type=1b pid=100 prog_reg_desc=\n[mpegts @ 000001be8fd74c00] stream=1 stream_type=6 pid=101 prog_reg_desc=\nOption rtsp_transport not found.\nError opening input file https://camerai1.iticfoundation.org/hls/pty71.m3u8.\nError opening input files: Option not found\n[AVIOContext @ 000001be8fdadc80] Statistics: 48838 bytes read, 0 seeks\n[AVIOContext @ 000001be8fd88880] Statistics: 0 bytes read, 0 seeks\n[AVIOContext @ 000001be8fd78900] Statistics: 138 bytes read, 0 seeks\n"
}


