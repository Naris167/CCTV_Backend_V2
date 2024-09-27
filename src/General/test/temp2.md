fetch("http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8", {
  "headers": {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,th-TH;q=0.8,th;q=0.7"
  },
  "referrer": "http://183.88.214.137:8000/",
  "referrerPolicy": "strict-origin-when-cross-origin",
  "body": null,
  "method": "GET",
  "mode": "cors",
  "credentials": "omit"
});


fetch("https://camerai1.iticfoundation.org/hls/kk12.m3u8", {
  "headers": {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,th-TH;q=0.8,th;q=0.7",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Google Chrome\";v=\"128\"",
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




fetch("https://maps.googleapis.com/$rpc/google.internal.maps.mapsjs.v1.MapsJsInternalService/GetViewportInfo", {
  "headers": {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,th-TH;q=0.8,th;q=0.7",
    "content-type": "application/json+protobuf",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Google Chrome\";v=\"128\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "x-client-data": "CIu2yQEIorbJAQipncoBCIvwygEIlqHLAQiFoM0BCIDCzgEYj87NAQ==",
    "x-goog-api-key": "AIzaSyAx__8_59JMBUtuujJZEaCl9OH0g41ZgS0",
    "x-goog-maps-api-salt": "9CJPGdOydS",
    "x-goog-maps-api-signature": "15805",
    "x-goog-maps-channel-id": "",
    "x-goog-maps-client-id": "",
    "x-user-agent": "grpc-web-javascript/0.1"
  },
  "referrer": "http://183.88.214.137:8000/",
  "referrerPolicy": "strict-origin-when-cross-origin",
  "body": "[[[15.229835651498538,104.84308051529543],[15.2490895524486,104.88531487866976]],16,null,\"en-US\",0,\"m@706000000\",0,0,null,null,null,2]",
  "method": "POST",
  "mode": "cors",
  "credentials": "omit"
});







fetch("https://cdn.jsdelivr.net/npm/hls.js@1.0.7", {
  "headers": {
    "sec-ch-ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Google Chrome\";v=\"128\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
  },
  "referrer": "https://portal.kkmuni.go.th/",
  "referrerPolicy": "strict-origin-when-cross-origin",
  "body": null,
  "method": "GET",
  "mode": "cors",
  "credentials": "omit"
});








This is the correct url to get the file. Take whateve name get from 
http://183.88.214.137:8000/cctvList.js
http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8
http://183.88.214.137:1935/livecctv/cctvp2c003.stream/chunklist_w1719538425.m3u8
http://183.88.214.137:1935/livecctv/cctvp2c003.stream/media_w241855592_12813.ts






Create a class in dart for flutter application. This class will require cctvId as string, height as int, and borderRadius as int.
For now, you don't have to make it do anything yet. But make sure it is reusable and cn be call to use from other class. The result of this class is to show the live video. But Now these is no video, it is ok. Just leave it empty. Now, just take the size of height, the frame that will be used to show the video it should have height as specify but for width will depend on the size of live video. Make sure the aspect ratio of video is maintain. and also the borderRadius should be the border radius of this video frame. This is the example from other class how I did it for the picture showing.


```dart
@override
  Widget build(BuildContext context) {
    return Stack(
      alignment: Alignment.center,
      children: [
        if (imageKeys.isNotEmpty)
          AnimatedOpacity(
            key: ValueKey(imageKeys[_previousIndex]),
            opacity: 1,
            duration: const Duration(milliseconds: 1),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(widget.borderRadius),
              child: Image.memory(
                imageCache[imageKeys[_previousIndex]]!,
                height: widget.height,
                fit: BoxFit.contain,
              ),
            ),
          ),
      ],
    );
  }
```




Implement this main function from python into dart for flutter application. Use existing downloadTsFile, getMediaInfo, getM3u8Info in the same way as this python code did. However, this python code will save a file which I don't want. I want you to make it live stream the video content to the Widget build(BuildContext context) {...} Make sure that you connect video pieces together while the streaming happen like python did before it save. Give me the part of the code that need update.


```python
save_concatenated_file(cctv_id: str, buffer: BytesIO, start_time: float):
    duration = time.time() - start_time
    file_name = f"{cctv_id}_{int(start_time)}_{int(duration)}s.ts"
    with open(file_name, 'wb') as f:
        f.write(buffer.getvalue())
    logger.info(f"Saved concatenated file: {file_name}")

def monitor_cctv(cctv_id: str, duration: int = 60):
    playlist = get_m3u8_info(cctv_id)
    if not playlist:
        logger.error(f"Failed to get playlist for CCTV ID: {cctv_id}")
        return

    current_m3u8 = playlist[0]
    logger.info(f"Current M3U8: {current_m3u8}")

    downloaded_files: Set[str] = set()
    buffer = BytesIO()
    start_time = time.time()

    while time.time() - start_time < duration:
        media_info = get_media_info(cctv_id, current_m3u8)
        if not media_info or len(media_info) < 5:
            logger.error(f"Failed to get valid media info for CCTV ID: {cctv_id}")
            time.sleep(1)  # Wait a bit before retrying
            continue

        logger.info(f"Media info: {media_info}")

        # Check and download up to two available media files
        for i in range(4, min(6, len(media_info))):
            media_file = media_info[i][1]
            if media_file not in downloaded_files:
                logger.info(f"Downloading new file: {media_file}")
                file_content = download_ts_file(cctv_id, media_file)
                if file_content:
                    buffer.write(file_content)
                    downloaded_files.add(media_file)
            else:
                logger.info(f"File already downloaded: {media_file}")

        # Calculate time to wait before next check
        next_segment_time = float(media_info[4][0])  # Duration of the first segment
        current_time = time.time()
        elapsed_time = current_time - start_time
        time_to_wait = next_segment_time - (elapsed_time % next_segment_time)

        logger.info(f"Waiting {time_to_wait:.2f} seconds before next check")
        time.sleep(max(0.1, time_to_wait))  # Ensure we wait at least 0.1 seconds

    # Save the concatenated file after the monitoring duration
    save_concatenated_file(cctv_id, buffer, start_time)

def main():
    cctv_id = "cctvp2c003"
    monitor_cctv(cctv_id)

if __name__ == "__main__":
    main()
```






Can you write a code for flutter that so the same thing as this python code. It should call 

media_file = mediaInfo!.extInfList[i].$2

getTsFile(widget.cctvId,media_file)

Then store the video in buffer

# Check and download up to two available media files
        for i in range(4, min(6, len(media_info))):
            media_file = media_info[i][1]
            if media_file not in downloaded_files:
                logger.info(f"Downloading new file: {media_file}")
                file_content = getTsFile(cctv_id, media_file)
                if file_content:
                    buffer.write(file_content)
                    downloaded_files.add(media_file)
            else:
                logger.info(f"File already downloaded: {media_file}")

        # Calculate time to wait before next check
        next_segment_time = float(media_info[4][0])  # Duration of the first segment
        current_time = time.time()
        elapsed_time = current_time - start_time
        time_to_wait = next_segment_time - (elapsed_time % next_segment_time)

        logger.info(f"Waiting {time_to_wait:.2f} seconds before next check")
        time.sleep(max(0.1, time_to_wait))





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

4. Create the following variable

```dart
Set<String> downloadedFiles = <String>{};
BytesBuilder buffer = BytesBuilder();
int startTime = DateTime.now().millisecondsSinceEpoch;
```

5. Create while loop that run as long as the widget is open. This loop should do the following
5.1 Construct another URL "http://183.88.214.137:1935/livecctv/{cctvId}.stream/{current_m3u8}"
5.2 The final URL should look like this "http://183.88.214.137:1935/livecctv/cctvp2c003.stream/chunklist_w1730975490.m3u8"
5.3 Access the URL which it will return the following information:

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
5.4 Extract this information to a list of list `List<dynamic> media_info = [...]` using the following Regx

```text
'version': r'#EXT-X-VERSION:(\d+)',
'target_duration': r'#EXT-X-TARGETDURATION:(\d+)',
'media_sequence': r'#EXT-X-MEDIA-SEQUENCE:(\d+)',
'discontinuity_sequence': r'#EXT-X-DISCONTINUITY-SEQUENCE:(\d+)',
'extinf': r'#EXTINF:([\d.]+),\n(.*\.ts)'
```

The output should be like this

```dart
List<dynamic> media_info = [
  3, 
  12, 
  4497, 
  0, 
  [10.0, 'media_w1667482339_4772.ts'], 
  [10.0, 'media_w1667482339_4773.ts'], 
  [10.0, 'media_w1667482339_4774.ts']
];
// Accessing a specific nested element
print(media_info[4][1]); // Output: media_w2124041444_4497.ts
```

5.5 In this while loop, create another for loop with the following condition

```dart
for (int i = 4; i < (6 < mediaInfo.length ? 6 : mediaInfo.length); i++)
```

5.5.1 In this for loop, it should do the following:


```Dart
var media_file = mediaInfo[i][1];

/* Access these variable that was created early in the previous step.
Set<String> downloadedFiles = <String>{};
BytesBuilder buffer = BytesBuilder();
int startTime = DateTime.now().millisecondsSinceEpoch;
*/

if (!downloadedFiles.contains(media_file)) {
  print("Downloading new file: $media_file");
  var fileContent = downloadTsFile(cctvId, media_file);  // Replace with your actual function
  if (fileContent != null) {
    buffer.add(fileContent);
    downloadedFiles.add(media_file);
  }
} else {
  print("File already downloaded: $media_file");
}
```

5.6 Out from the for loop, create these variable:

```Dart
double nextSegmentTime = mediaInfo[4][0] as double;  // Duration of the first segment
int currentTime = DateTime.now().millisecondsSinceEpoch;
double elapsedTime = (currentTime - startTime) / 1000.0;
double timeToWait = nextSegmentTime - (elapsedTime % nextSegmentTime);

print("Waiting ${timeToWait.toStringAsFixed(2)} seconds before next check");
await Future.delayed(Duration(milliseconds: (timeToWait * 1000).clamp(100, double.infinity).toInt()));  // Ensure we wait at least 0.1 seconds
```

5.7 As of now, `BytesBuilder buffer = BytesBuilder();` should have some bytes data of live stream video. Create a VideoPlayer widget that can do the following:
5.7.1 Use a VideoPlayer for Streaming: Although Flutter's video_player plugin typically streams from files or network URLs, we'll need to simulate live streaming using an Asset or Memory file source.
5.7.2 Update the Video Player with New Data: Continuously update the video source as new data is added to the BytesBuilder.
5.7.3 Control Playback: I want the user to have no control for video player widget and want to show live video without pausing or rewinding, we will disable all player controls.
5.7.4 Clearing Played Data: After playing a portion of the video, you need to clear that data from the buffer.

Here is the sample code of how can you achieve this:

```Dart
import 'dart:async';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:path_provider/path_provider.dart';

class LiveVideoPlayer extends StatefulWidget {
  @override
  _LiveVideoPlayerState createState() => _LiveVideoPlayerState();
}

class _LiveVideoPlayerState extends State<LiveVideoPlayer> {
  BytesBuilder buffer = BytesBuilder();
  VideoPlayerController? _controller;
  Timer? _updateTimer;
  File? _videoFile;

  @override
  void initState() {
    super.initState();
    _startBufferUpdate();
  }

  @override
  void dispose() {
    _controller?.dispose();
    _updateTimer?.cancel();
    super.dispose();
  }

  // Function to write the buffer to a temporary file
  Future<File> _writeBufferToFile(Uint8List bytes) async {
    final directory = await getTemporaryDirectory();
    final file = File('${directory.path}/live_video.mp4');  // Use a file extension appropriate for your video
    return file.writeAsBytes(bytes, flush: true);
  }

  void _startBufferUpdate() {
    _updateTimer = Timer.periodic(Duration(milliseconds: 500), (timer) async {
      if (buffer.length > 0) {
        // Append new bytes to the existing buffer
        Uint8List currentBytes = buffer.toBytes();

        // Write the buffer to a temporary file
        _videoFile = await _writeBufferToFile(currentBytes);

        // Update the video player with the new buffer content
        if (_controller != null) {
          await _controller?.pause();
          await _controller?.dispose();
        }

        _controller = VideoPlayerController.file(_videoFile!)
          ..initialize().then((_) {
            setState(() {
              _controller?.play();  // Start playing the updated video stream
            });
          });

        // Clear the played bytes from the buffer
        buffer.clear();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: _controller?.value.isInitialized ?? false
            ? AspectRatio(
                aspectRatio: _controller!.value.aspectRatio,
                child: VideoPlayer(_controller!),
              )
            : CircularProgressIndicator(),
      ),
    );
  }
}

```




This function will run every 100 ms to feed new video file to the player. But there is an issue when first video is finished, it will take some time to load and save video from list of bytes to file, and it will send that to video player. This create a glitch on video player. Modify it so that it can do the following:
1. It check if bufferList is empty or not
2. It check if currentIndex < bufferList.length or not
2.1 If currentIndex is less than bufferList.length, it mean that new video pieces has been add to this list.
2.2 Call _writeBufferToFile() to save that to file. If there are multiple item in the list. Save all of them with difference name.
3. It check if _controller is null or not, or _controller is finished played video or not.
3.1 If _controller is null mean this is first time it will be created. Get the first file.
3.2 If _controller is finished played video, get the next file for the player.

Note: I want to use not more than 5 temp file. If it is more than that, replace the oldest one. May be you can use something like a temp list that store temp file and use modulus operator to cycle through the list. If it is the end, just go to the first item.

Please give me these 2 function only for your answer

```dart
  Future<File> _writeBufferToFile(Uint8List bytes, String fileName) async {
    final directory = await getTemporaryDirectory();
    final file = File('${directory.path}/$fileName');
    return file.writeAsBytes(bytes, flush: true);
  }

  void _startBufferUpdate() {
    _updateTimer = Timer.periodic(Duration(milliseconds: 100), (timer) async {
      if (bufferList.isNotEmpty) {
        if (currentIndex < bufferList.length) {
          if (_controller == null || _controller!.value.position >= _controller!.value.duration) {

            // Current video finished or no video playing, move to the next one
            Uint8List currentBytes = bufferList[currentIndex];
            _videoFile = await _writeBufferToFile(currentBytes, 'live_video.ts');

            _controller = VideoPlayerController.file(_videoFile!)
              ..initialize().then((_) {
                setState(() {
                  isInitialized = true;
                  _controller?.play();
                });
              });

            currentIndex++;
          }
        }
      }
    });
  }
```




This code output a list of tuple with the following informaiton "List[Tuple["camid", "title", "latitude", "longitude"]]". I want you to change this function so it have 2 more element in each tuple. So new format will be "List[Tuple["camid", "title", "latitude", "longitude", "Stream_Method", "hls_url"]]" and data type for each element will be "List[Tuple[str, str, float, float, str, str]]:"

For "Stream_Method" always put "HLS".
For "hls_url", you have to construct the URL in the following way.
This is based URL "http://183.88.214.137:1935/livecctv/{"camid"}.stream/playlist.m3u8"

For example, thw record with "camid" "cctvp2c003" the URL will be "http://183.88.214.137:1935/livecctv/cctvp2c003.stream/playlist.m3u8"

Then put this URL into the last element of the tuple

```python
def getCamList_Ubon() -> List[Tuple[str, str, float, float]]:
    url = "http://183.88.214.137:8000/cctvList.js"
    
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Get the content of the response
        content = response.text
        
        # Define the regex pattern to extract the required fields
        pattern = r'"name":\s*"([^"]+)",\s*"streamId":\s*"([^"]+)",\s*"lat":\s*"([^"]+)",\s*"lng":\s*"([^"]+)"'
        
        # Find all matches in the content
        matches = re.findall(pattern, content)
        
        # Process the extracted information, remove '\n' and extra spaces in the name
        cctv_list = [
            (streamId, re.sub(r'\s+', ' ', name.replace("\\n", " ").strip()), lat, lng) 
            for name, streamId, lat, lng in matches
        ]
        
        # Return the cleaned data
        cctv_list = sorted(cctv_list, key=lambda x: sort_key(x[0]))
        return cctv_list
    else:
        logger.info("Failed to retrieve the data. Status code:", response.status_code)
        return []
```


I have my API endpoint here

```js
app.get('/cctv', apiKeyMiddleware, async (req, res) => {
  try {
      const result = await pool2.query('SELECT cam_id, cam_name, cam_name_e, cam_location, cam_direction, latitude, longitude , is_online , is_flooded FROM cctv_locations_preprocessing ');

      // Format the rows
      const formattedRows = result.rows.map(row => (

        {
          cameraId: row.cam_id,
              name: row.cam_name,
              nameEnglish: row.cam_name_e,
              location: row.cam_location,
              direction: row.cam_direction,
              latitude: row.latitude,
              longitude: row.longitude,
              is_online :row.is_online,
              is_flooded : row.is_flooded
             
      }));

      res.json({
        status: 200,
        errMsg: "",
        data: formattedRows
    });
  } catch (err) {
      console.error(err);
      res.status(500).json({ error: 'An error occurred' });
  }
});
```


now it will output the following JSON

```json
{
    "status": 200,
    "errMsg": "",
    "data": [
        {
            "cameraId": "170",
            "name": "สะพานลอยใกล้โรงพยาบาลวุฒิสมเด็จย่า ถนนพหลโยธิน",
            "nameEnglish": "Footbridge near  Nawati Somdet Ya Hospital on Phahon Yothin Road",
            "location": "รถมาจากอนุสาวรีย์ชัยสมรภูมิ มุ่งหน้าไปแยกสะพานควาย",
            "direction": "From Victory Monument towards Saphan Khwai Intersection",
            "latitude": 13.78402,
            "longitude": 100.54611,
            "is_online": false,
            "is_flooded": false
        },
        {
            "cameraId": "1039",
            "name": "ใกล้สะพานนริศดำรัส คลองมหานาค ถนนจักรพรรดิพงษ์",
            "nameEnglish": "Near Narit Damras Bridge, Khlong Mahanak, Chakraphat Phong Road",
            "location": "สะพานนริศดำรัส ",
            "direction": "Towards Maen Si Intersection",
            "latitude": 13.754920632102062,
            "longitude": 100.50943762381905,
            "is_online": false,
            "is_flooded": false
        }
    ]
}

```


I want you to change it so that it will fetch the data from 2 table from databse. If the data coming from `cctv_locations_preprocessing`, the json output will be the same information but you will have to add 2 more key and value for each record from database. The first key and value is ""Stream_Method": "BMA"", and the second one will be ""Stream_Data": row.cam_id" ensure that the value from "row.cam_id" will be string.

The first data processing from first table is done. Now, next table have a name "cctv_locations_general". You have to fetch the value from the following column "Cam_ID", "Cam_Name", "Cam_Name_e", "Cam_Location", "Cam_Direction", "Latitude", "Longitude", "is_online", "is_flooded", "Stream_Method", "Stream_Link_1". This time you don't need to process data but take it directly from this table ""Stream_Method": from column "Stream_Method"", and the second one will be ""Stream_Data": from column "Stream_Link_1""

This is how the databased structure looks like.

```sql
CREATE TABLE cctv_locations_general (
    Cam_ID VARCHAR(100) PRIMARY KEY NOT NULL,
    Cam_Group VARCHAR(50),
    Cam_Name TEXT NOT NULL,
    Cam_Name_e TEXT,
    Cam_Location TEXT,
    Cam_Direction TEXT,
    Latitude DOUBLE PRECISION NOT NULL,
    Longitude DOUBLE PRECISION NOT NULL,
    Stream_Method VARCHAR(255) NOT NULL,
    Stream_Link_1 TEXT NOT NULL,
    is_online BOOLEAN DEFAULT TRUE,
    is_flooded BOOLEAN DEFAULT FALSE
);
```

The final JSON structure should looks like this. This is just a sample one for a quick look for you to understand what data type I want

```json
{
    "status": 200,
    "errMsg": "",
    "data": [
        {
            "cameraId": "170",
            "name": "สะพานลอยใกล้โรงพยาบาลวุฒิสมเด็จย่า ถนนพหลโยธิน",
            "nameEnglish": "Footbridge near  Nawati Somdet Ya Hospital on Phahon Yothin Road",
            "location": "รถมาจากอนุสาวรีย์ชัยสมรภูมิ มุ่งหน้าไปแยกสะพานควาย",
            "direction": "From Victory Monument towards Saphan Khwai Intersection",
            "latitude": 13.78402,
            "longitude": 100.54611,
            "is_online": false,
            "is_flooded": false,
            "Stream_Method": "BMA",
            "Stream_Data": "170"
        },
        {
            "cameraId": "CCTVP2C003",
            "name": "ใกล้สะพานนริศดำรัส คลองมหานาค ถนนจักรพรรดิพงษ์",
            "nameEnglish": "Near Narit Damras Bridge, Khlong Mahanak, Chakraphat Phong Road",
            "location": "สะพานนริศดำรัส ",
            "direction": "Towards Maen Si Intersection",
            "latitude": 13.754920632102062,
            "longitude": 100.50943762381905,
            "is_online": false,
            "is_flooded": false,
            "Stream_Method": "HLS", (sample value from database)
            "Stream_Data": "http://link.com" (sample value from database)
        }
    ]
}

```