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





So in this case, can you create a python function that accept the following arguemnts
1. HLS link
2. Number of image to capture
3. Interval between each capture in second

This function should just download the video from HLS link segment by segment and capture the image from it. Each link will have difference length of the video segment. For example, if the segment video have a length of 10 second, and I input the number to capture 8 image with interval of 2 seconds, the function should perform the following action.
1. it should first download only one segment video
2. detect theh lenght of this segment
3. Let's say it detected a length of 10 seconds for this segment piece, it will capture the image from this segment video at the first second.
4. Then the program should move (or basically skip) to next 2 second of the video segment and do the capture again.
5. If there is not enough length left to move further, the program should download the next segment from the HLS link and do the same thing from step 1
6. Make sure the program can keep track of which segment it currently working on and which is the next.
7. Each capture happen, the program should record the capture time also by putting it in a list
8. Each captured image, you can put it in the list too. So this mean that every index of every item in a list of image and a list of capture time should be match. Meaning, if there are 10 images in a list, there should be 10 date time object in a list of capture time too. And the first index of capture time list should be the capture time of the first image in the image list.
9. This function will return both image list and capture time list.
10. another case to handle is that, let's say if the segment of a video have a length of 10 seconds, and I input the interval for 30 second. In this case, as the capture interval is longer than the length of the segment, the program should download the first segment and capture it at first second. Next, it will wait for 30 seconds before it perform the capture again. However, this can be triggy because we don't actually know when the content in HLS link will be update and even it is already update, if we just only wait 30 seconds and download the other segment after waiting, we might end up capturing the next segment from the last one we just capture. This will result in just 10 seconds interval based on the real video. To aviod this problem, you will still keep track of each following segment after the first one that we captured. If the first segment have a length of 10 seconds, the second one have a length of 8 seconds, the third one have a length of 7 seconds, and the fourth one have a length of 10 seconds. The first capture should happen at the first second of the first segment, and the next one should happen at the fourth segment piece at the fifth second of it. This is because the interval is 30 second, the first capture happen at zero second of the first segment, to know when and where to capture the next image, we will wait for the next segment to come (the program should check and keep track) and sum up the length of each segment. In this case, 10 + 8 + 7 + 10 = 35, so the next capture should happen at the fourth segment piece at the fifth second of it.















Now I am using the function from threading module to create multiple thread. They looks something like this. Can you do the same thing for Multiprocessing module? 

```py
semaphore = Semaphore(80)
run_threaded(scrape_image_HLS, semaphore, ...)

def run_threaded(func, semaphore, *args):
    threads = []
    for arg in args:
        thread = Thread(target=func, args=(semaphore, *arg))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
```


Can you create a function that take another function as argument, and any amount of other args in python? This function should run the given function using Multiprocessing module in python and it also need to input the value from paremeter into the given function.

Here is the I have this function that accept the following argument. I want to run this using Multiprocessing module.
```py
def scrape_image_HLS(semaphore: Semaphore,
                     camera_id: str,
                     HLS_Link: str,
                     image_result: List[Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]]],
                     working_cctv: Dict[str, str],
                     unresponsive_cctv: Dict[str, str],
                     interval: float,
                     target_image_count: int,
                     timeout: float,
                     max_retries: int
                     ) -> None:
    with semaphore:
        try:
            logger.info(f"[SCRAPER-HLS] Starting capturing for CCTV {camera_id}")
            
            image_png, image_time = capture_screenshots(camera_id, HLS_Link, target_image_count, interval, max_retries, timeout)
                    
            logger.info(f"[SCRAPER-HLS] CCTV {camera_id} capture complete. Total images captured: {len(image_png)}/{target_image_count}")
            with cctv_working_lock.gen_wlock():
                working_cctv[camera_id] = HLS_Link
                image_result.append((camera_id, image_png, image_time))
            
        except Exception as e:
            logger.error(f"[SCRAPER-HLS] Error scraping camera {camera_id}: {str(e)}")
            with cctv_unresponsive_lock.gen_wlock():
                unresponsive_cctv[camera_id] = HLS_Link
        finally:
            semaphore.release()
```


The function that I want you to create might looks something like this
```py
def run_multiprocessing(func, *args)
```

