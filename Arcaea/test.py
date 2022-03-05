import asyncio
import requests
import json
import base64
import uuid

# from api import *

headers = {
    "Accept-Language": "en-us",
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Accept-Encoding": "br, gzip, deflate",
    "AppVersion": "2.1.0",
    "User-Agent": "Arc-mobile/2.1.0.0 CFNetwork/976 Darwin/18.2.0",
}

# bind_id, email, password = asql.get_not_full_email()
# info = asyncio.run(get_web_api(email, password))
# print(info)


def friend_add(friend_code):
    """
    usage:
        friend_code: the 9-digit code of the user that you want to add as a friend
        by adding a friend you may check his/her best30 data via rank_friend
    example:
        friend_add(114514810)
    return:
        {
            "success": true,
            "value": {
                "user_id": 1506141,
                "updatedAt": "2019-03-28T18:46:48.021Z",
                "createdAt": "2019-03-28T17:03:51.959Z",
                "friends": [
                    {
                        "user_id": *,
                        "name": "*",
                        "recent_score": [
                            {
                                "song_id": "paradise",
                                "difficulty": 2,
                                "score": 10000727,
                                "shiny_perfect_count": 727,
                                "perfect_count": 729,
                                "near_count": 0,
                                "miss_count": 0,
                                "clear_type": 3,
                                "best_clear_type": 3,
                                "health": 100,
                                "time_played": 1553611941291,
                                "modifier": 2,
                                "rating": 9.8
                            }
                        ],
                        "character": 7,
                        "join_date": 1493860119612,
                        "rating": 1210,
                        "is_skill_sealed": false,
                        "is_char_uncapped": false,
                        "is_mutual": false
                    }
                ]
            }
        }
    """
    friend_add_data = {"friend_code": friend_code}
    if auth_str and ("Authorization" not in headers):
        headers["Authorization"] = auth_str
    friend_add_url = "https://arcapi.lowiro.com/5/friend/me/add"
    #
    friend_add_response = requests.post(
        friend_add_url, headers=headers, data=friend_add_data
    )
    friend_add_json = json.loads(friend_add_response.content)
    print(json.dumps(friend_add_json, indent=4))

    return friend_add_json


def user_login(name, password, add_auth=True, change_device_id=False):
    """
    attention:
        your account will be banned for a while if it is logged into more than 2 devices of different uuid
    usage:
        name: username
        password: password
        add_auth: whether to use the (new) authorization code for following functions
        change_device_id: whether to change (and use) a new device id instead of using default device id
    example:
        user_login('tester2234', 'tester223344')
    """

    login_cred = {"name": name, "password": password}
    login_data = {"grant_type": "client_credentials"}
    if change_device_id:
        headers["DeviceId"] = str(uuid.uuid4()).upper()
        static_uuid = headers["DeviceId"]
        print("new_uuid: " + static_uuid)
    headers["Authorization"] = "Basic " + str(
        base64.b64encode(
            (login_cred["name"] + ":" + login_cred["password"]).encode("utf-8")
        ),
        "utf-8",
    )
    login_url = "https://arcapi.lowiro.com/5/auth/login"
    print(headers)
    login_response = requests.post(login_url, headers=headers, data=login_data)
    login_json = json.loads(login_response.content)
    print(json.dumps(login_json, indent=4))

    if login_json["success"]:
        if add_auth:
            headers["Authorization"] = (
                login_json["token_type"] + " " + login_json["access_token"]
            )
            auth_str = headers["Authorization"]
            print("new_auth: " + auth_str)
        else:
            headers["Authorization"] = auth_str
        headers.pop("DeviceId")

    return login_json


print(user_login("smoe", "mm7749.1"))
