```bash
npm init -y
npm install express axios node-cron p-limit date-fns
```

```bash
git filter-branch --index-filter "git rm -rf --cached --ignore-unmatch ./.env.prod" HEAD
git push origin --force --all
```

```bash
npm install -g bun
```






'''
if jsut fetching the image ican keep session ID alive, Then we can do this like every 10 minute. So we don't have to fetch session ID again.
But if there are any image the less than 5120 bytes, we have to fetch the session ID 

But we have to think more for this approach as some cctv might come back online but we did not fetch the session ID (maybe we can fetch session ID every 30 minute or 1 hours)

Now we have to test if this will work or not, or we have to play video to keep session alive.

Also, if this way can keep it alive. How long can session ID last? 


And if we did not do anything with t he session ID, how long it will last?

Even we can keep session ID alive, we still have to fetch from bmatraffic to make sure that cctv list in DB is updated.

Conclusion:
1. It has been tested that getting image every 1 minutes for 80 minutes can keep session alive
2. It has been tested that play video every 1 minutes for 80 minutes can keep session alive.
3. Expired session ID cannot be recover.
4. Session ID will be expried after 20 minutes if there is no play video or getting image.
5. Test it to see if playing video every 18 minutes for whole day can still keep sesssion ID alive or not.
'''

**Edit the script to use multithread to get all the information from every source at the start to reduce time consume**

**When using `update_isCamOnline()` must use it twice to update record to online and offline. It could be a better idea to make it accept dictionary that have list of cctv as key and TRUE FALSE as a value. So this function will be call once**

To store data
`loaded_JSON_cctvSessions` dictionary
`current_cctv` list
`offline_session` list
`cctv_fail` list (cam id that falied to get session ID)


`alive_session` dictionary (put in new JSON)
`get_session` list (get session again)
string `loaded_JSON_latestRefreshTime`
string `loaded_JSON_latestUpdateTime`


This script will be call every 15 minutes 
1. Get the distance in meters for clustering
2. `log_setup()` is called
3. Load data from latest JSON. If there is no JSON available, skip this entire steps and start with `startUpdate(param)`.
    1. Load data from JSON
        - "latestRefreshTime" load to string `loaded_JSON_latestRefreshTime`,
        - "latestUpdateTime" load to string `loaded_JSON_latestUpdateTime`,
        - "cctvSessions" load to `loaded_JSON_cctvSessions` dictionary
    2. If string `loaded_JSON_latestUpdateTime` is older than 3 hours compare with time now skip this entire steps and start with `startUpdate(param)`.
    3. Call `get_images` using information in `loaded_JSON_cctvSessions` dictionary.
        1. If images size is more than 5120 bytes, this is success. Add cctv ID and its session ID to `alive_session` dictionary.
        2. If images size is less than 5120 bytes, this is failed. Retry 5 times. If still failed, add cctv ID to `offline_session` list.
    4. Call `retrieve_camInfo_BMA()` and put the cam ID in `current_cctv` list.
        1. For any item (cam ID) in `current_cctv` list that is not present in `alive_session` dictionary, add it to `get_session` list.
        2. For any item in `alive_session` dictionary that is not present in `current_cctv` list, add it to `offline_session` list. (This step is redundant since offline cctv will result in image size less than 5120 bytes, but just do it for edge case and display a warning log as this is unusal)
    5. If `get_session` list is not empty, put it into a `create_session_id()`. This function will get and play video for new session ID. Then it will store session ID in the `alive_session` dictionary. Any falied to prepare session ID will be store in `cctv_fail` list
    6. Extract key from `alive_session` dictionary to list, then put that list into `update_isCamOnline()` function.
    7. call `save_cctv_sessions_to_file` to write data to new JSON
        - "latestRefreshTime" use time now
        - "latestUpdateTime" use time from string `loaded_JSON_latestUpdateTime`
        - "cctvSessions" use data from `alive_session` dictionary
    8. END OF SCRIPT

