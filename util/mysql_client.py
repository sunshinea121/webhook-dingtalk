import pymysql
import myconfig


class DB:
    host = myconfig.get_config().get('db').get('host')
    port = myconfig.get_config().get('db').get('port')
    user = myconfig.get_config().get('db').get('user')
    db = myconfig.get_config().get('db').get('database')
    passwd = myconfig.get_config().get('db').get('passwd')

    def __init__(self, host=host, port=port, database=db, user=user, passwd=passwd, charset='utf8'):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.database = database
        self.port = port
        self.charset = charset
        self.conn = None
        self.cur = None

    # 建立连接
        try:
            self.conn = pymysql.connect(host=self.host,
                                        port=self.port,
                                        db=self.database,
                                        user=self.user,
                                        passwd=self.passwd,
                                        charset=self.charset)
        except Exception as e:
            print(e)
        # 创建游标，操作设置为字段类型
        self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)

    def __del__(self):
        # print("关闭")
        # 关闭游标
        self.cur.close()
        # 关闭数据库连接
        self.conn.close()


if __name__ == '__main__':
    db = DB()
    sql = """select * from alert_info where instance='139.9.38.10' 
                                and alertname='主机状态' and alert_time='201-07-01T01:24:14.43Z'"""
    db.cur.execute(sql)
    ret = db.cur.fetchone()
    print(ret)
    # db.conn.commit()
