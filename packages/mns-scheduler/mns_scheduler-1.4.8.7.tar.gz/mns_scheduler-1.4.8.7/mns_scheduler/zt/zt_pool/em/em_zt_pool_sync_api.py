import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import mns_common.api.akshare.stock_zt_pool_api as stock_zt_pool_api
import mns_common.utils.date_handle_util as date_handle_util
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.company.company_common_service_api as company_common_service_api
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
import mns_common.api.ths.zt.ths_stock_zt_pool_v2_api as ths_stock_zt_pool_v2_api
import mns_common.component.zt.zt_common_service_api as zt_common_service_api
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.main_line.main_line_zt_reason_service as main_line_zt_reason_service
import mns_scheduler.zt.zt_pool.em.em_zt_pool_service as em_zt_pool_service

'''
东方财富涨停池
'''

mongodb_util = MongodbUtil('27017')


# 保存东财涨停股票
def save_zt_info(str_day):
    if bool(1 - trade_date_common_service_api.is_trade_day(str_day)):
        return pd.DataFrame()

    stock_em_zt_pool_df_data = stock_zt_pool_api.stock_em_zt_pool_df(
        date_handle_util.no_slash_date(str_day))

    # 处理丢失的涨停数据 通过今日实时数据
    stock_em_zt_pool_df_data = em_zt_pool_service.handle_miss_zt_data_by_real_time(stock_em_zt_pool_df_data.copy(),
                                                                                   str_day)

    query_ths_zt = {'str_day': str_day}
    ths_zt_pool_df_data = mongodb_util.find_query_data(db_name_constant.THS_ZT_POOL, query_ths_zt)

    if data_frame_util.is_empty(ths_zt_pool_df_data):
        try:

            # 同花顺问财涨停池
            ths_zt_pool_df_data = ths_stock_zt_pool_v2_api.get_ths_stock_zt_reason_with_cache(str_day)
        except BaseException as e:
            logger.error("使用问财同步ths涨停数据异常:{}", e)
            ths_zt_pool_df_data = pd.DataFrame()

    # 更新涨停金额
    stock_em_zt_pool_df_data = em_zt_pool_service.update_closure_funds(stock_em_zt_pool_df_data,
                                                                       ths_zt_pool_df_data)
    # 处理东财涨停池丢失的数据 同花顺有的
    stock_em_zt_pool_df_data = em_zt_pool_service.handle_ths_em_diff_data(ths_zt_pool_df_data, stock_em_zt_pool_df_data)

    stock_em_zt_pool_df_data = common_service_fun_api.total_mv_classification(stock_em_zt_pool_df_data.copy())

    stock_em_zt_pool_df_data = common_service_fun_api.classify_symbol(stock_em_zt_pool_df_data.copy())

    stock_em_zt_pool_df_data = common_service_fun_api.symbol_amount_simple(stock_em_zt_pool_df_data.copy())

    stock_em_zt_pool_df_data = company_common_service_api.amendment_industry(stock_em_zt_pool_df_data.copy())

    # 上个交易交易日涨停股票
    last_trade_day_zt_df = zt_common_service_api.get_last_trade_day_zt(str_day)
    # 设置连板
    stock_em_zt_pool_df_data = em_zt_pool_service.set_connected_boards_numbers(stock_em_zt_pool_df_data.copy(),
                                                                               last_trade_day_zt_df.copy())

    # 添加主线信息
    stock_em_zt_pool_df_data = main_line_zt_reason_service.merge_main_line_info(str_day,
                                                                                stock_em_zt_pool_df_data.copy())
    # 添加涨停原因和分析信息
    stock_em_zt_pool_df_data = main_line_zt_reason_service.merge_zt_reason_info(str_day,
                                                                                stock_em_zt_pool_df_data.copy())

    stock_em_zt_pool_df_data['first_closure_time'] = stock_em_zt_pool_df_data['first_closure_time'].str.strip()
    stock_em_zt_pool_df_data['list_date'] = stock_em_zt_pool_df_data['list_date'].apply(
        lambda x: pd.to_numeric(x, errors="coerce"))

    stock_em_zt_pool_df_data['new_stock'] = False
    # 将日期数值转换为日期时间格式
    stock_em_zt_pool_df_data['list_date_01'] = pd.to_datetime(stock_em_zt_pool_df_data['list_date'], format='%Y%m%d')
    str_day_date = date_handle_util.str_to_date(str_day, '%Y-%m-%d')
    # 计算日期差值 距离现在上市时间
    stock_em_zt_pool_df_data['diff_days'] = stock_em_zt_pool_df_data.apply(
        lambda row: (str_day_date - row['list_date_01']).days, axis=1)
    # 上市时间小于100天为新股
    stock_em_zt_pool_df_data.loc[
        stock_em_zt_pool_df_data["diff_days"] < 100, ['new_stock']] \
        = True
    stock_em_zt_pool_df_data = stock_em_zt_pool_df_data.dropna(subset=['diff_days'], axis=0, inplace=False)

    # 按照"time"列进行排序，同时将值为0的数据排到最末尾
    stock_em_zt_pool_df_data = stock_em_zt_pool_df_data.sort_values(by=['first_closure_time'])

    # 重置索引，并将排序结果保存到新的"index"列中
    stock_em_zt_pool_df_data['str_day'] = str_day
    stock_em_zt_pool_df_data['_id'] = stock_em_zt_pool_df_data['symbol'] + "_" + str_day
    stock_em_zt_pool_df_data.drop_duplicates('symbol', keep='last', inplace=True)

    # 保存数据
    em_zt_pool_service.update_zt_pool_data(str_day, stock_em_zt_pool_df_data)

    stock_em_zt_pool_df_data.fillna('', inplace=True)
    stock_em_zt_pool_df_data = stock_em_zt_pool_df_data[em_zt_pool_service.ZT_FIELD]
    return stock_em_zt_pool_df_data


# 更新今日涨停相关的信息
def update_today_zt_relation_info(str_day):
    if bool(1 - trade_date_common_service_api.is_trade_day(str_day)):
        return pd.DataFrame()

    stock_em_zt_pool_df_data = stock_zt_pool_api.stock_em_zt_pool_df(
        date_handle_util.no_slash_date(str_day))

    # 保存连板股票主线
    main_line_zt_reason_service.save_last_trade_day_main_line(str_day, stock_em_zt_pool_df_data)

    # 异步 更新涨停分析和原因数据
    em_zt_pool_service.update_zt_reason_analysis(stock_em_zt_pool_df_data, str_day)


if __name__ == '__main__':
    update_today_zt_relation_info('2026-01-13')
