import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil
from mns_common.component.cookie.cookie_enum import CookieEnum

mongodb_util = MongodbUtil('27017')


# ths cookie
def get_ths_cookie():
    stock_account_info = mongodb_util.find_query_data('stock_account_info',
                                                      {"type": CookieEnum.THS_COOKIE.cookie_code})
    ths_cookie = list(stock_account_info['cookie'])[0]
    return ths_cookie


# 东财 cookie
def get_em_cookie():
    stock_account_info = mongodb_util.find_query_data('stock_account_info',
                                                      {"type": CookieEnum.EM_COOKIE.cookie_code})
    em_cookie = list(stock_account_info['cookie'])[0]
    return em_cookie


# 雪球 cookie
def get_xue_qiu_cookie():
    stock_account_info = mongodb_util.find_query_data('stock_account_info',
                                                      {"type": CookieEnum.XUE_QIU_COOKIE.cookie_code })
    cookie = list(stock_account_info['cookie'])[0]
    return cookie


# 开盘啦 token
def get_kpl_cookie():
    stock_account_info = mongodb_util.find_query_data('stock_account_info',
                                                      {"type": CookieEnum.KPL_COOKIE.cookie_code, })
    cookie = list(stock_account_info['cookie'])[0]
    return cookie
