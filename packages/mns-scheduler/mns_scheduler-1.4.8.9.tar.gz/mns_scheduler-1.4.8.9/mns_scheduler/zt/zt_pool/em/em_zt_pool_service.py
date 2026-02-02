import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import pandas as pd
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.company.company_common_service_api as company_common_service_api
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.em.em_real_time_quotes_api as em_real_time_quotes_api
from datetime import datetime
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.deal.deal_service_api as deal_service_api
import mns_common.component.company.company_common_service_new_api as company_common_service_new_api
import mns_common.component.main_line.main_line_zt_reason_service as main_line_zt_reason_service
from mns_common.utils.async_fun import async_fun

mongodb_util = MongodbUtil('27017')
ZT_FIELD = ['_id', 'symbol', 'name', 'now_price', 'chg', 'first_closure_time',
            'last_closure_time', 'connected_boards_numbers',
            'zt_reason', 'zt_analysis', 'closure_funds',
            # 'closure_funds_per_amount', 'closure_funds_per_flow_mv',
            'frying_plates_numbers',
            # 'statistics_detail', 'zt_type', 'market_code',
            'statistics',
            # 'zt_flag',
            'industry', 'first_sw_industry',
            'second_sw_industry',
            'third_sw_industry', 'ths_concept_name',
            'ths_concept_code', 'ths_concept_sync_day', 'em_industry',
            'mv_circulation_ratio', 'ths_concept_list_info', 'kpl_plate_name',
            'kpl_plate_list_info', 'company_type', 'diff_days', 'amount',
            'list_date',
            'exchange', 'flow_mv', 'total_mv',
            'classification', 'flow_mv_sp', 'total_mv_sp', 'flow_mv_level',
            'amount_level', 'new_stock', 'list_date_01', 'index', 'str_day', 'main_line', 'sub_main_line']


# 处理东财涨停池丢失的数据 同花顺有的
def handle_ths_em_diff_data(ths_zt_pool_df_data, stock_em_zt_pool_df_data):
    if data_frame_util.is_empty(ths_zt_pool_df_data):
        return stock_em_zt_pool_df_data
    else:
        diff_ths_zt_df = ths_zt_pool_df_data.loc[
            ~(ths_zt_pool_df_data['symbol'].isin(stock_em_zt_pool_df_data['symbol']))]
        if data_frame_util.is_empty(diff_ths_zt_df):
            return stock_em_zt_pool_df_data
        else:
            diff_ths_zt_df = diff_ths_zt_df[[
                'symbol',
                'name',
                'chg',
                'now_price',
                # 'amount',
                # 'flow_mv',
                # 'total_mv',
                # 'exchange',
                'closure_funds',
                'first_closure_time',
                'last_closure_time',
                'frying_plates_numbers',
                'statistics',
                'connected_boards_numbers'

            ]]

            company_info_df = query_company_info_with_share()
            company_info_df['symbol'] = company_info_df['_id']
            company_info_df = company_info_df.loc[company_info_df['symbol'].isin(list(diff_ths_zt_df['symbol']))]

            company_info_df = common_service_fun_api.add_after_prefix(company_info_df)

            symbol_prefix_list = list(company_info_df['symbol_prefix'])
            real_time_quotes_list = deal_service_api.get_qmt_real_time_quotes_detail('qmt',
                                                                                     symbol_prefix_list)

            real_time_quotes_df = pd.DataFrame(real_time_quotes_list)

            real_time_quotes_df['symbol'] = real_time_quotes_df['symbol'].str.slice(0, 6)
            company_info_df = company_info_df.set_index(['symbol'], drop=True)
            real_time_quotes_df = real_time_quotes_df.set_index(['symbol'], drop=False)

            real_time_quotes_df = pd.merge(company_info_df, real_time_quotes_df, how='outer',
                                           left_index=True, right_index=True)

            real_time_quotes_df['amount'] = round(real_time_quotes_df['amount'], 1)

            real_time_quotes_df['total_mv'] = round(
                real_time_quotes_df['lastPrice'] * real_time_quotes_df['total_share'], 1)
            real_time_quotes_df['flow_mv'] = round(real_time_quotes_df['lastPrice'] * real_time_quotes_df['flow_share'],
                                                   1)
            real_time_quotes_df['exchange'] = round(
                real_time_quotes_df['amount'] * 100 / real_time_quotes_df['flow_mv'], 1)

            real_time_quotes_df = real_time_quotes_df[
                ['symbol', 'amount', 'total_mv', 'flow_mv', 'exchange', 'industry']]

            real_time_quotes_df = real_time_quotes_df.set_index(['symbol'], drop=True)
            diff_ths_zt_df = diff_ths_zt_df.set_index(['symbol'], drop=False)
            diff_ths_zt_df = pd.merge(real_time_quotes_df, diff_ths_zt_df, how='outer',
                                      left_index=True, right_index=True)

            diff_ths_zt_df = diff_ths_zt_df[[
                'symbol',
                'name',
                'chg',
                'now_price',
                'amount',
                'flow_mv',
                'total_mv',
                'exchange',
                'closure_funds',
                'first_closure_time',
                'last_closure_time',
                'frying_plates_numbers',
                'statistics',
                'connected_boards_numbers',
                'industry'

            ]]

            exist_number = stock_em_zt_pool_df_data.shape[0] + 1

            diff_ths_zt_df.index = range(exist_number, exist_number + len(diff_ths_zt_df))
            diff_ths_zt_df['index'] = diff_ths_zt_df.index

            stock_em_zt_pool_df_data = pd.concat([stock_em_zt_pool_df_data, diff_ths_zt_df])
            return stock_em_zt_pool_df_data


