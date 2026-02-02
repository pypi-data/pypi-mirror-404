import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')
import mns_common.utils.data_frame_util as data_frame_util
from loguru import logger
import time
import mns_common.component.main_line.main_line_zt_reason_service as main_line_zt_reason_service


def update_null_zt_reason(str_day):
    query = {"str_day": str_day, "$or": [{"zt_reason": "0"},
                                         {"zt_reason": ""},
                                         {"zt_reason": float('nan')},

                                         {"zt_analysis": "0"},
                                         {"zt_analysis": ""},
                                         {"zt_analysis": float('nan')},

                                         ]}
    stock_zt_pool_df_null_zt_reason = mongodb_util.find_query_data('stock_zt_pool', query)
    no_reason_list = []
    if data_frame_util.is_not_empty(stock_zt_pool_df_null_zt_reason):
        no_reason_list = list(stock_zt_pool_df_null_zt_reason['symbol'])

    # 比较两个表
    query_zt_reason_analysis = {"str_day": str_day}
    stock_zt_pool_df_exist = mongodb_util.find_query_data('stock_zt_pool', query_zt_reason_analysis)
    stock_zt_reason_df = mongodb_util.find_query_data('zt_reason_analysis', query_zt_reason_analysis)
    if data_frame_util.is_not_empty(stock_zt_pool_df_exist):
        if data_frame_util.is_empty(stock_zt_reason_df):
            no_reason_list.extend(list(stock_zt_pool_df_exist['symbol']))
        else:
            not_in_zt_reason_zf = stock_zt_pool_df_exist.loc[~stock_zt_pool_df_exist['symbol']
            .isin(stock_zt_reason_df['symbol'])]
            if data_frame_util.is_not_empty(not_in_zt_reason_zf):
                no_reason_list.extend(list(not_in_zt_reason_zf['symbol']))

            null_zt_reason_df = stock_zt_reason_df.loc[(stock_zt_reason_df['zt_reason'] == '')
                                                       | (stock_zt_reason_df['zt_analysis'] == '')]
            if data_frame_util.is_not_empty(null_zt_reason_df):
                no_reason_list.extend(list(null_zt_reason_df['symbol']))

    for symbol in no_reason_list:
        try:

            need_update_zt_pool_df = stock_zt_pool_df_exist.loc[
                stock_zt_pool_df_exist['symbol'].isin([symbol])]
            main_line_zt_reason_service.update_symbol_list_zt_reason_analysis(need_update_zt_pool_df, True)
            time.sleep(2)

            query_zt = {'symbol': symbol, 'str_day': str_day}
            zt_reason_analysis_one_df = mongodb_util.find_query_data('zt_reason_analysis', query_zt)
            if data_frame_util.is_empty(zt_reason_analysis_one_df):
                continue
            zt_analysis = list(zt_reason_analysis_one_df['zt_analysis'])[0]
            zt_reason = list(zt_reason_analysis_one_df['zt_reason'])[0]
            new_values = {'$set': {
                'zt_analysis': zt_analysis,
                'zt_reason': zt_reason
            }}
            mongodb_util.update_many(query_zt, new_values, 'stock_zt_pool')
            mongodb_util.update_many(query_zt, new_values, 'main_line_detail')

            if symbol in no_reason_list:
                no_reason_list.remove(symbol)
        except BaseException as e:
            logger.error("出现异常:{},{}", symbol, e)
            continue


if __name__ == '__main__':
    update_null_zt_reason('2026-01-12')