2. If there is no JSON available or string `loaded_JSON_latestUpdateTime` is older than 3 hours, the following process will be run.
    1. Get the distance in meters for clustering
    2. `log_setup()` is called
    3. `startUpdate(param)` is called
        1. `retrieve_camInfo_BMA()` is called 
            1. Fetch and extract online cam from URL
            2. max_retries=5, delay=5, timeout=120
            3. Return `list of tuple` or `False` if failed
        2. `retrieve_camLocation()` is called
            1. Get `Cam_ID`, `Latitude`, `Longitude` from DB
        3. if result from `retrieve_camInfo_BMA()` is not empty
            1. Sort the result and put in `CCTV_LIST`
            2. `filter_new_and_all_cams(onlineCamInfo, dbCamCoordinate)` is called
                1. Any `onlineCamInfo` that is not found in `dbCamCoordinate` will be added to `new_cam_info`
                2. `onlineCamInfo` will also be added to `all_cams_coordinate`
            3. Any cam ID in `CCTV_LIST` will be update to online
            4. if `new_cam_info` is not empty
                1. Start clustering
                2. `add_camRecord(new_cams_info)` is called to add cam info to DB
                3. `update_camCluster(clustered_cams_coordinate)` is called to update cam group in DB
                4. else `logger.info("[UPDATER] No new cameras found.")`
            5. else `retrieve_onlineCam()` is called and result is put in `CCTV_LIST`
    4. `prepare_session_workers()` is called to distribute workers
        1. `get_cctv_session_id()` is called
        2. `play_video()` is called
        3. if the process success, add session ID to dictionary with cam ID as a key
        4. if the process failed, add cam ID to `cctv_fail` list
    5. Sort and display `cctv_sessions` dictionary
    6. If `cctv_fail` list is not empty, update those cam ID to offline
    7. Error check if scraped cctv ID list is not equal to processed_cctv and fail to processed cctv.
    8. Call `save_cctv_sessions_to_file` to write data to new JSON
        - "latestRefreshTime" use time now
        - "latestUpdateTime" use time from string `loaded_JSON_latestUpdateTime`
        - "cctvSessions" use data from `cctv_sessions` dictionary








```python
cctv_working = {"cam1": "A1", "cam2": "B2"}
cctv_unresponsive = {"cam3": "C3", "cam4": "A1"}  # Note: "A1" is duplicate
cctv_fail = ["E5", "cam1"]  # Note: "cam1" is duplicate
```
Edit it so that it can check for all types of conbinations that can happen. Use this as a template for output

In case a value is duplicate in 2 source
Duplicate found: Found '{duplicate value}' which is a {'key', 'value', or 'item' (choose base on type of input. If it is a list, use word 'item', if it is dictionary, use word 'key' or 'value' which you have to find out)} in {'cctv_working' or 'cctv_unresponsive' or 'cctv_fail', choose the source name} {data type of source name; list or dictionary}

In case a value is duplicate in 3 source
Duplicate found: Found '{duplicate value}' which is a {'key', 'value', or 'item' (choose base on type of input. If it is a list, use word 'item', if it is dictionary, use word 'key' or 'value' which you have to find out)} in {'cctv_working' or 'cctv_unresponsive' or 'cctv_fail', choose the source name} {data type of source name; list or dictionary} and is a {'key', 'value', or 'item' (choose base on type of input. If it is a list, use word 'item', if it is dictionary, use word 'key' or 'value' which you have to find out)} in {'cctv_working' or 'cctv_unresponsive' or 'cctv_fail', choose the source name} {data type of source name; list or dictionary}


make it so that it can handle the case where there are more than 1 record in dictionary that have same value in 2 differemce key. You can tell it like (key: 'cam2', value: 'B2'), (key: 'cam3', value: 'B2') and so on. On the other hand, if it is a list tell how many you found in that list like "... is a item in cctv_fail list (found 3 duplicate in this one)"



