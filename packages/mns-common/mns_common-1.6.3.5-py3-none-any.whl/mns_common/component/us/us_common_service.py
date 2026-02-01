import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.v2.MongodbUtilV2 import MongodbUtilV2
import mns_common.constant.extra_income_db_name as extra_income_db_name
from datetime import datetime, timedelta

mongodbUtilV2_27019 = MongodbUtilV2('27019', extra_income_db_name.US_STOCK)
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')
import mns_common.utils.ip_util as ip_util


# 保存数据
def save_us_minute_data(us_df, col_name, symbol, insert_flag):
    us_df['symbol'] = symbol
    us_df['_id'] = symbol + '_' + us_df['time']
    us_df['close'] = round(us_df['close'], 3)
    us_df['high'] = round(us_df['high'], 3)
    us_df['low'] = round(us_df['low'], 3)
    us_df['open'] = round(us_df['open'], 3)
    us_df['volume'] = round(us_df['volume'], 0)
    us_df = us_df[[
        '_id',
        'open',
        'high',
        'low',
        'close',
        'volume',
        'symbol',
    ]]
    if insert_flag:
        mongodbUtilV2_27019.insert_mongo(us_df, col_name)
    else:
        mongodbUtilV2_27019.save_mongo(us_df, col_name)


# 0:星期一, 1:星期二, ..., 6:星期日
def get_us_last_trade_day():
    now_date = datetime.now()
    yesterday_date = now_date - timedelta(days=1)
    return yesterday_date.strftime('%Y-%m-%d')


def get_chinese_last_trade_day():
    now_date = datetime.now()
    return now_date.strftime('%Y-%m-%d')


# 是否是us stock day 不排除节假日 星期一到星期六
def is_us_trade_day():
    now_date = datetime.now()
    weekday_num = now_date.weekday()
    if 0 < weekday_num < 6:
        return True
    else:
        return False


# 获取us 数据库
def get_us_mongo_db():
    mac_address = ip_util.get_mac_address()
    if mac_address is not None and mac_address == ip_util.APPLE_AIR_MAC_ADDRESS:
        return mongodb_util
    else:
        return mongodbUtilV2_27019


if __name__ == '__main__':
    trade_day = get_us_last_trade_day()
    print(trade_day)
