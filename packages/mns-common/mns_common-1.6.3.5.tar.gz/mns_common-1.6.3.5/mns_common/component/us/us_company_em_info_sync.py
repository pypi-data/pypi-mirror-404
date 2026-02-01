import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

from loguru import logger
from datetime import datetime
import mns_common.constant.extra_income_db_name as extra_income_db_name
import mns_common.component.cookie.cookie_info_service as cookie_info_service
import mns_common.api.em.real_time.east_money_stock_us_api as east_money_stock_us_api
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.us.us_stock_etf_info_api as us_stock_etf_info_api
import mns_common.component.us.us_common_service as us_common_service

mongodb_util = us_common_service.get_us_mongo_db()


# 同步东方财富美股信息
def sync_em_us_stock_etf_info(exist_em_df):
    # 同步东方财富美股信息 todo 增加稳定接口
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    us_day = us_common_service.get_us_last_trade_day()
    logger.info("同步东方财富美股信息")
    em_cookie = cookie_info_service.get_em_cookie()
    if data_frame_util.is_not_empty(exist_em_df):
        us_stock_etf_info = exist_em_df.copy()
    else:
        us_stock_etf_info = east_money_stock_us_api.get_all_us_real_time_quotes(30, em_cookie)

    us_stock_etf_info.loc[us_stock_etf_info['industry'] == '-', 'industry'] = '其他'
    us_stock_etf_info.loc[us_stock_etf_info['industry'] == '-', 'industry_code'] = 'US0'

    us_stock_etf_info['sync_time'] = str_now_date
    us_stock_etf_info['us_day'] = us_day
    us_stock_etf_info = us_stock_etf_info.fillna(0)
    # 美股代码使用中划线  东财使用的下划线

    us_stock_etf_info['market_code_str'] = us_stock_etf_info['market_code'].astype(str)
    us_stock_etf_info['em_symbol'] = us_stock_etf_info['market_code_str'] + '.' + us_stock_etf_info['symbol']
    us_stock_etf_info['symbol'] = us_stock_etf_info['symbol'].str.replace('_', '-')
    us_stock_etf_info['_id'] = us_stock_etf_info['symbol']

    us_stock_etf_info = us_stock_etf_info[[
        "_id",
        "symbol",
        "name",
        "em_symbol",
        "industry",
        "industry_code",
        "list_date",
        "sync_time",
        "us_day",
        "market_code",
        "now_price",
        "chg",
        "change_price",
        "volume",
        "amount",
        "exchange",
        "pe_ttm",
        "quantity_ratio",
        "high",
        "low",
        "open",
        "yesterday_price",
        "voucher_type",
        "total_mv",
        "flow_mv",
        "wei_bi",
        "outer_disk",
        "inner_disk",
        "today_main_net_inflow",
        "super_large_order_net_inflow",
        "super_large_order_net_inflow_ratio",
        "large_order_net_inflow",
        "concept_name_str",
        "today_main_net_inflow_ratio",
        "average_price",
        "concept_code_str",
        "large_order_net_inflow_ratio",
        "disk_ratio",
        "disk_diff_amount"
    ]]

    # voucher_type= 1 美国本地公司
    # voucher_type= 2 优先股
    # voucher_type= 3 在多个市场上市的股票 如 阿里巴巴 台积电
    # voucher_type= 4 信托or基金
    # voucher_type= 5 ETF
    # voucher_type= 6  票据
    # voucher_type= 8   权证
    # voucher_type= 9 债务证券
    # voucher_type= 10 持股拥有完整投票权 BRK.A (伯克希尔哈撒韦 - A)：公司原始股票
    # BRK.B (伯克希尔哈撒韦 - B)：1996 年为满足中小投资者需求而发行，后经 2010 年 1 拆 50，进一步降低投资门槛，被称为 “Baby Berkshire”。
    # us stock
    us_stock_df = us_stock_etf_info.loc[us_stock_etf_info['voucher_type'].isin([1, 2, 3, 10])]
    us_etf_df = us_stock_etf_info.loc[~us_stock_etf_info['voucher_type'].isin([1, 2, 3, 10])]
    if data_frame_util.is_not_empty(us_stock_df):
        us_stock_df.reset_index(drop=True, inplace=True)
        mongodb_util.save_mongo(us_stock_df, extra_income_db_name.US_STOCK_INFO_EM)
        us_stock_df['_id'] = us_stock_df['symbol'] + '_' + us_day
        mongodb_util.save_mongo(us_stock_df, extra_income_db_name.US_STOCK_INFO_EM + '_his')
    # us etf
    if data_frame_util.is_not_empty(us_etf_df):
        us_etf_df.reset_index(drop=True, inplace=True)
        del us_etf_df['industry']
        del us_etf_df['industry_code']
        del us_etf_df['concept_code_str']
        del us_etf_df['concept_name_str']
        del us_etf_df['pe_ttm']
        mongodb_util.save_mongo(us_etf_df, extra_income_db_name.US_ETF_INFO_EM)

        us_etf_df['_id'] = us_etf_df['symbol'] + '_' + us_day
        mongodb_util.save_mongo(us_etf_df, extra_income_db_name.US_ETF_INFO_EM + '_his')
    return us_stock_etf_info