def query_company_info_with_share():
    query_field = {"_id": 1,
                   "industry": 1,
                   "company_type": 1,
                   "ths_industry_code": 1,
                   "ths_concept_name": 1,
                   "ths_concept_code": 1,
                   "ths_concept_sync_day": 1,
                   "first_sw_industry": 1,
                   "second_sw_industry": 1,
                   "second_industry_code": 1,
                   "third_sw_industry": 1,
                   "mv_circulation_ratio": 1,
                   "list_date": 1,
                   "diff_days": 1,
                   'em_industry': 1,
                   'operate_profit': 1,
                   'total_operate_income': 1,
                   "name": 1,
                   'pb': 1,
                   'pe_ttm': 1,
                   'ROE': 1,
                   'ths_industry_name': 1,
                   'total_share': 1,
                   'flow_share': 1
                   }
    de_list_company_symbols = company_common_service_new_api.get_de_list_company()
    query_field_key = str(query_field)
    query = {"_id": {"$regex": "^[^48]"},
             'symbol': {"$nin": de_list_company_symbols}, }
    query_key = str(query)
    company_info_df = company_common_service_new_api.get_company_info_by_field(query_key, query_field_key)

    return company_info_df


# 设置连板数目
def set_connected_boards_numbers(stock_em_zt_pool_df_data, last_trade_day_zt_df):
    if data_frame_util.is_empty(stock_em_zt_pool_df_data):
        return stock_em_zt_pool_df_data
    if data_frame_util.is_empty(last_trade_day_zt_df):
        return stock_em_zt_pool_df_data
    # 连板股票
    connected_boards_df_copy = last_trade_day_zt_df.loc[
        last_trade_day_zt_df['symbol'].isin(stock_em_zt_pool_df_data['symbol'])]

    connected_boards_df = connected_boards_df_copy.copy()
    #
    connected_boards_df['connected_boards_numbers'] = connected_boards_df['connected_boards_numbers'] + 1

    symbol_mapping_connected_boards_numbers = dict(
        zip(connected_boards_df['symbol'], connected_boards_df['connected_boards_numbers']))
    # 使用map进行替换，不匹配的保持原值
    stock_em_zt_pool_df_data['connected_boards_numbers'] = stock_em_zt_pool_df_data['symbol'].map(
        symbol_mapping_connected_boards_numbers).fillna(1)
    return stock_em_zt_pool_df_data


