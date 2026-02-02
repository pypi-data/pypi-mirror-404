import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.api.kpl.theme.kpl_theme_api as kpl_theme_api
from mns_common.db.MongodbUtil import MongodbUtil
from datetime import datetime
import pandas as pd
import mns_common.constant.db_name_constant as db_name_constant
from loguru import logger
import mns_common.component.cookie.cookie_info_service as cookie_info_service
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.api.msg.push_msg_api as push_msg_api

mongodb_util = MongodbUtil('27017')


# 获取最大id
def query_max_theme_id():
    kpl_theme_max_one_df = mongodb_util.descend_query({}, db_name_constant.KPL_THEME_LIST, '_id', 1)
    if data_frame_util.is_empty(kpl_theme_max_one_df):
        return 381
    else:
        return int(list(kpl_theme_max_one_df['theme_id'])[0])


def sync_new_kpl_theme_info():
    exist_max_theme_id = query_max_theme_id() + 1
    max_sync_theme_id = exist_max_theme_id + 10

    while exist_max_theme_id <= max_sync_theme_id:
        try:
            kpl_token = cookie_info_service.get_kpl_cookie()

            json_data = kpl_theme_api.kpl_theme_index(exist_max_theme_id, kpl_token)
            tables = json_data.get('Table')
            if tables is not None and len(tables) > 0:
                theme_name = json_data.get('Name')

                title = '新增开盘啦题材:' + theme_name
                push_msg_api.push_msg_to_wechat(title, title)

                # 保存到主线列表
                sync_kpl_theme_list(json_data, exist_max_theme_id)
                # 保存到主线详细列表
                sync_kpl_theme_detail(json_data, exist_max_theme_id)
                exist_max_theme_id = exist_max_theme_id + 1
            exist_max_theme_id = exist_max_theme_id + 1
        except BaseException as e:
            exist_max_theme_id = exist_max_theme_id + 1
            logger.error("更新新题材信息异常:{},{}", str(exist_max_theme_id), e)


def update_all_kpl_theme_info():
    theme_id = 0
    max_theme_id = query_max_theme_id() + 1
    while theme_id < max_theme_id:
        try:
            kpl_token = cookie_info_service.get_kpl_cookie()
            json_data = kpl_theme_api.kpl_theme_index(theme_id, kpl_token)
            # 保存到主线列表
            sync_kpl_theme_list(json_data, theme_id)
            # 保存到主线详细列表
            sync_kpl_theme_detail(json_data, theme_id)
            theme_id = theme_id + 1
        except BaseException as e:
            logger.error("出现异常:{}", e)
            theme_id = theme_id + 1


def sync_kpl_theme_list(json_data, theme_id):
    tables = json_data.get('Table')
    if tables is None or len(tables) == 0:
        return None

    theme_name = json_data.get('Name')

    stock_list_df = pd.DataFrame(json_data.get('StockList'))

    stock_list_df.drop_duplicates('StockID', keep='last', inplace=True)

    logger.info("同步题材:{},{}", str(theme_id), theme_name)
    brief_intro = json_data.get('BriefIntro')
    introduction = json_data.get('Introduction')
    kpl_create_time = covert_time(json_data.get('CreateTime'))
    kpl_update_time = covert_time(json_data.get('UpdateTime'))
    now_date = datetime.now()
    sync_time = now_date.strftime('%Y-%m-%d %H:%M:%S')

    theme_dict = {
        '_id': int(theme_id),
        'theme_id': str(theme_id),
        'theme_name': theme_name,
        'brief_intro': brief_intro,
        'introduction': introduction,
        'kpl_create_time': kpl_create_time,
        'kpl_update_time': kpl_update_time,
        'theme_remark': '',
        'sync_time': sync_time,
        'grade': 1,
        'stock_count': stock_list_df.shape[0],
        'valid': True,
        'theme_classify': 2,
    }

    query = {'theme_id': str(theme_id)}

    kpl_theme_one_df = mongodb_util.find_query_data(db_name_constant.KPL_THEME_LIST, query)

    if data_frame_util.is_empty(kpl_theme_one_df):
        ths_concept_one_df = pd.DataFrame(theme_dict, index=[1])
        mongodb_util.save_mongo(ths_concept_one_df, db_name_constant.KPL_THEME_LIST)

    else:
        new_values = {'$set': {
            'brief_intro': brief_intro,
            'introduction': introduction,
            'kpl_update_time': kpl_update_time,
            'theme_name': theme_name}}

        mongodb_util.update_many(query, new_values, db_name_constant.KPL_THEME_LIST)


def sync_kpl_theme_detail(json_data, theme_id):
    tables = json_data.get('Table')
    theme_name = json_data.get('Name')
    if tables is None or len(tables) == 0:
        return None
    for table in tables:
        save_theme_l1(table, theme_name, theme_id)

    return tables