# 同步alpha_vantage美股信息
def sync_us_alpha_stock_etf_list():
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    us_day = us_common_service.get_us_last_trade_day()
    logger.info("同步alpha_vantage美股信息")

    us_alpha_stock_list_df = us_stock_etf_info_api.get_us_alpha_stock_list('SRMP19KUP24M8B0E')
    us_alpha_stock_list_df['_id'] = us_alpha_stock_list_df['symbol']

    us_alpha_stock_list_df['sync_time'] = str_now_date
    us_alpha_stock_list_df['us_day'] = us_day
    us_alpha_stock_list_df = us_alpha_stock_list_df.fillna(0)
    alpha_us_etf_info = us_alpha_stock_list_df.loc[us_alpha_stock_list_df['assetType'] == 'ETF']
    alpha_us_stock_info = us_alpha_stock_list_df.loc[us_alpha_stock_list_df['assetType'] == 'Stock']

    if data_frame_util.is_not_empty(alpha_us_stock_info):
        alpha_us_stock_info.reset_index(drop=True, inplace=True)
        mongodb_util.save_mongo(alpha_us_stock_info, extra_income_db_name.US_STOCK_INFO_ALPHA_VANTAGE)

    if data_frame_util.is_not_empty(alpha_us_etf_info):
        alpha_us_etf_info.reset_index(drop=True, inplace=True)
        mongodb_util.save_mongo(alpha_us_etf_info, extra_income_db_name.US_ETF_INFO_ALPHA_VANTAGE)


# 同步alpha_vantage美股退市信息
def sync_us_alpha_de_list():
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    us_day = us_common_service.get_us_last_trade_day()
    logger.info("同步alpha_vantage美股退市信息")
    us_alpha_stock_de_list = us_stock_etf_info_api.get_us_alpha_stock_de_list('SRMP19KUP24M8B0E')
    us_alpha_stock_de_list['_id'] = us_alpha_stock_de_list['symbol']
    us_alpha_stock_de_list['sync_time'] = str_now_date
    us_alpha_stock_de_list['us_day'] = us_day
    us_alpha_stock_de_list = us_alpha_stock_de_list.fillna(0)

    if data_frame_util.is_not_empty(us_alpha_stock_de_list):
        us_alpha_stock_de_list.reset_index(drop=True, inplace=True)
        mongodb_util.save_mongo(us_alpha_stock_de_list, extra_income_db_name.US_DE_LIST_INFO_ALPHA_VANTAGE)


if __name__ == '__main__':
    sync_em_us_stock_etf_info(None)
    sync_us_alpha_stock_etf_list()
    sync_us_alpha_de_list()
