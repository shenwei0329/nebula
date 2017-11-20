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
#
