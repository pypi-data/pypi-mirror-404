alter table sherlock_classifications drop key `idx_summary`;
alter table sherlock_classifications add key `idx_summary` (`summary`,`transient_object_id`);
