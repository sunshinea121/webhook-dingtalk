#### alertmanager-webhook
```接收alertmanager消息，格式化后发送到钉钉机器人
通过job名称与告警时间进行告警抑制
time为UTC时间
```

#### 启动方式
```docker run -d --name myalertmanager -v /config:/code/config -p 8888:8888 alertmanager-webhook:1.0.0```

#### 消息模板

#### 配置文件模板
```robot:
  webhook: "https://oapi.dingtalk.com/robot/send?access_token=991f96"
  secret: "SEC02dc23224dd449a8d570db1074dad6"

log:
  path: "/code/logs/run.log"

time:
  day_start_time: '00:35:00'
  day_end_time: '07:35:00'
  night_start_time: '12:35:00'
  night_end_time: '18:40:00'

job:
  job_list: ['instance-down', "ProcessFMSDown", "ProcessFMDDown", "ProcessFMKDown",]
  ```
