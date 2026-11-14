-- BAS-AI D5B rollback
-- Scope: database basai ONLY
-- Drops only D5B tables. Legacy Alembic-era tables are preserved.

USE basai;

DROP TABLE IF EXISTS basai_setting_audits;
DROP TABLE IF EXISTS basai_speaker_mappings;
DROP TABLE IF EXISTS basai_channel_profile_items;
DROP TABLE IF EXISTS basai_channel_profiles;
DROP TABLE IF EXISTS basai_roles;
DROP TABLE IF EXISTS basai_settings;
