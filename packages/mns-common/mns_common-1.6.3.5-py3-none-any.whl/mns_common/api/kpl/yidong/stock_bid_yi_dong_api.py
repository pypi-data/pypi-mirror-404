import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import requests
from loguru import logger


def get_stock_yi_dong_info(kpl_token):
    # 接口请求地址
    url = "https://apphwshhq.longhuvip.com/w1/api/index.php"

    # 请求头，完全复刻你抓包的所有请求头，缺一不可（接口校验用）
    headers = {
        "Host": "apphwshhq.longhuvip.com",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "Connection": "keep-alive",
        "Accept": "*/*",
        "User-Agent": "lhb/5.22.5 (com.kaipanla.www; build:1; iOS 18.6.2) Alamofire/4.9.1",
        "Accept-Language": "en-US;q=1.0, zh-Hans-US;q=0.9",
        "Accept-Encoding": "gzip;q=1.0, compress;q=0.5"
    }

    # POST表单请求参数，完全复制你抓包的参数，键值对一一对应
    data = {
        "DeviceID": "712e04ccbd13c8e55930ab11b1ca2ee76e7f0e80",
        "PhoneOSNew": "2",
        "Token": kpl_token,
        "UserID": "3838941",
        "VerSion": "5.22.0.5",
        "ZDJK_Type": "1",
        "a": "GetPianLiZhi_Index",
        "apiv": "w43",
        "c": "StockBidYiDong"
    }

    # 发送POST请求（核心）
    try:
        # verify=False 忽略HTTPS证书校验（部分域名会有证书问题，加上无影响）
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)
        result = response.json()
        return result

    except Exception as e:
        logger.error("接口请求失败，错误信息:{}", str(e))


if __name__ == '__main__':
    get_stock_yi_dong_info('1b3144e108bb84bda145e7ae2abd5c4f')
