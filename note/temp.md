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