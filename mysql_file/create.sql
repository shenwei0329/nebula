#
# 数据库表
# =======
# 用于"研发管理"数据管理系统
#
# 为数据采集创建数据库表
#

#
# 需求功能数据
# 2017年10月17日
#
CREATE TABLE if not exists requirment_t
(
	id integer primary key not null auto_increment,
	PD_BH varchar(40) NOT NULL,
  PD_BBH varchar(80) NOT NULL,
	title varchar(40) NOT NULL,
	role varchar(80) NOT NULL,
  requirment varchar(2048) NOT NULL,
  effect varchar(2048) NOT NULL,
	const varchar(256),
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#
# 测试记录数据
# 2017年10月28日
#
CREATE TABLE if not exists testrecord_t
(
	id integer primary key not null auto_increment,
	err_summary varchar(160),
	err_key varchar(40),
	err_id varchar(40),
	err_type varchar(40),
	err_state varchar(40),
	err_pj_key varchar(20),
	err_pj_name varchar(80),
	err_level varchar(40),
	err_result varchar(40),
	err_opr varchar(40),
	err_rpr varchar(40),
	err_cr_date varchar(40),
	err_md_date varchar(40),
	err_ed_date varchar(40),
	err_version_ing varchar(40),
	err_version_ed varchar(40),
	err_mod_1 varchar(40),
	err_mod_2 varchar(40),
	err_desc varchar(1024),
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#
# 人员别名表
# 2017年10月28日
#
CREATE TABLE if not exists member_alias_t
(
	id integer primary key not null auto_increment,
	m_name varchar(80),
	m_gh varchar(20),
	m_alias varchar(40),
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#
# 会议记录数据
#
CREATE TABLE if not exists meeting_t
(
	id integer primary key not null auto_increment,
	mt_name varchar(160),
	mt_date VARCHAR(40),
	mt_hours varchar(20),
	mt_addr varchar(160),
	mt_master varchar(160),
	mt_members varchar(1024),
	mt_title varchar(2048),
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#
# 表记录条数统计
#
CREATE TABLE if not exists count_record_t
(
	id integer primary key not null auto_increment,
	table_name VARCHAR(80),
	rec_count INTEGER,
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#
# 考勤数据
#
CREATE TABLE if not exists checkon_t
(
	id integer primary key not null auto_increment,
	KQ_NAME varchar(40),
	KQ_PART varchar(160),
	KQ_USERID varchar(40),
	KQ_DATE varchar(40),
	KQ_WORKTIME varchar(20),
	KQ_AM varchar(16),
	KQ_AM_STATE varchar(20),
	KQ_PM varchar(16),
	KQ_PM_STATE varchar(20),
	KQ_REF varchar(80),
	KQ_GROUP varchar(40),
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#
# 研发管理计划
#
CREATE TABLE if not exists pd_management_t
(
	id integer primary key not null auto_increment,
	PDM_TASK varchar(1024),
	PDM_STATE INTEGER,
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#
# 研发组定义
#
CREATE TABLE if not exists pd_group_t
(
	id integer primary key not null auto_increment,
	GRP_NAME varchar(128) comment '组名',
	GRP_STATE INTEGER comment '状态：1、有效；0、无效',
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#
# 研发组与人员关联
#
CREATE TABLE if not exists pd_group_member_t
(
	id integer primary key not null auto_increment,
	MEMBER_NAME varchar(20) comment '员工名',
	GROUP_NAME varchar(128) comment '组名',
	FLG INTEGER comment '标识：0、无效；1、有效',
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# 风险定义
#
#
CREATE TABLE if not exists risk_t
(
	id integer primary key not null auto_increment,
	RISK_TITLE varchar(160) comment '风险标题',
	RISK_DESC varchar(1024) comment '风险描述',
	FLG INTEGER comment '标识：0、无效；1、有效',
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# 事件定义
#
#
CREATE TABLE if not exists event_t
(
	id integer primary key not null auto_increment,
	EVT_TITLE varchar(160) comment '标题',
	EVT_DESC varchar(1024) comment '描述',
	FLG INTEGER comment '标识：0、无效；1、有效',
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# 个人指标定义
#
#
CREATE TABLE if not exists quota_t
(
	id integer primary key not null auto_increment,
	QT_TITLE varchar(40) comment '标题',
	MM_GH varchar(20) comment '工号',
	QT_QUOTA DECIMAL(5,4) comment '指标值',
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# 项目统计
#
#
CREATE TABLE if not exists project_key_t
(
	id integer primary key not null auto_increment,
	PJ_XMMC varchar(80) comment '项目名称',
	PJ_XMBH varchar(20) comment '项目编号',
	PJ_KEY varchar(80) comment '俗称',
	PJ_COST INTEGER comment '成本',
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# Jira 任务执行跟踪表
#
#
CREATE TABLE if not exists jira_task_t
(
	id integer primary key not null auto_increment,
	project_alias varchar(80) comment '项目号',
	issue_id varchar(24) comment '任务标识',
	issue_status varchar(24) comment '状态（中文）',
	summary varchar(160) comment '任务简述',
    description varchar(1024) comment '任务描述',
    users varchar(80) comment '任务执行人数组',
    users_alias varchar(80) comment '任务执行人别名数组',
    user_emails varchar(1024) comment '任务执行人电邮数组',
	startDate varchar(48) comment '计划：启动日期',
	endDate varchar(48) comment '计划：完成日期',
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# Project 任务计划表
#
#
CREATE TABLE if not exists project_task_t
(
	id integer primary key not null auto_increment,
	PJ_XMBH varchar(20),
	task_id integer comment '任务ID',
	task_name varchar(80) comment '任务或子任务名称',
	start_date varchar(32) comment '启动日期',
	end_date varchar(32) comment '结束日期',
	days varchar(32) comment '计划工日',
	task_resources varchar(80) comment '任务分配人',
	work_hour varchar(12) comment '计划工时',
	task_level varchar(12) comment '任务层级',
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# KPI考核项目定义
#
#
CREATE TABLE if not exists kpi_t
(
	id integer primary key not null auto_increment,
	name varchar(20) comment 'KPI名称',
	weight varchar(16) comment 'KPI权重',
	flg integer comment '启用标志，0：停用，1：在用',
	summary varchar(80) comment '简述',
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# 个人指标定义
#
#
CREATE TABLE if not exists person_kpi_t
(
	id integer primary key not null auto_increment,
	name varchar(20) comment '名称',
	m_gh varchar(16) comment '员工号',
	kpi_name varchar(24) comment '考核项名称',
	kpi_val varchar(16) comment '考核分值',
    kpi_date varchar(8) comment '考核日期（yyyy-mm)',
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# PRD定义
#
#
CREATE TABLE if not exists prd_t
(
	id integer primary key not null auto_increment,
	prd_level varchar(16) comment '层次',
	prd_topic varchar(80) comment '标题',
	PJ_XMBH varchar(32) comment '项目编号',
	created_at datetime,
	updated_at datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#
#
