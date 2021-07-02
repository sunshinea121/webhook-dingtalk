#!/usr/bin/env python3
# alertmanager filter
# 告警筛选，自动获取上海证券交易所的交易时间，剔除prometheus的相关告警信息
# by: seven
# date: 2021-06-23

import json
from flask import request, Flask, Response, render_template
from dingtalkchatbot.chatbot import DingtalkChatbot
import datetime
import util.mysql_client as mysql_client
from myconfig import get_config
from app_log import Mylog
from util.get_cal_date import get_cal_date
import prometheus_client

# 日盘夜盘开始结束时间(UTC时间)
today = datetime.datetime.now().strftime("%Y%m%d")
tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y%m%d")
my_log = Mylog()


# 时间转换
def str_to_time(time_object):
    """
    根据字符串格式时间转换为日期格式
    :param time_object:
    :return:
    """
    time_obj = datetime.datetime.strptime(time_object, '%Y%m%d%H%M%S')
    # time_obj = int(time.mktime(time.strptime(time_object, "%Y%m%d%H:%M:%S")))
    return time_obj


def send_message(webhook, text, title='新消息', secret=None, is_at_all=False, at_mobiles=[]):
    try:
        ding = DingtalkChatbot(webhook=webhook, secret=secret)
        ret = ding.send_markdown(title=title, text=text, at_mobiles=at_mobiles, is_at_all=is_at_all)
        print(ret)
        if ret['errcode'] == 0:
            return None
        else:
            return ret['errmsg']
    except Exception as error:
        return str(error)


def alertmanager_json_to_markdown(alert_data):
    template_name = get_config().get('template').get('name')
    with app.app_context():
        if isinstance(alert_data, str):
            context = json.loads(alert_data)
        else:
            context = alert_data
        render = render_template(template_name, **context)
        return render


# Flask通用配置
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route('/webhook/send/', methods=['POST'])
def send():
    db = mysql_client.DB()
    request_time = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y%m%d%H%M%S"), "%Y%m%d%H%M%S")
    robot_info = get_config().get('robot')
    day_start_time = today + get_config().get('time').get('day_start_time')
    day_end_time = today + get_config().get('time').get('day_end_time')
    night_start_time = today + get_config().get('time').get('night_start_time')
    night_end_time = today + get_config().get('time').get('night_end_time')
    job_list = get_config().get('job').get('job_list')
    alertmessage = []
    text = {"alerts": alertmessage}

    response_data = {
        "code": 200,
        "message": None
    }

    if not robot_info:
        response_data['code'] = 400
        response_data['message'] = "Failed send message, robot config not found!"

    data = json.loads(request.data)

    alerts = data['alerts']
    description = data['alerts'][0]['annotations']['description']
    status = data['alerts'][0]['status']
    instance = data['alerts'][0]['labels']['instance']
    job = data['alerts'][0]['labels']['job']
    startsat = data['alerts'][0]['startsAt']
    endsat = data['alerts'][0]['endsAt']

    for alert in alerts:
        alert_name = alert['labels']['alertname']

        if get_cal_date(today) == 0 and alert_name in job_list:
            # 如果为非交易日并且告警信息是
            response_data['code'] = 200
            response_data['message'] = str(alert)
            my_log.console_log_logger.info("robot： dingtalk, response: %s" % (json.dumps(response_data)))
        else:
            # 如果在夜盘时间内
            if str_to_time(night_start_time) < request_time < str_to_time(night_end_time):
                response_data['code'] = 200
                response_data['message'] = str(alert)
                alertmessage.append(alert)
                my_log.console_log_logger.info("robot： dingtalk, response: %s" % (json.dumps(response_data)))
                my_log.console_log_logger.info("robot： dingtalk, response: '夜盘时间，正常告警'")
            elif str_to_time(day_start_time) < request_time < str_to_time(day_end_time):
                response_data['code'] = 200
                response_data['message'] = str(alert)
                alertmessage.append(alert)
                my_log.console_log_logger.info("robot： dingtalk, response: %s" % (json.dumps(response_data)))
                my_log.console_log_logger.info("robot： dingtalk, response: '日盘时间，正常告警'")
            elif alert_name in job_list:
                response_data['code'] = 201
                response_data['message'] = "我拦截" + " " + str(alert)
                my_log.console_log_logger.info("robot： dingtalk, response: %s" % (json.dumps(response_data)))
            else:
                alertmessage.append(alert)

    if len(alertmessage):
        alert_name = alertmessage[0]['labels']['alertname']

        ret = send_message(webhook=robot_info.get('webhook'),
                           secret=robot_info.get('secret'),
                           text=alertmanager_json_to_markdown(text))

        if not ret:
            response_data['message'] = "Send successful"
            if status == 'firing':
                sql = f"""insert into alert_info (instance, status, alertname, job, alert_time,end_time, 
                                description) values ('{instance}', '{status}', '{alert_name}', '{job}', 
                                '{startsat}', '{endsat}', '{description}')"""
                select_sql = f"""select * from alert_info where instance='{instance}' 
                                and alertname='{alert_name}' and alert_time='{startsat}'"""
                db.cur.execute(select_sql)
                ret = db.cur.fetchone()
                if ret is None:
                    my_log.console_log_logger.info("robot： dingtalk, response: '数据库没有记录。'")
                    db.cur.execute(sql)
                    db.conn.commit()
                my_log.console_log_logger.info("robot： dingtalk, response: '数据库已经存在记录。'")
            else:
                sql = f"""update alert_info set status='{status}', end_time='{endsat}' where instance='{instance}' 
                                and alertname='{alert_name}' and alert_time='{startsat}'"""
                my_log.console_log_logger.info("robot： dingtalk, response: '告警恢复'")
                db.cur.execute(sql)
                db.conn.commit()
            response_data['message'] = str(alerts)
            my_log.log_to_file_logger.info("robot： dingtalk, response: %s" % (json.dumps(response_data)))
        else:
            response_data['message'] = ret
            response_data['code'] = 400
            my_log.log_to_file_logger.info("robot： dingtalk, response: %s" % (json.dumps(response_data)))

    return Response(response=json.dumps(response_data), status=response_data['code'], mimetype='application/json')


@app.route('/metrics/', methods=['GET'])
def mointor_alter_data():
    total_alert_num = prometheus_client.Counter(name='total_alert_num', documentation='Total number of alarms.')
    month_alert_num = prometheus_client.Counter(name='month_alert_num', documentation='Number of alerts this month.')
    week_alert_num = prometheus_client.Counter(name='week_alert_num', documentation='Number of alarms this week.')
    current_alert_num = prometheus_client.Gauge(name='current_alert_num', documentation='Number of current alarms.')
    pass


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8888)
