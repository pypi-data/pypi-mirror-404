import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import akshare as ak
import pandas as pd
from loguru import logger


# 获取外汇表
def get_foreign_exchange():
    try:
        forex_spot_em_df = ak.forex_spot_em()
        forex_spot_em_df.rename(columns={"序号": "index",
                                         "代码": "symbol",
                                         "名称": "name",
                                         "最新价": "now_price",
                                         "涨跌额": "chg_price",
                                         "涨跌幅": "chg",
                                         "今开": "open",
                                         "最高": "high",
                                         "最低": "low",
                                         "昨收": "last_price",

                                         }, inplace=True)
        return forex_spot_em_df
    except BaseException as e:
        logger.error("获取外汇信息异常:{}", e)
        return pd.DataFrame()



if __name__ == '__main__':
    test_df=get_foreign_exchange()
    print(test_df)
