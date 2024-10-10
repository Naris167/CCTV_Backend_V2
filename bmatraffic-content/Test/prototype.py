import time
import requests
from requests.exceptions import RequestException
from typing import Optional

"""
1. Make connetion to http://www.bmatraffic.com to get the sessionID
2. Request for the specific video from http://www.bmatraffic.com/PlayVideo.aspx?ID={camera_id} with the camera ID
3. Get the streaming images from http://www.bmatraffic.com/show.aspx
"""



BASE_URL = "http://www.bmatraffic.com"
IMAGE_FILENAME = 'image.jpg'


def get_session_id(url: str) -> Optional[str]:
    try:
        response = requests.get(url)
        response.raise_for_status()
        cookie = response.headers.get('Set-Cookie', '')
        return cookie.split("=")[1].split(";")[0] if cookie else None
    except RequestException as e:
        print(f"Error getting session ID: {e}")
        return None


def get_image(session_id: str) -> bool:
    url = f"{BASE_URL}/show.aspx"
    headers = {
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        with open(IMAGE_FILENAME, 'wb') as f:
            f.write(response.content)
        return True
    except RequestException as e:
        print(f"Error getting image: {e}")
        return False


def play_video(camera_id: int, session_id: str) -> bool:
    url = f"{BASE_URL}/PlayVideo.aspx?ID={camera_id}"
    headers = {
        'Referer': f'{BASE_URL}/index.aspx',
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        time.sleep(3)
        return get_image(session_id)
    except RequestException as e:
        print(f"Error playing video: {e}")
        return False


def main():
    session_id = get_session_id(BASE_URL)
    if not session_id:
        print("Failed to obtain session ID")
        return

    print(f"Session ID: {session_id}")
    time.sleep(1)

    print("Playing video...")
    if play_video(1223, session_id):
        print(f"Image saved as {IMAGE_FILENAME}")
    else:
        print("Failed to play video and get image")


if __name__ == '__main__':
    main()