import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import requests
import json
import re
import pandas as pd
from datetime import datetime
from loguru import logger
import mns_common.component.proxies.proxy_common_api as proxy_common_api
from concurrent.futures import ThreadPoolExecutor
import time
import mns_common.component.cache.cache_service as cache_service

# 整体数量key
TOTAL_NUMBER_KEY = 'total_number_key'

fs_amount = "m:0+t:6+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2,m:1+t:23+f:!2,m:0+t:81+s:262144+f:!2"

# 包含退市的
fs_all = "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048"

fields = ("f352,f2,f3,f5,f6,f8,f10,f11,f22,f12,f14,f15,f16,f17,"
          "f18,f20,f21,f26,f33,f34,f35,f62,f66,f69,f72,f100,f184,f211,f212"),

# 分页条数
PAGE_SIZE = 100


def get_all_stock_ticker_data(initial_proxies, time_out, total_number, use_proxy, must_all) -> pd.DataFrame:
    """
        使用多线程获取所有股票数据，失败页面会使用新IP重试，最多使用10个IP
        """

    total_pages = (total_number + PAGE_SIZE - 1) // PAGE_SIZE  # 向上取整
    all_pages = set(range(1, total_pages + 1))  # 所有需要获取的页码
    success_pages = set()  # 成功获取的页码
    results = []  # 存储成功获取的数据
    used_ip_count = 1  # 已使用IP计数器（初始IP算第一个）
    MAX_IP_LIMIT = 10  # IP使用上限

    # 完整数据同步最大次数
    must_all_max_number = 10
    must_all_count = 0

    # 循环处理直到所有页面成功或达到IP上限
    while True:
        must_all_count += 1

        # 获取当前需要处理的失败页码
        current_failed_pages = all_pages - success_pages
        if used_ip_count > 1:
            logger.info("当前需要处理的失败页码: {}, 已使用IP数量: {}/{}", current_failed_pages, used_ip_count,
                        MAX_IP_LIMIT)

        # 首次使用初始代理，后续获取新代理
        if len(success_pages) == 0:
            proxies = initial_proxies
        else:
            # 每次重试前获取新代理并计数
            # logger.info("获取新代理IP处理失败页面")
            if use_proxy:
                new_proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
                proxies = {"https": new_proxy_ip}
            else:
                proxies = None
            # logger.info("新代理IP: {}, 已使用IP数量: {}/{}", new_proxy_ip, used_ip_count + 1, MAX_IP_LIMIT)
            used_ip_count += 1  # 增加IP计数器

        # 创建线程池处理当前失败的页码
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(get_em_real_time_page_df, pn, PAGE_SIZE, proxies, time_out): pn
                for pn in current_failed_pages
            }

            # 收集结果并记录成功页码
            for future, pn in futures.items():
                try:
                    result_dict = future.result()

                    if result_dict is not None:
                        result = result_dict['stock_list']

                        if not result.empty:
                            results.append(result)
                            success_pages.add(pn)
                    # else:
                    #     logger.warning("页码 {} 未返回有效数据", pn)
                except Exception as e:
                    continue
                    # logger.error("页码 {} 处理异常: {}", pn, str(e))

        if len(list(all_pages - success_pages)) == 0 or must_all_count > must_all_max_number:
            break

        # 不要求全部数据时候，操过次数
        if bool(1 - must_all) and (used_ip_count > MAX_IP_LIMIT):
            break

    # 检查是否达到IP上限
    if used_ip_count >= MAX_IP_LIMIT and (all_pages - success_pages):
        remaining_pages = all_pages - success_pages
        logger.warning("已达到最大IP使用限制({}个)，剩余未获取页码: {}, 返回现有数据", MAX_IP_LIMIT, remaining_pages)

    # 合并所有成功获取的数据
    if results:
        return pd.concat(results, ignore_index=True)
    else:
        return pd.DataFrame()


