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