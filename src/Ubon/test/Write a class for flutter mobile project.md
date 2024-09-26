Write a class for flutter mobile project using Dart. This class will respondsible for custom CCTV live streaming content. When this class is call from main file. It should populate the element that show the live video. Here is how it will be use in the main file:

```dart
cctvVideoWidget = LiveVideoWidget(
                    cctvId: 'cctvp2c003',
                    height: 200,
                    borderRadius: 10,
                  );
```

"cctvId" will be use to get the video streaming.
"height" is the height of this video widget, it should maintain the aspect ratio of the video. Sometimes video will not have fix aspect ratio, so width can be anything that maintain the aspect ratio of the video.
"borderRadius" is the value for rounded conner of the video widget.

To Make this work. This class should construct some URLs to get the information from my server and show live stream video. Please note that this is special and custom video streaming. So follow the instruction strictly.


1. Take the value from "cctvId". Assume it is 'cctvp2c003' in this example. Use this calue to construct the following URL "http://183.88.214.137:1935/livecctv/{cctvId}.stream/playlist.m3u8"
2. After you got the URL "http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8", you should access it to get the following information.

```text
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1662070,CODECS="avc1.4d002a",RESOLUTION=1920x1080
chunklist_w1730975490.m3u8
```

The program should store the information in Map in the following format:

```text
'chunklist': r'#EXT-X-STREAM-INF:.*\n(.*\.m3u8)',
'bandwidth': r'BANDWIDTH=(\d+)',
'codecs': r'CODECS="([^"]+)"',
'resolution': r'RESOLUTION=(\d+x\d+)',
'version': r'#EXT-X-VERSION:(\d+)'
```

Please use Regx to extrct the information from the URL, the final information in Map should be like this

```dart
Map<String, dynamic> playlist = {
  'chunklist': 'chunklist_w1730975490.m3u8',
  'bandwidth': 1662070,
  'codecs': 'avc1.4d002a',
  'resolution': '1920x1080',
  'version': '3'
};
```

Put this information in Map call "playlist"

3. Once the playlist.m3u8 information is get and extracted, get the current_m3u8 from "playlist" Map.

```dart
var current_m3u8 = playlist['chunklist'];
```

4. do the following
4.1 Construct another URL "http://183.88.214.137:1935/livecctv/{cctvId}.stream/{current_m3u8}"
4.2 The final URL should look like this "http://183.88.214.137:1935/livecctv/cctvp2c003.stream/chunklist_w1730975490.m3u8"
4.3 Access the URL which it will return the following information:

```text
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:12
#EXT-X-MEDIA-SEQUENCE:4772
#EXT-X-DISCONTINUITY-SEQUENCE:0
#EXTINF:10.0,
media_w1667482339_4772.ts
#EXTINF:10.0,
media_w1667482339_4773.ts
#EXTINF:10.0,
media_w1667482339_4774.ts
```
4.4 Use this for HLS Video player. Please not that this is the only way to get the correct .m3u8 file. If you try to change the way to get .m3u8, it will not work. I want the user to have no control for video player widget and want to show live video without pausing or rewinding, we will disable all player controls. Then use this m3u8 information to get video streaming form this url "http://183.88.214.137:1935/livecctv/{cctvId}.stream/{current_video}". The final url should looks like this: "http://183.88.214.137:1935/livecctv/{cctvId}.stream/media_w1667482339_4772.ts"

I am not sure how the HLS work so I tell you the direct link to get the video file, but if HLS know how to manage information from m3u8 file, that's is ok.




#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2149280,CODECS="mp4a.40.2,avc1.64001f",RESOLUTION=1280x720,NAME="720" url_0/193039199_mp4_h264_aac_hd_7.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=246440,CODECS="mp4a.40.5,avc1.42000d",RESOLUTION=320x184,NAME="240" url_2/193039199_mp4_h264_aac_ld_7.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=460560,CODECS="mp4a.40.5,avc1.420016",RESOLUTION=512x288,NAME="380" url_4/193039199_mp4_h264_aac_7.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=836280,CODECS="mp4a.40.2,avc1.64001f",RESOLUTION=848x480,NAME="480" url_6/193039199_mp4_h264_aac_hq_7.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=6221600,CODECS="mp4a.40.2,avc1.640028",RESOLUTION=1920x1080,NAME="1080" url_8/193039199_mp4_h264_aac_fhd_7.m3u8