Also, make this function to be able to work with the shared resource. In this case, there are 3 shared resources:
1. image_result: List[Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]]]
2. working_cctv: Dict[str, str]
3. unresponsive_cctv: Dict[str, str]





Can you conver this chunk of code into class. This class should be about multiprocessing. This class should accept "logger" which is the custom one that has been setup and define outside this class. It also have to accept a function `capture_screenshots` and `scrape_image_HLS` which will be used to run by multiprocessing. I have no idea how this class should be, but it should be easy to use, I can just call it, input a function and arguments and it should work and return the result like this. Btw, it is VERY IMPORTANT that you keep the import machanism of cv2 the same. This is the part that you cannot change. If you want to change it, you have to make sure that the import will only be call in the fork process, not the main one 

```py
import concurrent.futures
from typing import Callable, List, Tuple, Dict, Any, Optional
from datetime import datetime
import time
import random
import math

from utils.log_config import logger, log_setup

# Global variable to hold the cv2 module
cv2 = None

def safe_import_cv2():
    global cv2
    if cv2 is None:
        import cv2 as cv2_imported
        cv2 = cv2_imported


# Ensure cv2 is not imported in the main process
def scrape_image_HLS(camera_id: str, HLS_Link: str, 
                    interval: float, target_image_count: int, 
                    timeout: float, max_retries: int) -> Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]] | None:

    # Import cv2 here
    safe_import_cv2()
    def capture_screenshots(
        camera_id: str,
        stream_url: str,
        num_images: int = 1,
        interval: float = 1,
        max_retries: int = 3,
        timeout: float = 30
    ) -> Tuple[Tuple[bytes, ...], Tuple[datetime, ...]]:
        
        logger.info(f"[{camera_id}] Connecting...")

        last_capture_time: Optional[float] = None
        image_data: List[bytes] = []
        capture_times: List[datetime] = []
        retries: int = 0
        
        while len(image_data) < num_images and retries < max_retries:
            try:
                cap = cv2.VideoCapture(stream_url)
                if not cap.isOpened():
                    raise Exception(f"Unable to open video stream")

                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps <= 0:
                    fps = 30
                    logger.warning(f"[{camera_id}] Unable to determine stream FPS, using {fps} as default")
                
                start_time = time.time()

                while len(image_data) < num_images:
                    current_time = time.time()
                    
                    if current_time - start_time > timeout:
                        logger.warning(f"[{camera_id}] Timeout reached. Reconnecting...")
                        break

                    # Check if enough time has passed since the last capture
                    if last_capture_time is None or (current_time - last_capture_time) >= interval:
                        # Skip frames to reach the desired interval
                        frames_to_skip = int(fps * interval)
                        for _ in range(frames_to_skip):
                            cap.grab()

                        ret, frame = cap.read()
                        if not ret:
                            logger.warning(f"[{camera_id}] Error reading frame, reconnecting...")
                            break
                        
                        # Convert frame to bytes
                        _, buffer = cv2.imencode('.png', frame)
                        image_bytes = buffer.tobytes()

                        # Check image validity
                        if len(image_bytes) <= 10000:
                            logger.warning(f"[{camera_id}] Image size less than 10 Kb, retrying...")
                            break
                        
                        # Store image bytes and capture time
                        image_data.append(image_bytes)
                        capture_times.append(datetime.now())
                        
                        last_capture_time = current_time
                        print(f"[{camera_id}] Screenshot {len(image_data)}/{num_images} captured")
                    else:
                        # Wait for the remaining interval
                        wait_time = interval - (current_time - last_capture_time)
                        if wait_time > 0:
                            time.sleep(min(wait_time, timeout - (current_time - start_time)))

                cap.release()

                if len(image_data) == num_images:
                    break
                else:
                    retries += 1
                    logger.warning(f"[{camera_id}] Retry {retries}/{max_retries}")
                    time.sleep(1)

            except Exception as e:
                logger.error(f"[{camera_id}] Error occurred - {str(e)}")
                retries += 1
                logger.warning(f"[{camera_id}] Retry {retries}/{max_retries}")
                time.sleep(1)

        if len(image_data) <= 0:
            raise Exception(f"Unable to capture any screenshots after {max_retries} retries")

        if len(image_data) < num_images:
            logger.warning(f"[{camera_id}] Captured only {len(image_data)}/{num_images} screenshots after {max_retries} retries")
        
        if len(image_data) >= num_images:
            logger.info(f"[{camera_id}] Captured {len(image_data)}/{num_images} screenshots")
        
        return tuple(image_data), tuple(capture_times)
    try:
        # Return a tuple of (camera_id, image_data, timestamps)
        logger.info(f"[SCRAPER-HLS] Starting capturing for CCTV {camera_id}")
            
        image_png, image_time = capture_screenshots(camera_id, HLS_Link, target_image_count, interval, max_retries, timeout)
                
        logger.info(f"[SCRAPER-HLS] CCTV {camera_id} capture complete. Total images captured: {len(image_png)}/{target_image_count}")
        return camera_id, image_png, image_time
    except Exception as e:
        # Return None to indicate failure
        logger.error(f"[SCRAPER-HLS] Error scraping camera {camera_id}: {str(e)}")
        return None



def worker_func(func: Callable, camera_id: str, url: str, kwargs: Dict[str, Any]) -> Tuple[str, Any]:
    # Import cv2 here, after the process has been forked
    safe_import_cv2()
    result = func(camera_id, url, **kwargs)
    return camera_id, result

def run_multiprocessing(func: Callable, 
                        max_concurrent: int,
                        working_cctv: Dict[str, str],
                        **kwargs: Any) -> Dict[str, Any]:
    
    # Determine the number of pools and workers per pool
    num_pools = math.ceil(max_concurrent / 60)  # 60 workers per pool to stay within Windows limits
    workers_per_pool = min(60, max(1, max_concurrent // num_pools))
    
    # Create process pools
    pools = [concurrent.futures.ProcessPoolExecutor(max_workers=workers_per_pool) for _ in range(num_pools)]
    
    # Distribute work among pools
    futures = []
    for i, (camera_id, url) in enumerate(working_cctv.items()):
        pool = pools[i % num_pools]
        futures.append(pool.submit(worker_func, func, camera_id, url, kwargs))
    
    # Collect results
    all_results = []
    for future in concurrent.futures.as_completed(futures):
        try:
            all_results.append(future.result())
        except Exception as e:
            print(f"An error occurred: {str(e)}")
    
    # Process results
    image_result = []
    updated_working_cctv = {}
    unresponsive_cctv = {}

    for camera_id, result in all_results:
        if result is not None:
            image_result.append(result)
            updated_working_cctv[camera_id] = working_cctv[camera_id]
        else:
            unresponsive_cctv[camera_id] = working_cctv[camera_id]

    # Shutdown all pools
    for pool in pools:
        pool.shutdown()

    return {
        "image_result": image_result,
        "working_cctv": updated_working_cctv,
        "unresponsive_cctv": unresponsive_cctv
    }
```

