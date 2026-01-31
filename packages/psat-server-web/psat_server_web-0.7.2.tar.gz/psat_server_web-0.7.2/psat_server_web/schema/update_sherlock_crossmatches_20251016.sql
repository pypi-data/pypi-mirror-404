ALTER TABLE `sherlock_crossmatches`
ADD COLUMN `direct_distance_cat` varchar(100) AFTER `best_distance_source`,
ADD COLUMN `pz_distance_cat` varchar(100) AFTER `direct_distance_cat`,
ADD COLUMN `sm_axis_arcsec` double AFTER `pz_distance_cat`,
ADD COLUMN `z_distance_cat` varchar(100) AFTER `sm_axis_arcsec`,
ADD COLUMN `z_distance_scale` float AFTER `z_distance_cat`,
ADD COLUMN `W2` float AFTER `z_distance_scale`,
ADD COLUMN `W2Err` float AFTER `W2`,
ADD COLUMN `W3` float AFTER `W2Err`,
ADD COLUMN `W3Err` float AFTER `W3`,
ADD COLUMN `W4` float AFTER `W3Err`,
ADD COLUMN `W4Err` float AFTER `W4`,
ADD KEY `idx_rank_transient_object_id` (`rank`,`transient_object_id`)
;
