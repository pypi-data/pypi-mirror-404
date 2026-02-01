import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from loguru import logger
import requests
import time
import mns_common.component.proxies.proxy_common_api as proxy_common_api
import mns_common.utils.data_frame_util as data_frame_util

# 分页条数
page_number = 100

fields = ("f352,f2,f3,f5,f6,f8,f10,f13,f12,f14,f15,f16,f17,f18,f20,f21,f26,"
          "f33,f34,f35,f62,f66,f69,f72,f100,f184,f103,f383,f4,f9,f19,f265")


# fields_02 = "f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f19,f20,f21,f22,f23,f24,f25,f26,f27,f28,f29,f30,f31,f32,f33,f34,f35,f36,f37,f38,f39,f40,f41,f42,f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65,f66,f67,f68,f69,f70,f71,f72,f73,f74,f75,f76,f77,f78,f79,f80,f81,f82,f83,f84,f85,f86,f87,f88,f89,f90,f91,f92,f93,f94,f95,f96,f97,f98,f99,f100,f101,f102,f103,f104,f105,f106,f107,f108" \
#             ",f109,f110,f111,f112,f113,f114,f115,f116,f117,f118,f119,f120,f121,f122,f123,f124,f125,f126,f127,f128,f129,f130,f131,f132,f133,f134,f135,f136,f137,f138,f139,f140,f141,f142,f143,f144,f145,f146,f147,f148,f149,f150,f151,f152,f153,f154,f155,f156,f157,f158,f159,f160,f161,f162,f163,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183,f184,f185,f186,f187,f188,f189,f190,f191,f192,f193,f194,f195,f196,f197,f198,f199,f200,f201,f202,f203,f204,f205,f206,f207,f208" \
#             ",f209,f210,f211,f212,f213,f214,f215,f216,f217,f218,f219,f220,f221,f222,f223,f224,f225,f226,f227,f228,f229,f230,f231,f232,f233,f234,f235,f236,f237,f238,f239,f240,f241,f242,f243,f244,f245,f246,f247,f248,f249,f250,f251,f252,f253,f254,f255,f256,f257,f258,f259,f260,f261,f262,f263,f264,f265,f266,f267,f268,f269,f270,f271,f272,f273,f274,f275,f276,f277,f278,f279,f280,f281,f282,f283,f284,f285,f286,f287,f288,f289,f290,f291,f292,f293,f294,f295,f296,f297,f298,f299,f300,f301,f302,f303,f304,f305,f306,f307,f308" \
#             ",f309,f310,f311,f312,f313,f314,f315,f316,f317,f318,f319,f320,f321,f322,f323,f324,f325,f326,f327,f328,f329,f330,f331,f332,f333,f334,f335,f336,f337,f338,f339,f340,f341,f342,f343,f344,f345,f346,f347,f348,f349,f350,f351,f352,f353,f354,f355,f356,f357,f358,f359,f360,f361,f362,f363,f364,f365,f366,f367,f368,f369,f370,f371,f372,f373,f374,f375,f376,f377,f378,f379,f380,f381,f382,f383,f384,f385,f386,f387,f388,f389,f390,f391,f392,f393,f394,f395,f396,f397,f398,f399,f400,f401,f402,f403,f404,f405,f406,f407,f408" \
#             ",f401"


def get_us_stock_count(pn, proxies, page_size, cookie, time_out):
    try:
        headers = {
            'Cookie': cookie
        }

        current_timestamp = str(int(round(time.time() * 1000, 0)))

        url = "https://72.push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": str(pn),
            "pz": str(page_size),
            "po": "1",
            "np": "2",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f12",
            "fs": "m:105,m:106,m:107",
            "fields": fields,
            "_": str(current_timestamp),
        }
        if proxies is None:
            r = requests.get(url, params=params, headers=headers, timeout=time_out)
        else:
            r = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=time_out)
        data_json = r.json()
        total_number = int(data_json['data']['total'])
        return total_number
    except Exception as e:
        logger.error("获取美股数量:{}", e)
        return 0