Integrity check passed: False
Issues found:
- Found 'cam1' which is a key in cctv_working dictionary (key: 'cam1', value: 'A1') duplicated in the following items:
--- is a item in cctv_fail list (found 1 duplicate in this one)
- Found 'A1' which is a value in cctv_working dictionary (key: 'cam1', value: 'A1') duplicated in the following items:
--- is a value in cctv_unresponsive dictionary (key: 'cam4', value: 'A1')
--- is a item in cctv_fail list (found 2 duplicates in this one)
- Found 'B2' which is a value in cctv_working dictionary (key: 'cam2', value: 'B2'), (key: 'cam3', value: 'B2') duplicated in the following items:
--- is a key in cctv_unresponsive dictionary (key: 'B2', value: 'D4')
--- is a value in cctv_unresponsive dictionary (key: 'B3', value: 'B2')
--- is a item in cctv_fail list (found 3 duplicates in this one)










```sql
-- Create the cctv_locations_preprocessing table
CREATE TABLE cctv_locations_general (
    Cam_ID VARCHAR(50) PRIMARY KEY NOT NULL,
    Cam_Group VARCHAR(50),
    Cam_Name TEXT NOT NULL,
    Cam_Name_e TEXT,
    Cam_Location TEXT,
    Cam_Direction TEXT,
    Latitude DOUBLE PRECISION NOT NULL,
    Longitude DOUBLE PRECISION NOT NULL,
    Cam_Owner VARCHAR(255) NOT NULL,
    Cam_Host VARCHAR(255) NOT NULL,
    Verify BOOLEAN DEFAULT FALSE,
    is_online BOOLEAN DEFAULT FALSE,
    is_flooded BOOLEAN DEFAULT FALSE
);

-- Create the cctv_locations_preprocessing table
CREATE TABLE cctv_locations_general (
    -- Basic CCTV info
    Cam_ID VARCHAR(100) PRIMARY KEY NOT NULL,
    Cam_Group VARCHAR(50),
    Cam_Name TEXT NOT NULL,
    Cam_Name_e TEXT,
    Cam_Location TEXT,
    Cam_Direction TEXT,
    Latitude DOUBLE PRECISION NOT NULL,
    Longitude DOUBLE PRECISION NOT NULL,

    Organization TEXT,
    SponsorText TEXT,

    -- Streaming method and link
    Stream_Method VARCHAR(255) NOT NULL,
    Stream_Link_1 TEXT NOT NULL,
    Stream_Link_2 TEXT,
    Stream_Link_3 TEXT,
    Stream_Link_4 TEXT,
    Stream_Link_5 TEXT,
    Stream_Link_6 TEXT,
    Stream_Link_7 TEXT,
    
    LastUpdate TIMESTAMP,
    Verify BOOLEAN DEFAULT FALSE,
    is_inCity BOOLEAN,
    is_motion BOOLEAN,
    is_online BOOLEAN DEFAULT TRUE,
    is_flooded BOOLEAN DEFAULT FALSE
);

```


```python
List[Tuple[str, str, float, float, str, str, str, str, str, str, str, str, str, str, bool, bool]]
List[Tuple["camid", "title", "latitude", "longitude", "organization", "sponsertext", "Stream_Method", "hls_url", "link", "vdourl", "imgurl", "imgurl_specific", "overlay_file", "lastupdate", "incity", "motion"]]
```

Write a python function that access this URL "https://camera.longdo.com/feed/?command=json&callback=longdo.callback.cameras" to retrive the information and return a list of tuple in the following format "List[Tuple[str, str, float, float, str, str, str, str, str, str, str, str, str, str, bool, bool]]". This is how the data from URL looks like:

