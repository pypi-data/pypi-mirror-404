import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from datetime import datetime
import mns_common.component.tfp.stock_tfp_api as stock_tfp_api
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.utils.data_frame_util as data_frame_util
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.common_service_fun_api as common_service_fun_api

mongodb_util = MongodbUtil('27017')


def sync_stock_tfp(str_day):
    if str_day is None:
        now_date = datetime.now()
        last_year = now_date.year - 1
        init_str_day = str(last_year) + '-01' + '-01'
        stock_tfp_df = stock_tfp_api.get_stock_tfp_by_day(init_str_day)
        str_day = now_date.strftime('%Y-%m-%d')
        stock_tfp_df = handle_tfp_data(stock_tfp_df.copy(), str_day, 1)
    else:
        stock_tfp_df = stock_tfp_api.get_stock_tfp_by_day(str_day)
        stock_tfp_df = handle_tfp_data(stock_tfp_df.copy(), str_day, 2)

    return stock_tfp_df


def handle_tfp_data(stock_tfp_df, str_day, time_classify):
    if data_frame_util.is_not_empty(stock_tfp_df):
        stock_tfp_df['sus_begin_time'] = stock_tfp_df['sus_begin_time'].fillna('无')
        stock_tfp_df['sus_end_time'] = stock_tfp_df['sus_end_time'].fillna('无')
        stock_tfp_df['resume_time'] = stock_tfp_df['resume_time'].fillna('无')
        stock_tfp_df['_id'] = stock_tfp_df['symbol'] + "_" + str_day
        # 排除name列中值包含'B'的行
        stock_tfp_df = stock_tfp_df[~stock_tfp_df['name'].str.contains('B', na=False)]

        stock_tfp_df['sus_begin_time'] = stock_tfp_df['sus_begin_time'].astype(str)
        stock_tfp_df['sus_end_time'] = stock_tfp_df['sus_end_time'].astype(str)
        stock_tfp_df['resume_time'] = stock_tfp_df['resume_time'].astype(str)
        stock_tfp_df['sus_begin_date'] = stock_tfp_df['sus_begin_date'].astype(str)
        stock_tfp_df = common_service_fun_api.exclude_st_symbol(stock_tfp_df)
        # 根据条件设置新列'type'的值

        # 初始化类型值
        stock_tfp_df['type'] = '0'
        stock_tfp_df.loc[stock_tfp_df['sus_reason'] == '盘中停牌', 'type'] = '0'
        stock_tfp_df.loc[stock_tfp_df['sus_reason'] == '停牌一天', 'type'] = '1'
        stock_tfp_df.loc[stock_tfp_df['sus_reason'] == '连续停牌', 'type'] = '2'
        stock_tfp_df.loc[stock_tfp_df['sus_reason'] == '刊登重要公告', 'type'] = '3'
        stock_tfp_df.loc[stock_tfp_df['sus_reason'] == '拟筹划重大资产重组', 'type'] = '4'
        stock_tfp_df.loc[stock_tfp_df['sus_reason'] == '交易异常波动', 'type'] = '5'
        stock_tfp_df['valid'] = True
        stock_tfp_df['str_day'] = str_day
        stock_tfp_df.loc[stock_tfp_df['type'] == '2', 'valid'] = False
        stock_tfp_df.loc[stock_tfp_df['type'] == '1', 'valid'] = False

        if time_classify == 1:
            stock_tfp_df = stock_tfp_df.loc[(stock_tfp_df['sus_begin_time'] >= str_day)
                                            | (stock_tfp_df['sus_end_time'] >= str_day)
                                            | (stock_tfp_df['resume_time'] >= str_day)
                                            | (stock_tfp_df['sus_begin_date'] >= str_day)]

            stock_tfp_df = stock_tfp_df.loc[stock_tfp_df['sus_period'] != '盘中停牌']
        # 停复牌
        stock_tfp_df = stock_tfp_df.fillna(0)
        mongodb_util.save_mongo(stock_tfp_df, db_name_constant.STOCK_TFP_INFO)
        return stock_tfp_df


if __name__ == '__main__':
    df = sync_stock_tfp(None)
    print(df)