def save_theme_l1(table, theme_name, theme_id):
    theme_l1 = table.get('Level1')

    first_shelve_time = covert_time(theme_l1.get('FirstShelveTime'))
    theme_l1_id = theme_l1.get('ID')
    is_new = theme_l1.get('IsNew')
    theme_l1_name = theme_l1.get('Name')
    update_cache_time = covert_time(theme_l1.get('UpdateCacheTime'))
    zs_code = theme_l1.get('ZSCode')
    now_date = datetime.now()
    sync_time = now_date.strftime('%Y-%m-%d %H:%M:%S')
    theme_dict = {
        '_id': str(theme_l1_id),
        'theme_l1_id': str(theme_l1_id),
        'theme_l1_name': str(theme_l1_name),
        'theme_id': str(theme_id),
        'theme_name': str(theme_name),
        'first_shelve_time': first_shelve_time,
        'update_cache_time': update_cache_time,
        'zs_code': zs_code,
        'is_new': is_new,
        'sync_time': sync_time,
    }

    ths_concept_one_df = pd.DataFrame(theme_dict, index=[1])
    mongodb_util.save_mongo(ths_concept_one_df, db_name_constant.KPL_THEME_LIST_L1)
    stock_list = theme_l1.get('Stocks')
    if len(stock_list) != 0:
        save_theme_stocks(stock_list, theme_name, theme_id, theme_l1_name, theme_l1_id, '无', 0)
    else:
        theme_l2_list = table.get('Level2')
        save_theme_l2(theme_l2_list, theme_name, theme_id, theme_l1_name, theme_l1_id)


def save_theme_l2(theme_l2_list, theme_name, theme_id, theme_l1_name, theme_l1_id):
    for theme_l2_one in theme_l2_list:

        first_shelve_time = covert_time(theme_l2_one.get('FirstShelveTime'))
        theme_l2_id = theme_l2_one.get('ID')
        is_new = theme_l2_one.get('IsNew')
        theme_l2_name = theme_l2_one.get('Name')
        update_cache_time = covert_time(theme_l2_one.get('UpdateCacheTime'))
        zs_code = theme_l2_one.get('ZSCode')
        now_date = datetime.now()
        sync_time = now_date.strftime('%Y-%m-%d %H:%M:%S')
        theme_dict = {
            '_id': str(theme_l2_id),
            'theme_l2_id': str(theme_l2_id),
            'theme_l2_name': str(theme_l2_name),

            'theme_l1_id': str(theme_l1_id),
            'theme_l1_name': str(theme_l1_name),
            'theme_id': str(theme_id),
            'theme_name': str(theme_name),
            'first_shelve_time': first_shelve_time,
            'update_cache_time': update_cache_time,
            'zs_code': zs_code,
            'is_new': is_new,
            'sync_time': sync_time,
        }

        ths_concept_one_df = pd.DataFrame(theme_dict, index=[1])
        mongodb_util.save_mongo(ths_concept_one_df, db_name_constant.KPL_THEME_LIST_L2)
        stock_list = theme_l2_one.get('Stocks')
        if len(stock_list) != 0:
            save_theme_stocks(stock_list, theme_name, theme_id, theme_l1_name, theme_l1_id, theme_l2_name, theme_l2_id)


def save_theme_stocks(stock_list, theme_name, theme_id, theme_l1_name, theme_l1_id, theme_l2_name, theme_l2_id):
    stock_list_df = pd.DataFrame(stock_list)
    stock_list_df = stock_list_df.rename(columns={
        "StockID": "symbol",
        "IsZz": "is_zz",
        "IsHot": "is_hot",
        "Reason": "reason",
        "FirstShelveTime": "first_shelve_time",
        "UpdateCacheTime": "update_cache_time",
        "IsNew": "is_new",
        "name": "prod_name",
        "Hot": "hot",
    })
    stock_list_df["first_shelve_time"] = stock_list_df["first_shelve_time"].apply(covert_time)
    stock_list_df["update_cache_time"] = stock_list_df["update_cache_time"].apply(covert_time)

    stock_list_df['theme_id'] = str(theme_id)
    stock_list_df['theme_name'] = theme_name

    stock_list_df['theme_l1_id'] = str(theme_l1_id)
    stock_list_df['theme_l1_name'] = theme_l1_name

    stock_list_df['theme_l2_name'] = theme_l2_name
    stock_list_df['theme_l2_id'] = str(theme_l2_id)

    stock_list_df['_id'] = (stock_list_df['symbol']
                            + '_'
                            + stock_list_df['theme_id']
                            + '_'
                            + stock_list_df['theme_l1_id']
                            + '_'
                            + stock_list_df['theme_l2_id'])
    now_date = datetime.now()
    sync_time = now_date.strftime('%Y-%m-%d %H:%M:%S')
    stock_list_df['sync_time'] = sync_time
    mongodb_util.save_mongo(stock_list_df, db_name_constant.KPL_THEME_DETAILS)


def covert_time(timestamp_str):
    timestamp = int(timestamp_str)
    if timestamp == 0:
        return "1989-06-04"
    else:
        # 3. 转换为本地时区的datetime对象
        dt_local = datetime.fromtimestamp(timestamp)
        # 4. 格式化为「年月日 时分秒」的字符串（格式可自定义）
        datetime_str = dt_local.strftime('%Y-%m-%d %H:%M:%S')
        return datetime_str


if __name__ == '__main__':
    update_all_kpl_theme_info()