# 获取美股分页信息
def get_us_real_time_quotes_page_df(pn, proxies, page_size, cookie, time_out):
    try:
        headers = {
            'Cookie': cookie
        }

        current_timestamp = str(int(round(time.time() * 1000, 0)))

        url = "https://72.push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": str(pn),
            "pz": str(page_size),
            "po": "1",
            "np": "2",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f6",
            "fs": "m:105,m:106,m:107",
            "fields": fields,
            "_": str(current_timestamp),
        }
        if proxies is None:
            r = requests.get(url, params=params, headers=headers, timeout=time_out)
        else:
            r = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=time_out)
        data_json = r.json()
        if not data_json["data"]["diff"]:
            return pd.DataFrame()
        temp_df = pd.DataFrame(data_json["data"]["diff"]).T

        return temp_df
    except Exception as e:
        logger.error("获取美股实时行情异常:{}", e)
        return pd.DataFrame()


def rename_us_stock(temp_df):
    temp_df = temp_df.rename(columns={

        "f4": "change_price",
        "f9": "pe_ttm",

        # 1 美国本土公司 3 多个市场上市美股 如阿里巴巴 台积电  5 ETF
        "f19": "voucher_type",
        "f12": "symbol",
        "f14": "name",
        "f3": "chg",
        "f2": "now_price",
        "f5": "volume",
        "f6": "amount",
        "f8": "exchange",
        "f10": "quantity_ratio",
        "f13": "market_code",
        "f15": "high",
        "f16": "low",
        "f17": "open",
        "f18": "yesterday_price",
        "f20": "total_mv",
        "f21": "flow_mv",
        "f26": "list_date",
        "f33": "wei_bi",
        "f34": "outer_disk",
        "f35": "inner_disk",
        "f62": "today_main_net_inflow",
        "f66": "super_large_order_net_inflow",
        "f69": "super_large_order_net_inflow_ratio",
        "f72": "large_order_net_inflow",
        # "f78": "medium_order_net_inflow",
        # "f84": "small_order_net_inflow",
        "f100": "industry",
        "f265": "industry_code",
        "f103": "concept_name_str",
        "f383": "concept_code_str",
        "f184": "today_main_net_inflow_ratio",
        "f352": "average_price",
    })

    temp_df.loc[temp_df['average_price'] == '-', 'average_price'] = 0
    temp_df.loc[temp_df['wei_bi'] == '-', 'wei_bi'] = 0
    temp_df.loc[temp_df['yesterday_price'] == '-', 'yesterday_price'] = 0
    temp_df.loc[temp_df['now_price'] == '-', 'now_price'] = 0
    temp_df.loc[temp_df['chg'] == '-', 'chg'] = 0
    temp_df.loc[temp_df['volume'] == '-', 'volume'] = 0
    temp_df.loc[temp_df['amount'] == '-', 'amount'] = 0
    temp_df.loc[temp_df['exchange'] == '-', 'exchange'] = 0
    temp_df.loc[temp_df['quantity_ratio'] == '-', 'quantity_ratio'] = 0
    temp_df.loc[temp_df['high'] == '-', 'high'] = 0
    temp_df.loc[temp_df['low'] == '-', 'low'] = 0
    temp_df.loc[temp_df['open'] == '-', 'open'] = 0
    temp_df.loc[temp_df['total_mv'] == '-', 'total_mv'] = 0
    temp_df.loc[temp_df['flow_mv'] == '-', 'flow_mv'] = 0
    temp_df.loc[temp_df['inner_disk'] == '-', 'inner_disk'] = 0
    temp_df.loc[temp_df['outer_disk'] == '-', 'outer_disk'] = 0
    temp_df.loc[temp_df['today_main_net_inflow_ratio'] == '-', 'today_main_net_inflow_ratio'] = 0
    temp_df.loc[temp_df['today_main_net_inflow'] == '-', 'today_main_net_inflow'] = 0
    temp_df.loc[temp_df['super_large_order_net_inflow'] == '-', 'super_large_order_net_inflow'] = 0
    temp_df.loc[temp_df['super_large_order_net_inflow_ratio'] == '-', 'super_large_order_net_inflow_ratio'] = 0
    temp_df.loc[temp_df['large_order_net_inflow'] == '-', 'large_order_net_inflow'] = 0
    # temp_df.loc[temp_df['medium_order_net_inflow'] == '-', 'medium_order_net_inflow'] = 0
    # temp_df.loc[temp_df['small_order_net_inflow'] == '-', 'small_order_net_inflow'] = 0

    temp_df["list_date"] = pd.to_numeric(temp_df["list_date"], errors="coerce")
    temp_df["wei_bi"] = pd.to_numeric(temp_df["wei_bi"], errors="coerce")
    temp_df["average_price"] = pd.to_numeric(temp_df["average_price"], errors="coerce")
    temp_df["yesterday_price"] = pd.to_numeric(temp_df["yesterday_price"], errors="coerce")
    temp_df["now_price"] = pd.to_numeric(temp_df["now_price"], errors="coerce")
    temp_df["chg"] = pd.to_numeric(temp_df["chg"], errors="coerce")
    temp_df["volume"] = pd.to_numeric(temp_df["volume"], errors="coerce")
    temp_df["amount"] = pd.to_numeric(temp_df["amount"], errors="coerce")
    temp_df["exchange"] = pd.to_numeric(temp_df["exchange"], errors="coerce")
    temp_df["quantity_ratio"] = pd.to_numeric(temp_df["quantity_ratio"], errors="coerce")
    temp_df["high"] = pd.to_numeric(temp_df["high"], errors="coerce")
    temp_df["low"] = pd.to_numeric(temp_df["low"], errors="coerce")
    temp_df["open"] = pd.to_numeric(temp_df["open"], errors="coerce")
    temp_df["total_mv"] = pd.to_numeric(temp_df["total_mv"], errors="coerce")
    temp_df["flow_mv"] = pd.to_numeric(temp_df["flow_mv"], errors="coerce")
    temp_df["outer_disk"] = pd.to_numeric(temp_df["outer_disk"], errors="coerce")
    temp_df["inner_disk"] = pd.to_numeric(temp_df["inner_disk"], errors="coerce")
    temp_df["today_main_net_inflow"] = pd.to_numeric(temp_df["today_main_net_inflow"], errors="coerce")
    temp_df["super_large_order_net_inflow"] = pd.to_numeric(temp_df["super_large_order_net_inflow"],
                                                            errors="coerce")
    temp_df["super_large_order_net_inflow_ratio"] = pd.to_numeric(temp_df["super_large_order_net_inflow_ratio"],
                                                                  errors="coerce")
    temp_df["large_order_net_inflow"] = pd.to_numeric(temp_df["large_order_net_inflow"],
                                                      errors="coerce")
    # temp_df["medium_order_net_inflow"] = pd.to_numeric(temp_df["medium_order_net_inflow"],
    #                                                    errors="coerce")
    # temp_df["small_order_net_inflow"] = pd.to_numeric(temp_df["small_order_net_inflow"], errors="coerce")

    # 大单比例
    temp_df['large_order_net_inflow_ratio'] = round((temp_df['large_order_net_inflow'] / temp_df['amount']) * 100,
                                                    2)

    # 外盘是内盘倍数
    temp_df['disk_ratio'] = round((temp_df['outer_disk'] - temp_df['inner_disk']) / temp_df['inner_disk'], 2)
    # 只有外盘没有内盘
    temp_df.loc[temp_df["inner_disk"] == 0, ['disk_ratio']] = 1688
    temp_df['disk_diff_amount'] = round(
        (temp_df['outer_disk'] - temp_df['inner_disk']) * temp_df[
            "average_price"],
        2)
    return temp_df


