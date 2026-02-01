import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import requests
import pandas as pd


# year 年
#  quarter 季度
# month 月度
# week 周
# day 日
def get_xue_qiu_k_line(symbol, period, cookie, end_time, hq):
    url = "https://stock.xueqiu.com/v5/stock/chart/kline.json"

    params = {
        "symbol": symbol,
        "begin": end_time,
        "period": period,
        "type": hq,
        "count": "-120084",
        "indicator": "kline,pe,pb,ps,pcf,market_capital,agt,ggt,balance"
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "origin": "https://xueqiu.com",
        "priority": "u=1, i",
        "referer": "https://xueqiu.com/S/SZ300879?md5__1038=n4%2BxgDniDQeWqxYwq0y%2BbDyG%2BYDtODuD7q%2BqRYID",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "cookie": cookie
    }

    response = requests.get(
        url=url,
        params=params,
        headers=headers
    )

    if response.status_code == 200:
        response_data = response.json()
        df = pd.DataFrame(
            data=response_data['data']['item'],
            columns=response_data['data']['column']
        )

        # 1. 转换为 datetime（自动处理毫秒级时间戳）
        df["beijing_time"] = pd.to_datetime(df["timestamp"], unit="ms")

        # 2. 设置 UTC 时区
        df["beijing_time"] = df["beijing_time"].dt.tz_localize("UTC")

        # 3. 转换为北京时间（UTC+8）
        df["beijing_time"] = df["beijing_time"].dt.tz_convert("Asia/Shanghai")

        # 4. 提取年月日（格式：YYYY-MM-DD）
        df["str_day"] = df["beijing_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        del df["beijing_time"]

        return df
    else:
        # 直接抛出带有明确信息的异常
        raise ValueError("调用雪球接口失败")


import mns_common.component.cookie.cookie_info_service as cookie_info_service
if __name__ == '__main__':
    number = 1
    cookies = cookie_info_service.get_xue_qiu_cookie()
    while True:
        test_df = get_xue_qiu_k_line('NVDA', '1m', cookies, '1769473112000', '')
        print(number)
        number = number + 1
