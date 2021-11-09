# 获取上交所交易日期

import datetime
import tushare as ts
import time
from util.mysql_client import DB
import myconfig
from sqlalchemy import create_engine

# tushare网站token
token = '0a1e5e0d918fd09df4e4824bdc2c71367b65180caea7e210ca8cbc3b'
today = datetime.datetime.now().strftime("%Y%m%d")
enddate = datetime.datetime.now().strftime("%Y") + '1231'


# noinspection PyBroadException
def get_daily(start_date=today, end_date=enddate):
    # 数据存储
    # 设置token
    db_info = {
        'host': myconfig.get_config().get('db').get('host'),
        'port': myconfig.get_config().get('db').get('port'),
        'user': myconfig.get_config().get('db').get('user'),
        'db': myconfig.get_config().get('db').get('database'),
        'passwd': myconfig.get_config().get('db').get('passwd')
    }

    ts.set_token(token)
    # 初始化接口
    pro = ts.pro_api()
    engine = create_engine("mysql+pymysql://%(user)s:%(passwd)s@%(host)s:%(port)d/%(db)s?charset=utf8" % db_info,
                           encoding='utf-8')
    for _ in range(3):
        try:
            df = pro.trade_cal(start_date=start_date, end_date=end_date, fields='cal_date,is_open')
            df.to_sql(name='trade_cal', con=engine, if_exists='append', index=False, chunksize=5000)
        except Exception as e:
            print(e)
            time.sleep(1)
        else:
            return True


# 数据读取
def get_cal_date(date_time):
    """
    :param date_time:  接收一个整数参数，为日期格式。例如20210623
    :return: 返回整数，0为不交易，1为交易日
    """
    sql = 'select is_open from trade_cal where cal_date = %s' % date_time
    try:
        db = DB()
        db.cur.execute(sql)
        ret = db.cur.fetchone()
        if ret is None:
            get_daily()
            return None
        return ret['is_open']
    except Exception as e:
        return None
