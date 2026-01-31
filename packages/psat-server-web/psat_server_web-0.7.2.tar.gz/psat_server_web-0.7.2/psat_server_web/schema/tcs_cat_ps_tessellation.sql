drop table if exists `tcs_cat_ps_tessellation`;

create table `tcs_cat_ps_tessellation` (
`id` int unsigned not null auto_increment,
`skycell` char(40) not null,
`ra` double not null,
`dec` double not null,
`htm10ID` int unsigned not null,
`htm13ID` int unsigned not null,
`htm16ID` bigint(20) unsigned not null,
PRIMARY KEY `idx_id` (`id`),
UNIQUE KEY `idx_name` (`skycell`),
KEY `idx_htm10ID` (`htm10ID`),
KEY `idx_htm13ID` (`htm13ID`),
KEY `idx_htm16ID` (`htm16ID`),
UNIQUE KEY `idx_ra_dec` (`ra`,`dec`)
) ENGINE=MyISAM;