```json
longdo.callback.cameras([
    {
        "title": "(จ.ชลบุรี) แยกแกแล็คซี่ 1",
        "link": "https://camera1.iticfoundation.org/mjpeg2.php?camid=X.X.X.X:YYYY",
        "camid": "ITICM_BMAMI0112",
        "lastupdate": "2030-04-17 00:00:00",
        "latitude": "13.286483",
        "longitude": "100.938967",
        "incity": "N",
        "organization": "iTIC Motion",
        "sponsertext": "iTIC Motion",
        "motion": "Y",
        "vdourl": "https://camera1.iticfoundation.org/mjpeg2.php?camid=X.X.X.X:YYYY",
        "imgurl": "https://camera1.iticfoundation.org/jpeg2.php?camid=X.X.X.X:YYYY",
        "imgurl_specific": "https://camera1.iticfoundation.org/mjpeg2.cgi?camid=X.X.X.X:YYYY",
        "overlay_file": "banner_sponsors_sansuk_itic.jpg",
        "hls_url": "https://camerai1.iticfoundation.org/hls/ss10.m3u8"
    },
    {
        "title": "(จ.เพชรบุรี) 4 - อ.ชะอำ จ.เพชรบุรี ทิศทางมุ่งหน้าหัวหิน",
        "link": "https://camera1.iticfoundation.org/mjpeg.php?camid=PER-5-006-out",
        "camid": "DOH-PER-5-006-out",
        "lastupdate": "2030-04-17 00:00:00",
        "latitude": "12.8295",
        "longitude": "99.9352",
        "incity": "N",
        "organization": "กรมทางหลวง",
        "sponsertext": "สำนักอำนวยความปลอดภัย กรมทางหลวง",
        "motion": "Y",
        "vdourl": "https://camera1.iticfoundation.org/mjpeg.php?camid=PER-5-006-out",
        "imgurl": "https://camera1.iticfoundation.org/jpeg.cgi?camid=PER-5-006-out",
        "imgurl_specific": "https://camera1.iticfoundation.org/mjpeg.cgi?camid=PER-5-006-out",
        "overlay_file": "banner_sponsors_doh.jpg",
        "hls_url": "https://camerai1.iticfoundation.org/pass/180.180.242.207:1935/Phase5/PER_5_006_OUT.stream/playlist.m3u8"
    }
]);
```

Put the data into list of tuple in the following way:

"List[Tuple["camid", "title", "latitude", "longitude", "organization", "sponsertext", "Stream_Method", "hls_url", "link", "vdourl", "imgurl", "imgurl_specific", "overlay_file", "lastupdate", "incity", "motion"]]"

You may see that "Stream_Method" is not present in the JSON data. The value that you should put in this depend on the value from key "hls_url" in JSON. If the value of key "hls_url" in JSON have a value of URL that ended with ".m3u8", the value that you should assign for "Stream_Method" in the tuple will be "HLS", otherwise put "UNKNOWN"

For the last 2 value in the tuple, "incity" and "motion", originally the data in JSON will be "Y" or "N", if the value in JSON is "Y" put TRUE, if it is "N" put FALSE in the tuple












So I have here 3 list. For "cctv_list_ubon" and "cctv_list_itic" I will put in the argument of the function. This function should directly use "all_cctv_ids" list because this is the master record.

This function should find out which cctv is not online by check if any record in "cctv_list_ubon" and "cctv_list_itic" is not present in "all_cctv_ids", then that one is offline. This function should also check if "cctv_list_ubon" and "cctv_list_itic" and all input arguments, if their  "Stream_Method" is equal to "UNKNOWN" or "Stream_Link_1" is an empty text, then that record is offline too. The output of this function should be a list of "Cam_ID" that are offline


```python
cctv_list_ubon = List[Tuple["Cam_ID", "Cam_Name", "Latitude", "Longitude", "Stream_Method", "Stream_Link_1"]]

cctv_list_itic = List[Tuple["Cam_ID", "Cam_Name", "Latitude", "Longitude", "Stream_Method", "Stream_Link_1", "Stream_Link_2", 
"Stream_Link_3", "Stream_Link_4", "Stream_Link_5", "Stream_Link_6", "Organization", "SponsorText", "LastUpdate", "is_inCity", "is_motion"]]

all_cctv_ids = List["Cam_ID","Cam_ID","Cam_ID"...]

```