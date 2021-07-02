/*
Navicat MySQL Data Transfer

Source Server         : 192.168.1.47
Source Server Version : 50734
Source Host           : 192.168.1.47:3306
Source Database       : alertmanager

Target Server Type    : MYSQL
Target Server Version : 50734
File Encoding         : 65001

Date: 2021-07-02 09:07:34
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for alert_info
-- ----------------------------
DROP TABLE IF EXISTS `alert_info`;
CREATE TABLE `alert_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `instance` varchar(255) CHARACTER SET utf8 NOT NULL COMMENT '实例名',
  `status` varchar(20) CHARACTER SET utf8 NOT NULL COMMENT '状态',
  `alertname` varchar(255) CHARACTER SET utf8 NOT NULL COMMENT '告警名称',
  `job` varchar(255) CHARACTER SET utf8 NOT NULL COMMENT '触发器名称',
  `alert_time` varchar(255) CHARACTER SET utf8 NOT NULL COMMENT '告警发现时间',
  `end_time` varchar(255) CHARACTER SET utf8 NOT NULL,
  `description` varchar(255) CHARACTER SET utf8 NOT NULL COMMENT '详细信息',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for trade_cal
-- ----------------------------
DROP TABLE IF EXISTS `trade_cal`;
CREATE TABLE `trade_cal` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cal_date` varchar(50) NOT NULL COMMENT '交易日期',
  `is_open` int(64) NOT NULL DEFAULT '0' COMMENT '1为交易日，0为非交易日',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=373 DEFAULT CHARSET=latin1;