def all_us_stock_ticker_data_new(initial_proxies, time_out, em_cookie, max_number) -> pd.DataFrame:
    """
    使用多线程获取所有股票数据，失败页面会使用新IP重试，最多使用10个IP
    """
    per_page = page_number
    total_pages = (max_number + per_page - 1) // per_page  # 向上取整
    all_pages = set(range(1, total_pages + 1))  # 所有需要获取的页码
    success_pages = set()  # 成功获取的页码
    results = []  # 存储成功获取的数据
    used_ip_count = 1  # 已使用IP计数器（初始IP算第一个）
    MAX_IP_LIMIT = 10  # IP使用上限

    # 循环处理直到所有页面成功或达到IP上限
    while (all_pages - success_pages) and (used_ip_count < MAX_IP_LIMIT):
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
            new_proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
            proxies = {"https": new_proxy_ip}
            # logger.info("新代理IP: {}, 已使用IP数量: {}/{}", new_proxy_ip, used_ip_count + 1, MAX_IP_LIMIT)
            used_ip_count += 1  # 增加IP计数器

        # 创建线程池处理当前失败的页码
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(get_us_real_time_quotes_page_df, pn, proxies,
                                per_page, em_cookie, time_out): pn
                for pn in current_failed_pages
            }

            # 收集结果并记录成功页码
            for future, pn in futures.items():
                try:
                    result = future.result()
                    if not result.empty:
                        results.append(result)
                        success_pages.add(pn)
                    # else:
                    #     logger.warning("页码 {} 未返回有效数据", pn)
                except Exception as e:
                    continue
                    # logger.error("页码 {} 处理异常: {}", pn, str(e))

    # 检查是否达到IP上限
    if used_ip_count >= MAX_IP_LIMIT and (all_pages - success_pages):
        remaining_pages = all_pages - success_pages
        logger.warning("已达到最大IP使用限制({}个)，剩余未获取页码: {}, 返回现有数据", MAX_IP_LIMIT, remaining_pages)

    # 合并所有成功获取的数据
    if results:
        return pd.concat(results, ignore_index=True)
    else:
        return pd.DataFrame()


