import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

from mns_common.db.MongodbUtil import MongodbUtil
from loguru import logger
from datetime import datetime
import mns_common.constant.extra_income_db_name as extra_income_db_name

mongodb_util = MongodbUtil('27017')


def clean_us_stock_concept_industry():
    em_us_stock_info_df = mongodb_util.find_all_data(extra_income_db_name.EM_US_STOCK_INFO)
    return em_us_stock_info_df


if __name__ == '__main__':
    em_us_stock_info_test_df = clean_us_stock_concept_industry()
    em_us_stock_info_test_industry_df = em_us_stock_info_test_df.loc[em_us_stock_info_test_df['industry'] != '-']

    em_us_stock_info_test_no_industry_df = em_us_stock_info_test_df.loc[em_us_stock_info_test_df['industry'] == '-']
    em_us_stock_info_test_no_industry_df = em_us_stock_info_test_no_industry_df.sort_values(by=['flow_mv'],
                                                                                            ascending=False)

    print(em_us_stock_info_test_industry_df)
