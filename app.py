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
from flask_apscheduler import APScheduler

# 日盘夜盘开始结束时间(UTC时间)
tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y%m%d")



# 时间转换
def str_to_time(time_object):
    """
    根据字符串格式时间转换为日期格式
    :param time_object:
    :return:
    """
    time_obj = datetime.datetime.strptime(time_object, '%Y%m%d%H%M%S')
    return time_obj


def send_message(webhook, text, title='新消息', secret=None, is_at_all=False, at_mobiles=[]):
    try:
        ding = DingtalkChatbot(webhook=webhook, secret=secret)
        ret_value = ding.send_markdown(title=title, text=text, at_mobiles=at_mobiles, is_at_all=is_at_all)
        if ret_value['errcode'] == 0:
            return None
        else:
            return ret_value['errmsg']
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


def cut_alert(data):
    my_log = Mylog()
    db = mysql_client.DB()
    stock_info = get_config().get('stock')
    futures_info = get_config().get('futures')
    option_info = get_config().get('option')
    server_info = get_config().get('server')
    its_info = get_config().get('its')
    higt_info = get_config().get('higt')
    # 告警信息列表，存储告警时间
    error_dingtalk_list = []
    today = datetime.datetime.now().strftime("%Y%m%d")
    request_time = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y%m%d%H%M%S"), "%Y%m%d%H%M%S")
    day_start_time = today + get_config().get('time').get('day_start_time')
    day_end_time = today + get_config().get('time').get('day_end_time')
    night_start_time = today + get_config().get('time').get('night_start_time')
    night_end_time = today + get_config().get('time').get('night_end_time')
    its_start_time = today + get_config().get('time').get('its_start_time')
    its_end_time = today + get_config().get('time').get('its_end_time')
    alertmessage = []
    text = {"alerts": alertmessage}
    response_data = {
        "code": 200,
        "message": None
    }
    severity = data['alerts'][0]['labels']['severity']
    alerts = data['alerts']
    description = data['alerts'][0]['annotations']['description']
    status = data['status']
    instance = data['alerts'][0]['labels']['instance']
    job = data['alerts'][0]['labels']['job']
    start_sat = data['alerts'][0]['startsAt']
    end_sat = data['alerts'][0]['endsAt']
    fingerprint = data['alerts'][0]['fingerprint']
    alert_name = alertmessage[0]['labels']['alertname']
    alert_dict_key_name = start_sat + '_' + fingerprint
    dingtalk_dict = {}

    try:
        service = data['alerts'][0]['labels']['service']
    except KeyError as e:
        service = ""

    for alert in alerts:
        if status == 'firing':
            if get_cal_date(today) == 0 and service in ['rmcs', 'rmcf', 'rmco', 'its']:
                # 非告警时间，直接返回已发送告警，屏蔽告警
                response_data['code'] = 201
                my_log.console_log_logger.info("robot： dingtalk, response: '非交易时间的告警信息'")
                ret = None
            else:
                if service == 'rmcf':
                    if (str_to_time(night_start_time) < request_time < str_to_time(night_end_time) or
                            str_to_time(day_start_time) < request_time < str_to_time(day_end_time)):
                        # 告警时间，查询futures_dingtalk_list,如果1分钟内少于20条，则添加到告警列表
                        # 添加到list中，然后删除一分钟之前的所有数据
                        alertmessage.append(alert)
                        my_log.console_log_logger.info("robot： dingtalk, response: %s" % alert)
                        ret = send_message(webhook=futures_info.get('webhook'),
                                           secret=futures_info.get('secret'),
                                           text=alertmanager_json_to_markdown(text))
                        #
                    else:
                        # 非告警时间，直接返回已发送告警，屏蔽告警
                        response_data['code'] = 201
                        my_log.console_log_logger.info("robot： dingtalk, response: 非交易时间的rmcf告警,%s" % alert)
                        ret = None
                elif service == 'rmco':
                    if (str_to_time(night_start_time) < request_time < str_to_time(night_end_time) or
                            str_to_time(day_start_time) < request_time < str_to_time(day_end_time)):
                        # 告警时间，添加到告警列表
                        alertmessage.append(alert)
                        my_log.console_log_logger.info("robot： dingtalk, response: %s" % alert)
                        ret = send_message(webhook=option_info.get('webhook'),
                                           secret=option_info.get('secret'),
                                           text=alertmanager_json_to_markdown(text))
                        #
                    else:
                        # 非告警时间，直接返回已发送告警，屏蔽告警
                        response_data['code'] = 201
                        my_log.console_log_logger.info("robot： dingtalk, response: 非交易时间的rmco告警,%s" % alert)
                        ret = None
                elif service == 'rmcs':
                    if str_to_time(day_start_time) < request_time < str_to_time(day_end_time):
                        alertmessage.append(alert)
                        my_log.console_log_logger.info("robot： dingtalk, response: rmcs的告警，%s" % alert)
                        ret = send_message(webhook=stock_info.get('webhook'),
                                           secret=stock_info.get('secret'),
                                           text=alertmanager_json_to_markdown(text))
                    else:
                        my_log.console_log_logger.info("robot： dingtalk, response: 非交易时间的rmcs告警，%s" % alert)
                        # 非告警时间，直接返回已发送告警，屏蔽告警
                        response_data['code'] = 201
                        ret = None
                elif service == 'its':
                    if str_to_time(its_start_time) < request_time < str_to_time(its_end_time):
                        alertmessage.append(alert)
                        my_log.console_log_logger.info("robot: dingtalk, response: its告警, %s" % alert)
                        ret = send_message(webhook=its_info.get('webhook'),
                                           secret=its_info.get('secret'),
                                           text=alertmanager_json_to_markdown(text))
                    else:
                        my_log.console_log_logger.info("robot: dingtalk, response: 非交易时间的交易系统告警， %s" % alert)
                        # 非告警时间，直接返回已发送告警，屏蔽告警
                        response_data['code'] = 201
                        ret = None
                elif service == 'host' and severity == 'critical':
                    # 查看告警次数dict是否超过3，如果超过3则告警升级
                    # 大于3，发短信或者打电话，其他的则发钉钉
                    if dingtalk_dict.get(alert_dict_key_name) > 3:
                        dingtalk_dict[alert_dict_key_name] = dingtalk_dict.get(alert_dict_key_name) + 1
                        #
                        alertmessage.append(alert)
                        ret = send_message(webhook=higt_info.get('webhook'),
                                           secret=higt_info.get('secret'),
                                           text=alertmanager_json_to_markdown(text))
                    elif dingtalk_dict.get(alert_dict_key_name) > 0:
                        dingtalk_dict[alert_dict_key_name] = dingtalk_dict.get(alert_dict_key_name) + 1
                        alertmessage.append(alert)
                        ret = send_message(webhook=higt_info.get('webhook'),
                                           secret=higt_info.get('secret'),
                                           text=alertmanager_json_to_markdown(text))
                    else:
                        dingtalk_dict = {alert_dict_key_name: 1}
                        alertmessage.append(alert)
                        ret = send_message(webhook=higt_info.get('webhook'),
                                           secret=higt_info.get('secret'),
                                           text=alertmanager_json_to_markdown(text))
                else:
                    my_log.console_log_logger.info("robot： dingtalk, response: 交易日期的其他告警，%s" % alert)
                    alertmessage.append(alert)
                    ret = send_message(webhook=higt_info.get('webhook'),
                                       secret=higt_info.get('secret'),
                                       text=alertmanager_json_to_markdown(text))
        else:
            my_log.console_log_logger.info("robot： dingtalk, response: '恢复告警信息'")
            # 恢复告警，查找dict中告警标识，删除告警次数数据
            if dingtalk_dict.get(alert_dict_key_name):
                dingtalk_dict.pop(alert_dict_key_name)
            alertmessage.append(alert)
            ret = send_message(webhook=server_info.get('webhook'),
                               secret=server_info.get('secret'),
                               text=alertmanager_json_to_markdown(text))

    if ret is None:
        response_data['message'] = "Send successful"
        if status == 'firing':
            sql = f"""insert into alert_info (instance, status, alertname, job, alert_time, end_time,description, 
            fingerprint, alert_num) values ('{instance}', '{status}', '{alert_name}', '{job}','{start_sat}', 
            '{end_sat}', '{description}', '{fingerprint}', 1)"""
            select_sql = f"""select * from alert_info where alert_time='{start_sat}'
            and fingerprint='{fingerprint}'"""
            db.cur.execute(select_sql)
            ret_msg = db.cur.fetchone()
            if ret_msg is None:
                my_log.console_log_logger.info("robot： dingtalk, response: '数据库没有记录。'")
                db.cur.execute(sql)
                db.conn.commit()
            else:
                update_sql = f"""update alert_info set alert_num=alert_num + 1 where alert_time='{start_sat}'
                and fingerprint='{fingerprint}'"""
                db.cur.execute(update_sql)
                my_log.console_log_logger.info("robot： dingtalk, response: '数据库已经存在记录。'")
        else:
            sql = f"""update alert_info set status='{status}', end_time='{end_sat}' where 
            fingerprint='{fingerprint}'"""
            my_log.console_log_logger.info("robot： dingtalk, response: '告警恢复'")
            db.cur.execute(sql)
            db.conn.commit()
        response_data['message'] = str(alerts)
        my_log.log_to_file_logger.info("robot： dingtalk, response: %s" % (json.dumps(response_data)))
    else:
        # 如果返回码等于400 ，即发送数量超过20条，统计相关信息，保存到列表中，下次发送后，pop出相关元素
        error_dingtalk_list.append(data)
        response_data['code'] = 200
        my_log.log_to_file_logger.info("robot： dingtalk, response: %s" % (json.dumps(response_data)))

    return Response(response=json.dumps(response_data), status=response_data['code'], mimetype='application/json')


class Config(object):

    JOBS = [
        {
            'id': 'job1',
            'func': '__main__:cut_alert',
            'args': (),
            'trigger': 'interval',
            'minute': 2
        },
    ]


# Flask通用配置
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route('/webhook/send/', methods=['POST'])
def send():
    data = json.loads(request.data)
    cut_alert(data)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8888)