def get_us_real_time_quotes(time_out, em_cookie):
    try_numer = 3
    while try_numer > 0:
        proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
        initial_proxies = {"https": proxy_ip,
                           "http": proxy_ip}

        max_number = get_us_stock_count(1, initial_proxies, 20, em_cookie, time_out)
        if max_number > 0:
            break
        try_numer = try_numer - 1
    if max_number == 0:
        return pd.DataFrame()
    all_hk_stock_ticker_data_new_df = all_us_stock_ticker_data_new(initial_proxies, time_out, em_cookie, max_number)
    return rename_us_stock(all_hk_stock_ticker_data_new_df)


# 使用代理ip同步数据
def get_all_us_real_time_quotes(time_out, em_cookie):
    try_numer = 3
    while try_numer > 0:
        proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
        initial_proxies = {"https": proxy_ip,
                           "http": proxy_ip}

        max_number = get_us_stock_count(1, initial_proxies, 20, em_cookie, time_out)
        if max_number > 0:
            break
        try_numer = try_numer - 1
    if max_number == 0:
        max_number = 13000
    total_pages = (max_number + page_number - 1) // page_number  # 向上取整

    results_df = pd.DataFrame()
    pn = 1
    while pn <= total_pages:
        try:
            page_df = get_us_real_time_quotes_page_df(pn, initial_proxies, page_number, em_cookie, time_out)
            while data_frame_util.is_empty(page_df):
                proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
                initial_proxies = {"https": proxy_ip,
                                   "http": proxy_ip}
                page_df = get_us_real_time_quotes_page_df(pn, initial_proxies, page_number, em_cookie, time_out)
                time.sleep(1)
            results_df = pd.concat([results_df, page_df])
            logger.info("同步美股第几{}页成功", pn)
            pn = pn + 1
        except BaseException as e:
            logger.error("同步美股信息失败:{},{}", e, pn)
    return rename_us_stock(results_df)


# 使用本地ip同步数据
def get_all_us_real_time_quotes_local_ip(time_out, em_cookie):
    try_numer = 3
    while try_numer > 0:
        max_number = get_us_stock_count(1, None, 20, em_cookie, time_out)
        if max_number > 0:
            break
        try_numer = try_numer - 1
    if max_number == 0:
        max_number = 13000
    total_pages = (max_number + page_number - 1) // page_number  # 向上取整

    results_df = pd.DataFrame()
    pn = 1
    while pn <= total_pages:
        try:
            page_df = get_us_real_time_quotes_page_df(pn, None, page_number, em_cookie, time_out)
            while data_frame_util.is_empty(page_df):
                page_df = get_us_real_time_quotes_page_df(pn, None, page_number, em_cookie, time_out)
                time.sleep(1)
            results_df = pd.concat([results_df, page_df])
            logger.info("同步美股第几{}页成功", pn)
            pn = pn + 1
        except BaseException as e:
            logger.error("同步美股信息失败:{},{}", e, pn)
    return rename_us_stock(results_df)