This is how I use it right now. Just so you have understanding about it.
```py
if __name__ == "__main__":
    # Configuration and setup
    log_setup("./logs/imageScraper","TestMultiprocessor")
    config = {
        'interval': 1.0,
        'target_image_count': 5,  # Reduced for faster testing
        'timeout': 30.0,
        'max_retries': 3
    }

    working_cctv: Dict[str, str] = {
        "DOH-PER-9-004": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase9/PER_9_004.stream/playlist.m3u8",
        "ITICM_BMAMI0277": "https://camerai1.iticfoundation.org/hls/pty76.m3u8"
    }

    print(f"Starting scraping for {len(working_cctv)} CCTVs...")
    start_time = time.time()

    # Run the multiprocessing function
    results = run_multiprocessing(
        scrape_image_HLS,
        80,  # Desired number of concurrent processes
        working_cctv,
        **config
    )

    end_time = time.time()
    total_time = end_time - start_time

    # Process the results
    print(f"\nScraping completed in {total_time:.2f} seconds")
    print(f"Successfully scraped {len(results['image_result'])} cameras")
    print(f"Working CCTV: {len(results['working_cctv'])}")
    print(f"Unresponsive CCTV: {len(results['unresponsive_cctv'])}")

    # Calculate and print statistics
    success_rate = len(results['working_cctv']) / len(working_cctv) * 100
    print(f"\nSuccess rate: {success_rate:.2f}%")
    print(f"Average time per camera: {total_time / len(working_cctv):.4f} seconds")

```



















