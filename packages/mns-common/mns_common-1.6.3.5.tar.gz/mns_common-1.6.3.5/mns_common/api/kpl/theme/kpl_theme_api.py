import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import requests


def kpl_theme_index(theme_id, kpl_token):
    # 1. 定义请求的基础信息
    url = "https://applhb.longhuvip.com/w1/api/index.php"

    # 2. 构造请求头（Headers），与你提供的完全一致
    headers = {
        "Host": "applhb.longhuvip.com",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "Connection": "keep-alive",
        "Accept": "*/*",
        "User-Agent": "lhb/5.22.5 (com.kaipanla.www; build:1; iOS 18.6.2) Alamofire/4.9.1",
        "Accept-Language": "en-US;q=1.0, zh-Hans-US;q=0.9",
        "Accept-Encoding": "gzip;q=1.0, compress;q=0.5"
    }

    # 3. 构造表单数据（POST Body）
    data = {
        "DeviceID": "712e04ccbd13c8e55930ab11b1ca2ee76e7f0e80",
        "ID": str(theme_id),
        "PhoneOSNew": "2",
        "Token": kpl_token,
        "UserID": "3838941",
        "VerSion": "5.22.0.5",
        "a": "InfoGet",
        "apiv": "w43",
        "c": "Theme"
    }

    try:
        # 4. 发送POST请求
        response = requests.post(
            url=url,
            headers=headers,
            data=data,  # 表单数据用data参数，会自动按x-www-form-urlencoded编码
            timeout=10  # 设置10秒超时，避免请求挂起
        )

        # 5. 打印响应结果

        json_data = response.json()
        return json_data
        # 如果响应是JSON格式，也可以解析成字典
        # print("JSON格式响应:", response.json())

    except requests.exceptions.RequestException as e:
        # 捕获请求相关的异常（超时、连接失败等）
        print("请求出错:", str(e))


import time

if __name__ == '__main__':
    theme_id_test = 9
    while theme_id_test < 300:
        json_data = kpl_theme_index(theme_id_test)
        theme_id_test = theme_id_test + 1
        print(json_data)
        time.sleep(1)