# 处理丢失的涨停数据 通过今日实时数据
def handle_miss_zt_data_by_real_time(stock_em_zt_pool_df_data, str_day):
    now_date = datetime.now()
    now_day = now_date.strftime('%Y-%m-%d')
    if now_day == str_day:
        real_time_quotes_all_stocks_df = em_real_time_quotes_api.get_real_time_quotes_now(None, None)
        if data_frame_util.is_empty(real_time_quotes_all_stocks_df):
            return stock_em_zt_pool_df_data
        real_time_quotes_all_stocks_df = real_time_quotes_all_stocks_df.loc[
            (real_time_quotes_all_stocks_df['wei_bi'] == 100) & (real_time_quotes_all_stocks_df['chg'] >= 9)]
        miss_zt_data_df_copy = real_time_quotes_all_stocks_df.loc[~(
            real_time_quotes_all_stocks_df['symbol'].isin(stock_em_zt_pool_df_data['symbol']))]
        miss_zt_data_df = miss_zt_data_df_copy.copy()
        if data_frame_util.is_not_empty(miss_zt_data_df):
            miss_zt_data_df['buy_1_num'] = miss_zt_data_df['buy_1_num'].astype(float)
            miss_zt_data_df['now_price'] = miss_zt_data_df['now_price'].astype(float)
            miss_zt_data_df['closure_funds'] = round(miss_zt_data_df['buy_1_num'] * 100 * miss_zt_data_df['now_price'],
                                                     2)

            company_info_industry_df = company_common_service_api.get_company_info_name()
            company_info_industry_df = company_info_industry_df.loc[
                company_info_industry_df['_id'].isin(miss_zt_data_df['symbol'])]

            company_info_industry_df = company_info_industry_df[['_id', 'industry', 'name']]

            company_info_industry_df = company_info_industry_df.set_index(['_id'], drop=True)
            miss_zt_data_df = miss_zt_data_df.set_index(['symbol'], drop=False)

            miss_zt_data_df = pd.merge(miss_zt_data_df, company_info_industry_df, how='outer',
                                       left_index=True, right_index=True)

            miss_zt_data_df = miss_zt_data_df[[
                'symbol',
                'name',
                'chg',
                'now_price',
                'amount',
                'flow_mv',
                'total_mv',
                'exchange',
                'industry',
                'closure_funds'

            ]]
            miss_zt_data_df['index'] = 10000
            miss_zt_data_df['first_closure_time'] = '150000'
            miss_zt_data_df['last_closure_time'] = '150000'
            miss_zt_data_df['statistics'] = '1/1'
            miss_zt_data_df['frying_plates_numbers'] = 0
            miss_zt_data_df['connected_boards_numbers'] = 0

            stock_em_zt_pool_df_data = pd.concat([miss_zt_data_df, stock_em_zt_pool_df_data])
        return stock_em_zt_pool_df_data
    else:
        return stock_em_zt_pool_df_data


# 更新涨停金额
def update_closure_funds(stock_em_zt_pool_df_data, ths_zt_pool_df_data):
    if data_frame_util.is_empty(ths_zt_pool_df_data) or data_frame_util.is_empty(stock_em_zt_pool_df_data):
        return stock_em_zt_pool_df_data
    ths_zt_pool_df_data['closure_funds'] = ths_zt_pool_df_data['closure_funds'].astype(float)

    symbol_mapping_zt_closure_funds = dict(
        zip(ths_zt_pool_df_data['closure_funds'], ths_zt_pool_df_data['closure_funds']))

    stock_em_zt_pool_df_data['closure_funds'] = stock_em_zt_pool_df_data['symbol'].map(
        symbol_mapping_zt_closure_funds).fillna(
        stock_em_zt_pool_df_data['closure_funds'])

    return stock_em_zt_pool_df_data


def update_zt_pool_data(str_day, stock_em_zt_pool_df_data):
    mongodb_util.save_mongo(stock_em_zt_pool_df_data, db_name_constant.STOCK_ZT_POOL)


# 异步更新涨停分析和数据
@async_fun
def update_zt_reason_analysis(stock_em_zt_pool_df_data, str_day):
    if data_frame_util.is_empty(stock_em_zt_pool_df_data):
        return
    now_date = datetime.now()
    now_str_day = now_date.strftime('%Y-%m-%d')
    if now_str_day != str_day:
        return

    stock_em_zt_pool_df_data['str_day'] = str_day
    main_line_zt_reason_service.update_symbol_list_zt_reason_analysis(stock_em_zt_pool_df_data, True)
