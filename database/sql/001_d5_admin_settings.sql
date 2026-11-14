-- BAS-AI D5B Admin Settings + Speaker Role Mapping
-- Scope authorization: database basai ONLY
-- MariaDB 10.6 compatible
-- Idempotent: CREATE TABLE IF NOT EXISTS + upsert seed data

USE basai;

CREATE TABLE IF NOT EXISTS basai_settings (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    setting_group VARCHAR(64) NOT NULL,
    setting_key VARCHAR(128) NOT NULL,
    value_type VARCHAR(16) NOT NULL DEFAULT 'string',
    value_json LONGTEXT NOT NULL,
    description VARCHAR(255) NULL,
    updated_by INT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_basai_settings_group_key (setting_group, setting_key),
    KEY ix_basai_settings_group (setting_group),
    CONSTRAINT ck_basai_settings_value_type
        CHECK (value_type IN ('string','integer','decimal','boolean','json')),
    CONSTRAINT ck_basai_settings_value_json
        CHECK (JSON_VALID(value_json))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS basai_roles (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(64) NOT NULL,
    label VARCHAR(100) NOT NULL,
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    sort_order INT NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_basai_roles_code (code),
    KEY ix_basai_roles_enabled_sort (enabled, sort_order)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS basai_channel_profiles (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(64) NOT NULL,
    name VARCHAR(120) NOT NULL,
    channel_count SMALLINT UNSIGNED NOT NULL,
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    is_default TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_basai_channel_profiles_code (code),
    KEY ix_basai_channel_profiles_enabled (enabled),
    CONSTRAINT ck_basai_channel_profiles_count
        CHECK (channel_count BETWEEN 1 AND 32)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS basai_channel_profile_items (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    profile_id BIGINT UNSIGNED NOT NULL,
    channel_index SMALLINT UNSIGNED NOT NULL,
    channel_label VARCHAR(100) NOT NULL,
    role_id BIGINT UNSIGNED NULL,
    shared_role_group VARCHAR(64) NULL,
    diarization_enabled TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_basai_channel_profile_item (profile_id, channel_index),
    KEY ix_basai_channel_profile_role (role_id),
    CONSTRAINT fk_basai_channel_profile_items_profile
        FOREIGN KEY (profile_id)
        REFERENCES basai_channel_profiles (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_basai_channel_profile_items_role
        FOREIGN KEY (role_id)
        REFERENCES basai_roles (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT ck_basai_channel_profile_items_index
        CHECK (channel_index BETWEEN 1 AND 32)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS basai_speaker_mappings (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    hearing_id BIGINT NOT NULL,
    case_id BIGINT NOT NULL,
    channel_index SMALLINT UNSIGNED NOT NULL,
    diarization_speaker_id VARCHAR(64) NOT NULL,
    role_id BIGINT UNSIGNED NOT NULL,
    confidence DECIMAL(5,4) NULL,
    mapping_source VARCHAR(16) NOT NULL DEFAULT 'manual',
    confirmed_by INT NULL,
    confirmed_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_basai_speaker_mapping (
        hearing_id,
        case_id,
        channel_index,
        diarization_speaker_id
    ),
    KEY ix_basai_speaker_mapping_hearing (hearing_id, case_id),
    KEY ix_basai_speaker_mapping_role (role_id),
    CONSTRAINT fk_basai_speaker_mappings_role
        FOREIGN KEY (role_id)
        REFERENCES basai_roles (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT ck_basai_speaker_mapping_channel
        CHECK (channel_index BETWEEN 1 AND 32),
    CONSTRAINT ck_basai_speaker_mapping_confidence
        CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    CONSTRAINT ck_basai_speaker_mapping_source
        CHECK (mapping_source IN ('manual','channel','auto'))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS basai_setting_audits (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    actor_id INT NULL,
    action VARCHAR(32) NOT NULL,
    entity_type VARCHAR(80) NOT NULL,
    entity_key VARCHAR(160) NOT NULL,
    before_json LONGTEXT NULL,
    after_json LONGTEXT NULL,
    ip_address VARCHAR(45) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_basai_setting_audits_actor (actor_id),
    KEY ix_basai_setting_audits_entity (entity_type, entity_key),
    KEY ix_basai_setting_audits_created (created_at),
    CONSTRAINT ck_basai_setting_audits_before
        CHECK (before_json IS NULL OR JSON_VALID(before_json)),
    CONSTRAINT ck_basai_setting_audits_after
        CHECK (after_json IS NULL OR JSON_VALID(after_json))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

INSERT INTO basai_roles (code, label, enabled, sort_order)
VALUES
    ('HAKIM', 'Hakim', 1, 10),
    ('PANITERA_PENGGANTI', 'Panitera Pengganti', 1, 20),
    ('PENGGUGAT', 'Penggugat', 1, 30),
    ('TERGUGAT', 'Tergugat', 1, 40),
    ('SAKSI_1', 'Saksi 1', 1, 50),
    ('SAKSI_2', 'Saksi 2', 1, 60),
    ('KUASA_PENGGUGAT', 'Kuasa Penggugat', 1, 70),
    ('KUASA_TERGUGAT', 'Kuasa Tergugat', 1, 80),
    ('UNKNOWN', 'Belum Ditentukan', 1, 999)
ON DUPLICATE KEY UPDATE
    label = VALUES(label),
    enabled = VALUES(enabled),
    sort_order = VALUES(sort_order);

INSERT INTO basai_channel_profiles
    (code, name, channel_count, enabled, is_default)
VALUES
    ('DEFAULT_4CH', 'Default 4 Channel', 4, 1, 1),
    ('DEFAULT_8CH', 'Default 8 Channel', 8, 1, 0)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    channel_count = VALUES(channel_count),
    enabled = VALUES(enabled);

INSERT INTO basai_channel_profile_items
    (profile_id, channel_index, channel_label, role_id, shared_role_group, diarization_enabled)
SELECT p.id, 1, 'Hakim', r.id, NULL, 0
FROM basai_channel_profiles p
JOIN basai_roles r ON r.code = 'HAKIM'
WHERE p.code = 'DEFAULT_4CH'
ON DUPLICATE KEY UPDATE
    channel_label = VALUES(channel_label),
    role_id = VALUES(role_id),
    shared_role_group = VALUES(shared_role_group),
    diarization_enabled = VALUES(diarization_enabled);

INSERT INTO basai_channel_profile_items
    (profile_id, channel_index, channel_label, role_id, shared_role_group, diarization_enabled)
SELECT p.id, 2, 'Penggugat', r.id, NULL, 0
FROM basai_channel_profiles p
JOIN basai_roles r ON r.code = 'PENGGUGAT'
WHERE p.code = 'DEFAULT_4CH'
ON DUPLICATE KEY UPDATE
    channel_label = VALUES(channel_label),
    role_id = VALUES(role_id),
    shared_role_group = VALUES(shared_role_group),
    diarization_enabled = VALUES(diarization_enabled);

INSERT INTO basai_channel_profile_items
    (profile_id, channel_index, channel_label, role_id, shared_role_group, diarization_enabled)
SELECT p.id, 3, 'Tergugat', r.id, NULL, 0
FROM basai_channel_profiles p
JOIN basai_roles r ON r.code = 'TERGUGAT'
WHERE p.code = 'DEFAULT_4CH'
ON DUPLICATE KEY UPDATE
    channel_label = VALUES(channel_label),
    role_id = VALUES(role_id),
    shared_role_group = VALUES(shared_role_group),
    diarization_enabled = VALUES(diarization_enabled);

INSERT INTO basai_channel_profile_items
    (profile_id, channel_index, channel_label, role_id, shared_role_group, diarization_enabled)
SELECT p.id, 4, 'Saksi Bersama', NULL, 'WITNESS', 1
FROM basai_channel_profiles p
WHERE p.code = 'DEFAULT_4CH'
ON DUPLICATE KEY UPDATE
    channel_label = VALUES(channel_label),
    role_id = VALUES(role_id),
    shared_role_group = VALUES(shared_role_group),
    diarization_enabled = VALUES(diarization_enabled);

INSERT INTO basai_channel_profile_items
    (profile_id, channel_index, channel_label, role_id, shared_role_group, diarization_enabled)
SELECT p.id, 1, 'Hakim', r.id, NULL, 0
FROM basai_channel_profiles p
JOIN basai_roles r ON r.code = 'HAKIM'
WHERE p.code = 'DEFAULT_8CH'
ON DUPLICATE KEY UPDATE channel_label=VALUES(channel_label), role_id=VALUES(role_id),
    shared_role_group=VALUES(shared_role_group), diarization_enabled=VALUES(diarization_enabled);

INSERT INTO basai_channel_profile_items
    (profile_id, channel_index, channel_label, role_id, shared_role_group, diarization_enabled)
SELECT p.id, 2, 'Panitera Pengganti', r.id, NULL, 0
FROM basai_channel_profiles p
JOIN basai_roles r ON r.code = 'PANITERA_PENGGANTI'
WHERE p.code = 'DEFAULT_8CH'
ON DUPLICATE KEY UPDATE channel_label=VALUES(channel_label), role_id=VALUES(role_id),
    shared_role_group=VALUES(shared_role_group), diarization_enabled=VALUES(diarization_enabled);

INSERT INTO basai_channel_profile_items
    (profile_id, channel_index, channel_label, role_id, shared_role_group, diarization_enabled)
SELECT p.id, 3, 'Penggugat', r.id, NULL, 0
FROM basai_channel_profiles p
JOIN basai_roles r ON r.code = 'PENGGUGAT'
WHERE p.code = 'DEFAULT_8CH'
ON DUPLICATE KEY UPDATE channel_label=VALUES(channel_label), role_id=VALUES(role_id),
    shared_role_group=VALUES(shared_role_group), diarization_enabled=VALUES(diarization_enabled);

INSERT INTO basai_channel_profile_items
    (profile_id, channel_index, channel_label, role_id, shared_role_group, diarization_enabled)
SELECT p.id, 4, 'Tergugat', r.id, NULL, 0
FROM basai_channel_profiles p
JOIN basai_roles r ON r.code = 'TERGUGAT'
WHERE p.code = 'DEFAULT_8CH'
ON DUPLICATE KEY UPDATE channel_label=VALUES(channel_label), role_id=VALUES(role_id),
    shared_role_group=VALUES(shared_role_group), diarization_enabled=VALUES(diarization_enabled);

INSERT INTO basai_channel_profile_items
    (profile_id, channel_index, channel_label, role_id, shared_role_group, diarization_enabled)
SELECT p.id, 5, 'Saksi 1', r.id, NULL, 0
FROM basai_channel_profiles p
JOIN basai_roles r ON r.code = 'SAKSI_1'
WHERE p.code = 'DEFAULT_8CH'
ON DUPLICATE KEY UPDATE channel_label=VALUES(channel_label), role_id=VALUES(role_id),
    shared_role_group=VALUES(shared_role_group), diarization_enabled=VALUES(diarization_enabled);

INSERT INTO basai_channel_profile_items
    (profile_id, channel_index, channel_label, role_id, shared_role_group, diarization_enabled)
SELECT p.id, 6, 'Saksi 2', r.id, NULL, 0
FROM basai_channel_profiles p
JOIN basai_roles r ON r.code = 'SAKSI_2'
WHERE p.code = 'DEFAULT_8CH'
ON DUPLICATE KEY UPDATE channel_label=VALUES(channel_label), role_id=VALUES(role_id),
    shared_role_group=VALUES(shared_role_group), diarization_enabled=VALUES(diarization_enabled);

INSERT INTO basai_channel_profile_items
    (profile_id, channel_index, channel_label, role_id, shared_role_group, diarization_enabled)
SELECT p.id, 7, 'Kuasa / Pihak Tambahan', NULL, 'ADDITIONAL_PARTY', 1
FROM basai_channel_profiles p
WHERE p.code = 'DEFAULT_8CH'
ON DUPLICATE KEY UPDATE channel_label=VALUES(channel_label), role_id=VALUES(role_id),
    shared_role_group=VALUES(shared_role_group), diarization_enabled=VALUES(diarization_enabled);

INSERT INTO basai_channel_profile_items
    (profile_id, channel_index, channel_label, role_id, shared_role_group, diarization_enabled)
SELECT p.id, 8, 'Cadangan', NULL, 'RESERVE', 1
FROM basai_channel_profiles p
WHERE p.code = 'DEFAULT_8CH'
ON DUPLICATE KEY UPDATE channel_label=VALUES(channel_label), role_id=VALUES(role_id),
    shared_role_group=VALUES(shared_role_group), diarization_enabled=VALUES(diarization_enabled);

INSERT INTO basai_settings
    (setting_group, setting_key, value_type, value_json, description, updated_by)
VALUES
    ('audio', 'default_channel_profile', 'string', '"DEFAULT_4CH"',
     'Profil channel default BAS-AI.', NULL),
    ('diarization', 'enabled', 'boolean', 'true',
     'Aktifkan speaker diarization pada channel yang memerlukannya.', NULL),
    ('diarization', 'default_num_speakers', 'integer', '2',
     'Jumlah speaker default pada shared-channel diarization.', NULL),
    ('diarization', 'review_confidence_threshold', 'decimal', '0.80',
     'Hasil di bawah threshold ini wajib ditinjau operator.', NULL)
ON DUPLICATE KEY UPDATE
    value_type = VALUES(value_type),
    description = VALUES(description);