#EXTM3U 
#EXT-X-VERSION:3
#EXT-X-PLAYLIST-TYPE:VOD
#EXT-X-TARGETDURATION:11
#EXTINF:10.000, url_462/193039199_mp4_h264_aac_hd_7.ts
#EXTINF:10.000, url_463/193039199_mp4_h264_aac_hd_7.ts
#EXTINF:10.000, url_464/193039199_mp4_h264_aac_hd_7.ts
#EXTINF:10.000, url_465/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_466/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_467/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_468/193039199_mp4_h264_aac_hd_7.ts #EXTINF:9.950, url_469/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.050, url_470/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_471/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_472/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_473/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_474/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_475/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_476/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_477/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_478/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_479/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_480/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_481/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_482/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_483/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_484/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_485/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_486/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_487/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_488/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_489/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_490/193039199_mp4_h264_aac_hd_7.ts #EXTINF:9.950, url_491/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.050, url_492/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_493/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_494/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_495/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_496/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_497/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_498/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_499/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_500/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_501/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_502/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_503/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_504/193039199_mp4_h264_aac_hd_7.ts #EXTINF:9.950, url_505/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.050, url_506/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_507/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_508/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_509/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_510/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_511/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_512/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_513/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_514/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_515/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_516/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_517/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_518/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_519/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_520/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_521/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_522/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_523/193039199_mp4_h264_aac_hd_7.ts #EXTINF:10.000, url_524/193039199_mp4_h264_aac_hd_7.ts #EXTINF:4.584, url_525/193039199_mp4_h264_aac_hd_7.ts #EXT-X-ENDLIST












ok, next write a flutter application that can populate the live video widget by calling like this 

```dart
cctvVideoWidget = LiveVideoWidget(
                    url: 'http://183.88.214.137:1935/livecctv/cctvp2c003.stream/chunklist_w804003208.m3u8',
                    height: 200,
                    borderRadius: 10,
                  );
```

"url" will be use to get the video streaming.
"height" is the height of this video widget, it should maintain the aspect ratio of the video. Sometimes video will not have fix aspect ratio, so width can be anything that maintain the aspect ratio of the video.
"borderRadius" is the value for rounded conner of the video widget.

This class should call `assets/live_stream.html` which in the html file I jsut asked you to do. And you have to input the url into it.



fetch("https://camerai1.iticfoundation.org/hls/kk22.m3u8", {
  "headers": {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,th-TH;q=0.8,th;q=0.7",
    "if-modified-since": "Thu, 26 Sep 2024 03:09:36 GMT",
    "if-none-match": "\"66f4d070-88\"",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site"
  },
  "referrer": "https://portal.kkmuni.go.th/",
  "referrerPolicy": "strict-origin-when-cross-origin",
  "body": null,
  "method": "GET",
  "mode": "cors",
  "credentials": "omit"
});


So in my flutter mobile app project, I have these 2 class for flutter mobile app. The issue is that these 2 class will populate new live stream to show user, but the way it get cctv streaming from difference source is not the same. 

```dart
cctvImageWidget = BMALiveVideo(
  cctvId: '7',
  height: 250,
  borderRadius: 12,
);

cctvImageWidget = HLSLiveVideo(
  url: 'http://183.88.214.137:1935/livecctv/cctvp2c011.stream/playlist.m3u8',
  height: 200,
  borderRadius: 12,
);
```

However, this could be problematic because I have to hard code into difference point in my app that which one should use which class. I want you to create another class that will act as the adapeter. This class should accept the following information

```dart
cctvImageWidget = LiveVideoAdapter(
  data: {type of string only},
  owner: {type of string only},
  host: {type of string only},
  height: {type of double},
  borderRadius: {type of double},
);
```

I should be able to call it and it will decide which cctv streaming method it should use. If the owner and host is "ubon" then use HLSLiveVideo. Take the value from 'data' and put in the 'url' of HLSLiveVideo. Also take the value of height and borderRadius and put in the height and borderRadius of HLSLiveVideo.

If the owner and host is "bma" then use BMALiveVideo. Take the value from 'data' and put in the 'cctvId' of BMALiveVideo. Also take the value of height and borderRadius and put in the height and borderRadius of BMALiveVideo.

{
    "id": "7",
    "owner": "Ubon",
    "host": "Ubon",
    "data": "http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8"
}