So actually the logging that I just asked you about this this classes. This is the improved version of MultiprocessingImageScraper that also have ability to send logggin information from each process back to the main process for centralized logging. The logging machanism in this code work well. However, there are a lot of error when this code run under high concurrency because the manual multiprocessing implementation is not that good.
```python
class LoggingProcess(multiprocessing.Process):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def run(self):
        root_logger = logging.getLogger()
        root_logger.handlers = []
        handler = QueueHandler(self.log_queue)
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.DEBUG)
        self.run_process()

    def run_process(self):
        pass

class MultiprocessingImageScraper:
    def __init__(self, logger):
        self.logger = logger
        self.log_queue = multiprocessing.Queue()
        self.queue_listener = QueueListener(self.log_queue, *logger.handlers)

    def start_logging(self):
        self.queue_listener.start()

    def stop_logging(self):
        self.queue_listener.stop()

    class WorkerProcess(LoggingProcess):
        def __init__(self, log_queue, func, camera_id, url, kwargs):
            super().__init__(log_queue)
            self.func = func
            self.camera_id = camera_id
            self.url = url
            self.kwargs = kwargs
            self.result = None

        def run_process(self):
            safe_import_cv2()
            self.result = self.func(self.camera_id, self.url, **self.kwargs)

    def run_multiprocessing(self, func: Callable, 
                            max_concurrent: int,
                            working_cctv: Dict[str, str],
                            **kwargs: Any) -> Dict[str, Any]:
        
        self.start_logging()

        all_results = []
        processes = []

        for camera_id, url in working_cctv.items():
            process = self.WorkerProcess(self.log_queue, func, camera_id, url, kwargs)
            processes.append(process)
            process.start()

            if len(processes) >= max_concurrent:
                for p in processes:
                    p.join()
                    if p.result is not None:
                        all_results.append((p.camera_id, p.result))
                processes = []

        # Handle any remaining processes
        for p in processes:
            p.join()
            if p.result is not None:
                all_results.append((p.camera_id, p.result))

        image_result = []
        updated_working_cctv = {}
        unresponsive_cctv = {}

        for camera_id, result in all_results:
            if result is not None:
                image_result.append(result)
                updated_working_cctv[camera_id] = working_cctv[camera_id]
            else:
                unresponsive_cctv[camera_id] = working_cctv[camera_id]

        self.stop_logging()

        return {
            "image_result": image_result,
            "working_cctv": updated_working_cctv,
            "unresponsive_cctv": unresponsive_cctv
        }
```


But in this older version, the code work very well under high concurrency because I used `concurrent.futures.ProcessPoolExecutor`. However, it don't have ability to keep track of any logging like the new one I showed you above. I want you to use the below code as a base. You may change some part in it. and you have to implement logging like the code I showed you above. You might have to make the class `MultiprocessingImageScraper` inherit from `LoggingProcess` and `LoggingProcess` might have to inherit from, i don't know, may be things like concurrent.futures or ProcessPoolExecutor. Can you help me with this? My idea on how to implement it might not correct so can you please help me correct it before you implement this?

```python
class MultiprocessingImageScraper:
    def __init__(self, logger):
        self.logger = logger

    def worker_func(self, func: Callable, camera_id: str, url: str, kwargs: Dict[str, Any]) -> Tuple[str, Any]:
        safe_import_cv2()
        result = func(camera_id, url, **kwargs)
        return camera_id, result

    def run_multiprocessing(self, func: Callable, 
                            max_concurrent: int,
                            working_cctv: Dict[str, str],
                            **kwargs: Any) -> Dict[str, Any]:
        
        num_pools = math.ceil(max_concurrent / 60)
        workers_per_pool = min(60, max(1, max_concurrent // num_pools))
        
        pools = [concurrent.futures.ProcessPoolExecutor(max_workers=workers_per_pool) for _ in range(num_pools)]
        
        futures = []
        for i, (camera_id, url) in enumerate(working_cctv.items()):
            pool = pools[i % num_pools]
            futures.append(pool.submit(self.worker_func, func, camera_id, url, kwargs))
        
        all_results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                all_results.append(future.result())
            except Exception as e:
                self.logger.error(f"An error occurred: {str(e)}")
        
        image_result = []
        updated_working_cctv = {}
        unresponsive_cctv = {}

        for camera_id, result in all_results:
            if result is not None:
                image_result.append(result)
                updated_working_cctv[camera_id] = working_cctv[camera_id]
            else:
                unresponsive_cctv[camera_id] = working_cctv[camera_id]

        for pool in pools:
            pool.shutdown()

        return {
            "image_result": image_result,
            "working_cctv": updated_working_cctv,
            "unresponsive_cctv": unresponsive_cctv
        }
```