if __name__ == '__main__':
    cookie_test = 'qgqp_b_id=1e0d79428176ed54bef8434efdc0e8c3; mtp=1; ct=QVRY_s8Tiag1WfK2tSW2n03qpsX-PD8aH_rIjKVooawX8K33UVnpIofK088lD1lguWlE_OEIpQwn3PJWFPhHvSvyvYr4Zka3l4vxtZfH1Uikjtyy9z1H4Swo0rQzMKXncVzBXiOo5TjE-Dy9fcoG3ZF7UVdQ35jp_cFwzOlpK5Y; ut=FobyicMgeV51lVMr4ZJXvn-72bp0oeSOvtzifFY_U7kBFtR6og4Usd-VtBM5XBBvHq0lvd9xXkvpIqWro9EDKmv6cbKOQGyawUSMcKVP57isZCaM7lWQ6jWXajvTfvV4mIR-W_MZNK8VY0lL9W4qNMniJ6PBn_gkJsSAJCadmsyI9cxmjx--gR4m54pdF_nie_y4iWHys83cmWR2R7Bt1KKqB25OmkfCQTJJqIf7QsqangVGMUHwMC39Z9QhrfCFHKVNrlqS503O6b9GitQnXtvUdJhCmomu; pi=4253366368931142%3Bp4253366368931142%3B%E8%82%A1%E5%8F%8B9x56I87727%3BYNigLZRW%2FzMdGgVDOJbwReDWnTPHl51dB0gQLiwaCf1XY98mlJYx6eJbsoYr5Nie%2BX1L%2BzaMsec99KkX%2BT29Ds1arfST7sIBXxjUQ3dp11IPUnXy64PaBFRTHzMRWnCFJvvhc%2FAI41rXSGXolC8YMxI%2BvyPS%2BuErwgOVjC5vvsIiKeO7TLyKkhqqQJPX%2F7RWC5Sf3QLh%3Bdwjn4Xho10%2FKjqOgTWs%2FJF4%2FkdKzeuBwM8sz9aLvJovejAkCAyGMyGYA6AE67Xk2Ki7x8zdfBifF2DG%2Fvf2%2BXAYN8ZVISSEWTIXh32Z5MxEacK4JBTkqyiD93e1vFBOFQ82BqaiVmntUq0V6FrTUHGeh1gG5Sg%3D%3D; uidal=4253366368931142%e8%82%a1%e5%8f%8b9x56I87727; sid=170711377; vtpst=|; quote_lt=1; websitepoptg_api_time=1715777390466; emshistory=%5B%22%E8%BD%AC%E5%80%BA%E6%A0%87%22%2C%22%E8%BD%AC%E5%80%BA%E6%A0%87%E7%9A%84%22%5D; st_si=00364513876913; st_asi=delete; HAList=ty-116-00700-%u817E%u8BAF%u63A7%u80A1%2Cty-1-688695-%u4E2D%u521B%u80A1%u4EFD%2Cty-1-600849-%u4E0A%u836F%u8F6C%u6362%2Cty-1-603361-%u6D59%u6C5F%u56FD%u7965%2Cty-1-603555-ST%u8D35%u4EBA%2Cty-0-000627-%u5929%u8302%u96C6%u56E2%2Cty-0-002470-%u91D1%u6B63%u5927%2Cty-0-832876-%u6167%u4E3A%u667A%u80FD%2Cty-0-300059-%u4E1C%u65B9%u8D22%u5BCC%2Cty-107-CWB-%u53EF%u8F6C%u503AETF-SPDR; st_pvi=26930719093675; st_sp=2024-04-28%2017%3A27%3A05; st_inirUrl=https%3A%2F%2Fcn.bing.com%2F; st_sn=23; st_psi=20240517111108288-113200301321-2767127768'
    get_all_us_real_time_quotes(30, cookie_test)
    page_test_df = get_us_real_time_quotes_page_df(1, None, 100, cookie_test, 30)
    page_test_df = rename_us_stock(page_test_df)

    us_test_df = get_us_real_time_quotes(30, cookie_test)
    # us_test_df = get_us_real_time_quotes_page_df(1, None, 200, cookie_test, 30)
    print(us_test_df)