# 获取页面数据
def get_em_real_time_page_df(page_num,
                             page_size,
                             proxies,
                             time_out):
    # 将当前时间转换为时间戳（以毫秒为单位）
    current_time = datetime.now()
    current_timestamp_ms = int(current_time.timestamp() * 1000)
    """
    爬取东方财富网股票数据（参数化版本）

    Args:
        page_num: 页码，默认1
        page_size: 每页条数，默认20
        sort_field: 排序字段，默认f3(涨跌幅)
        sort_order: 排序方式，1=降序，0=升序，默认1

    Returns:
        股票数据列表
    """
    # 基础URL（固定部分）
    base_url = "https://push2.eastmoney.com/api/qt/clist/get"

    params = {
        "cb": "jQuery1124046660442520420653_" + str(current_timestamp_ms),
        "pn": str(page_num),
        "pz": str(page_size),  # 每页最大100条
        # 排序方式
        "po": "1",

        "np": "3",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",

        "fltt": "2",
        "invt": "2",

        "wbp2u": "|0|0|0|web",
        # 排序字段
        "fid": "f3",

        "fs": fs_amount,
        "fields": fields,

        "_": current_timestamp_ms
    }
    # 请求头
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "script",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-site",
        "Referer": "https://quote.eastmoney.com/center/gridlist.html",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "cookie": "qgqp_b_id=fa5743ab0670e69a6f73e4f24004396e; st_nvi=E-iUixSh6y9cw_cZir8sNe73a; nid18=0d2f9c2d3559ee51f95d9a74d9541cdc; nid18_create_time=1765257213388; gviem=poNRbxa36bUtWq2hp1EIL8ee1; gviem_create_time=1765257213388; st_si=79137246352319; st_asi=delete; websitepoptg_api_time=1769565463001; fullscreengg=1; fullscreengg2=1; st_pvi=94815720100284; st_sp=2025-12-09%2013%3A13%3A33; st_inirUrl=https%3A%2F%2Fwww.baidu.com%2Flink; st_sn=3; st_psi=20260128095752920-113200301321-2199927942"
    }
    try:
        # 发送GET请求（自动拼接参数）
        if proxies is None:
            response = requests.get(base_url, params=params, headers=headers, timeout=time_out)
        else:
            response = requests.get(base_url, params=params, headers=headers, proxies=proxies, timeout=time_out)
        response.raise_for_status()

        # 处理JSONP数据
        jsonp_data = response.text
        json_str = re.search(r'jQuery\w+\((.*)\)', jsonp_data).group(1)
        data = json.loads(json_str)

        # 提取股票数据
        if data.get('data') and data['data'].get('diff'):
            stock_list = data['data']['diff']
            total_number = data['data']['total']
            stock_df = pd.DataFrame(stock_list)
            result_dict = {'total_number': total_number,
                           'stock_list': stock_df}
            return result_dict
        else:
            return None
    except requests.exceptions.RequestException as e:
        return None
    except Exception as e:
        return None


def get_real_time_quotes_all_stocks(time_out, use_proxy, must_all):
    try_numer = 3

    total_number = cache_service.get_cache(TOTAL_NUMBER_KEY)
    if total_number is None:
        while try_numer > 0:

            if use_proxy:
                proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
                initial_proxies = {"https": proxy_ip,
                                   "http": proxy_ip}
            else:
                initial_proxies = None

            result_dict = get_em_real_time_page_df(1, PAGE_SIZE, initial_proxies, time_out)
            if result_dict is not None:
                total_number = result_dict['total_number']
                if total_number > 0:
                    cache_service.set_cache(TOTAL_NUMBER_KEY, total_number)
                    break
            else:
                total_number = 0
                time.sleep(1)
                logger.error("获取实时行情数据异常")
            try_numer = try_numer - 1
        if total_number == 0:
            return pd.DataFrame()
    else:
        if use_proxy:
            proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
            initial_proxies = {"https": proxy_ip,
                               "http": proxy_ip}
        else:
            initial_proxies = None

    page_df = get_all_stock_ticker_data(initial_proxies, time_out, total_number, use_proxy, must_all)
    page_df = east_money_stock_common_api.rename_real_time_quotes_df(page_df)
    page_df.drop_duplicates('symbol', keep='last', inplace=True)
    return page_df


import mns_common.api.em.real_time.east_money_stock_common_api as east_money_stock_common_api

# 调用示例
if __name__ == "__main__":
    # 示例1：爬取第40页，每页20条（原需求）
    # crawl_eastmoney_stock_data(page_num=40, page_size=20)

    # 示例2：爬取第1页，每页50条，按成交量(f9)降序排序
    number = 1
    while True:
        stock_list_df = get_real_time_quotes_all_stocks(10, True, True)
        stock_list_df = east_money_stock_common_api.rename_real_time_quotes_df(stock_list_df)

        if stock_list_df.shape[0] > 0:
            logger.info('成功同步次数:{}', str(number))
        number = number + 1

    # 示例3：使用默认参数（第1页，每页20条，按涨跌幅降序）
    # crawl_eastmoney_stock_data()