[DATABASE-UPDATE-QUERY] UPDATE cctv_locations_preprocessing SET cam_group = %s WHERE cam_id::text = ANY(%s::text[])
[DATABASE-UPDATE-PARAMS] [('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '14', '16', '17', '18', '13', '19', '20', '21', '13', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '19', '33', '34', '35', '36', '37', '38', '39', '40', '41', '36', '42', '43', '44', '33', '45', '46', '47', '48', '49', '25', '50', '51', '52', '53', '29', '54', '55', '32', '56', '57', '58', '32', '59', '60', '59', '61', '62', '63', '64', '65', '66', '42', '67', '68', '69', '70', '71', '34', '23', '13', '72', '73', '74', '75', '76', '77', '78', '79', '13', '80', '31', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '42', '92', '93', '65', '94', '95', '96', '25', '97', '98', '99', '100', '101', '102', '103', '104', '105', '106', '23', '65', '1', '1', '45', '107', '108', '109', '42', '110', '40', '111', '112', '65', '113', '114', '115', '116', '13', '117', '92', '118', '119', '114', '120', '121', '14', '122', '123', '106', '124', '125', '126', '127', '4', '57', '60', '127', '128', '129', '73', '130', '93', '131', '34', '106', '120', '132', '13', '81', '133', '134', '65', '135', '136', '137', '19', '52', '138', '139', '140', '141', '142', '143', '144', '20', '145', '146', '147', '148', '149', '150', '151', '152', '153', '61', '65', '154', '57', '155', '77', '156', '92', '157', '142', '158', '37', '159', '160', '106', '161', '162', '44', '21', '163', '164', '123', '165', '166', '167', '72', '0', '168', '169', '170', '171', '172', '173', '174', '65', '171', '175', '149', '8', '176', '47', '177', '13', '64', '178', '179', '83', '33', '180', '181', '142', '182', '14', '183', '93', '86', '16', '110', '65', '184', '76', '126', '22', '35', '185', '146', '186', '81', '187', '112', '67', '188', '189', '1', '22', '190', '14', '1', '191', '192', '1', '174', '193', '194', '193', '63', '133', '122', '105', '195', '179', '196', '197', '49', '198', '87', '199', '200', '8', '66', '160', '122', '156', '129', '185', '155', '161', '105', '120', '40', '70', '114', '201', '195', '156', '103', '202', '165', '203', '204', '205', '74', '135', '40', '40', '36', '117', '105', '195', '206', '114', '207', '208', '209', '210', '164', '35', '211', '194', '212', '41', '20', '213', '153', '214', '215', '216', '200', '217', '37', '218', '13', '194', '42', '219', '127', '220', '5', '121', '123', '183', '13', '5', '17', '221', '97', '133', '222', '106', '223', '56', '26', '142', '186', '22', '201', '26', '224', '179', '225', '226', '227', '183', '29', '228', '229', '63', '230', '66', '42', '188', '223', '18', '231', '226', '81', '111', '232', '233', '217', '234', '139', '235', '216', '236', '25', '237', '238', '173', '239', '240', '241', '242', '172', '159', '81', '40', '18', '243', '149', '244', '88', '44', '212', '11', '133', '29', '78', '245', '77', '246', '42', '209', '28', '39', '247', '9', '233', '0', '248', '108', '249', '11', '118', '239', '63', '250', '93', '39', '116', '23', '56', '251', '252', '141', '253', '208', '107', '254', '255', '256', '130', '257', '10', '258', '259', '0', '170', '235', '260', '203', '39', '261', '23', '262', '263', '145', '103', '264', '32', '265', '81', '119', '177', '129', '266', '149', '110', '267', '268', '43', '57', '269', '270', '151', '256', '62', '124', '137', '271', '22', '68', '230', '131', '272', '201', '40', '205', '104', '216', '268', '75', '36', '16', '262', '85', '221', '273', '262', '16', '274', '79', '275', '239', '119', '84', '276', '126', '277', '34', '220', '212', '66', '171', '176', '278', '118', '5', '25', '178', '279', '36', '140', '149', '120', '129', '280', '202', '161', '181', '181', '281', '45', '282', '44', '11', '236', '197', '132', '283', '284', '239', '285', '117', '175', '279', '100', '241', '249', '156', '187', '40', '55', '174', '85', '55', '67', '210', '195', '20', '214', '286', '50', '187', '221', '285', '93', '287', '174', '196', '288', '48', '289', '290', '262', '162', '182', '73', '167', '54', '14', '153', '122', '114', '12', '27', '103', '253', '291', '55', '13', '119', '39', '250', '271', '266', '292', '67', '293', '153', '56', '149', '112', '65', '169', '169', '55', '282', '294', '295', '155', '244', '296', '140', '45', '97', '152', '297', '298', '299', '70', '300', '164', '152', '297', '38', '301', '294', '302', '255', '161', '104', '272', '303', '265', '11', '134', '120', '301', '304', '153', '42', '169', '239', '97', '28', '221', '162', '13', '115', '15', '197', '132', '221', '91', '85', '258', '35', '297', '141', '262', '158', '55', '1', '114', '173', '305', '276', '306', '307', '243', '308', '186', '211', '26', '20', '40', '43', '172', '204', '22', '38', '226', '129', '309', '141', '40', '300', '76', '15', '71', '310', '311', '102', '181', '249', '219', '15', '99', '167', '147', '117', '120', '35', '126', '231', '110', '22', '259', ['602', '77', '1648', '1299', '1725', '1469', '1296', '1336', '1131', '211', '1526', '1477', '1445', '1379', '1708', '1709', '1712', '96', '1178', '1564', '1737', '51', '1781', '1483', '1154', '1184', '20', '1744', '1509', '500', '202', '1348', '1071', '1291', '1087', '1368', '997', '1273', '1641', '7', '1130', '47', '1643', '113', '1361', '163', '1654', '999', '1356', '615', '1658', '1510', '1246', '1726', '11', '217', '639', '127', '1783', '135', '1653', '63', '170', '1786', '1533', '1098', '1527', '1320', '1656', '239', '196', '240', '139', '1220', '1385', '257', '1592', '1662', '1051', '1631', '191', '1777', '1434', '1790', '481', '19', '394', '1088', '1070', '154', '201', '907', '1530', '130', '1734', '1161', '1249', '105', '1796', '1168', '172', '156', '87', '526', '147', '1066', '572', '1618', '1073', '75', '609', '309', '1263', '1329', '1298', '414', '1522', '125', '1317', '1558', '159', '1479', '1769', '26', '1539', '1650', '242', '926', '1395', '185', '184', '648', '1628', '152', '1690', '76', '1103', '370', '222', '1438', '68', '1314', '1514', '229', '1475', '1164', '1795', '612', '1429', '1604', '1490', '1332', '1482', '1713', '93', '112', '1788', '1775', '1693', '1127', '599', '1724', '318', '197', '597', '1752', '1575', '1069', '259', '1466', '1687', '1569', '1442', '569', '619', '1163', '1681', '405', '1086', '1261', '232', '947', '1499', '1124', '1406', '109', '209', '1756', '1545', '389', '1665', '1670', '1505', '1078', '528', '176', '1313', '1360', '939', '1441', '1710', '1231', '138', '913', '1669', '1529', '1453', '248', '1397', '610', '1297', '386', '1200', '1194', '1780', '1714', '1755', '1787', '1174', '616', '576', '1696', '1460', '1408', '255', '1481', '1401', '1635', '603', '1157', '1136', '562', '1552', '1735', '1383', '1388', '1260', '630', '253', '1083', '1121', '1746', '1728', '1719', '1162', '256', '991', '1716', '173', '1274', '1327', '114', '388', '1557', '1707', '1555', '310', '527', '98', '37', '227', '1358', '320', '1387', '1185', '1122', '1125', '529', '1587', '1691', '1206', '1089', '1630', '1067', '1322', '79', '1347', '1158', '432', '78', '250', '1286', '80', '1598', '32', '1616', '1085', '1431', '1753', '92', '1757', '1677', '1717', '1596', '1534', '216', '1169', '146', '1695', '1784', '1120', '1518', '1715', '94', '1398', '45', '1076', '1405', '1791', '1418', '1478', '1502', '1264', '354', '1027', '1678', '390', '1101', '1244', '254', '169', '181', '206', '155', '231', '1525', '1566', '1152', '1339', '1159', '1679', '1304', '1523', '1723', '225', '1747', '1763', '1461', '1655', '221', '1660', '244', '162', '1421', '1729', '1230', '218', '953', '195', '439', '215', '46', '1319', '1165', '1659', '182', '1590', '598', '1038', '335', '1480', '111', '1548', '1736', '363', '1179', '102', '124', '1484', '1172', '1443', '1498', '1192', '1255', '387', '1593', '1182', '1081', '942', '1741', '477', '1625', '289', '1439', '1549', '1108', '1353', '915', '1433', '1063', '1369', '73', '1068', '584', '1570', '1748', '317', '1683', '223', '1680', '1556', '214', '506', '208', '1427', '194', '140', '305', '226', '1305', '1531', '1472', '1284', '1633', '1293', '1704', '1779', '1682', '1399', '962', '150', '1785', '1074', '1065', '1568', '1407', '1234', '1754', '1107', '131', '1247', '1467', '1341', '186', '1673', '1349', '120', '212', '1110', '595', '601', '968', '153', '1646', '1486', '1432', '1542', '1386', '1166', '1471', '119', '1554', '1028', '1191', '1258', '1456', '1546', '1585', '224', '1627', '1323', '542', '493', '258', '1470', '301', '128', '1638', '604', '1536', '1426', '1684', '168', '121', '1170', '18', '1058', '1325', '1132', '1195', '1060', '546', '199', '1730', '1603', '1718', '1574', '1720', '1776', '1102', '1326', '148', '1782', '1528', '1259', '108', '1440', '1188', '1219', '1282', '374', '1766', '1183', '190', '233', '1688', '189', '1123', '70', '207', '1537', '1778', '149', '200', '1053', '97', '1622', '1133', '101', '228', '1626', '99', '1674', '1733', '1703', '1543', '1602', '1064', '1143', '1362', '413', '479', '1037', '1338', '1515', '1489', '1745', '1380', '1382', '364', '304', '1248', '133', '1357', '1578', '1359', '1423', '44', '1689', '1671', '1605', '117', '1451', '1595', '1649', '251', '613', '1768', '141', '332', '1581', '1243', '1242', '1474', '1511', '622', '1444', '132', '158', '1634', '1685', '395', '1207', '1503', '1224', '1389', '1134', '1225', '1632', '1764', '1774', '1422', '219', '1318', '126', '277', '1792', '1512', '1553', '1619', '1600', '1584', '1315', '12', '1333', '1301', '1043', '1345', '1559', '1642', '385', '171', '642', '1226', '95', '1458', '1446', '203', '1094', '1588', '924', '1223', '403', '1204', '118', '1167', '1767', '1721', '1672', '1629', '1324', '1232', '1661', '1082', '1437', '1591', '88', '89', '1222', '252', '412', '1738', '1403', '1075', '1620', '1580', '1797', '123', '1711', '1464', '1283', '1128', '1435', '83', '1381', '1794', '1463', '179', '136', '411', '1617', '535', '1606', '556', '188', '1436', '198', '1637', '39', '1613', '137', '1582', '1228', '1061', '90', '1541', '1452', '1428', '100', '1344', '971', '230', '1731', '1535', '536', '103', '1072', '1135', '129', '1092', '1601', '1547', '1447', '1607', '1221', '81', '1759', '1384', '1287', '996', '1330', '1316', '151', '1727', '1594', '220', '1597', '1506', '1550', '1039', '1705', '180', '1692', '178', '291', '1572', '1288', '1544', '371', '82', '1508', '1732', '1789', '1751', '1750', '1335', '116', '1686', '1589', '1798', '1563', '1668', '177', '623', '1497', '1112', '1430', '1749', '36', '1624', '1639'])]




with get_db_connection() as conn:
    try:
        
    except Exception as e:
        conn.rollback()
        logger.error(f"[DATABASE] Error executing {operation_type} operation: {e}")
        
    
def update_pair_data(
    table: str,
    columns_to_update: str,
    data_to_update: List[Any],
    columns_to_check_condition: str,
    data_to_check_condition: List[Any]
)