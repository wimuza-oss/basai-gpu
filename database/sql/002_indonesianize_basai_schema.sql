-- BAS-AI D5C - Penyeragaman nama tabel/kolom domain
-- Scope: database basai ONLY
-- MariaDB 10.6
-- owner_id dipetakan menjadi userid karena mengacu pada userid user login SIPP/BAS.
--   Kolom yang tidak tercantum dalam pedoman penamaan dipertahankan.

USE basai;

SET @basai_fk_checks_lama := @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE basai_channel_profile_items
    DROP FOREIGN KEY fk_basai_channel_profile_items_profile,
    DROP FOREIGN KEY fk_basai_channel_profile_items_role;

ALTER TABLE basai_speaker_mappings
    DROP FOREIGN KEY fk_basai_speaker_mappings_role;

RENAME TABLE
    basai_captures TO basai_media_sidang,
    basai_hearing_completions TO basai_sidang_sidang,
    basai_settings TO basai_setting,
    basai_roles TO basai_peran,
    basai_channel_profiles TO basai_profil_channel,
    basai_channel_profile_items TO basai_detail_profil_channel,
    basai_speaker_mappings TO basai_pembicara,
    basai_setting_audits TO basai_audit_pengaturan;

ALTER TABLE basai_media_sidang
    CHANGE COLUMN owner_id userid INT NOT NULL,
    CHANGE COLUMN hearing_id sidang_id BIGINT NOT NULL,
    CHANGE COLUMN case_id perkara_id BIGINT NOT NULL,
    CHANGE COLUMN hearing_date tanggal_sidang DATE NOT NULL,
    CHANGE COLUMN kind jenis VARCHAR(10) NOT NULL,
    CHANGE COLUMN mime tipe_mime VARCHAR(50) NOT NULL,
    CHANGE COLUMN interrupted terputus TINYINT(1) NOT NULL,
    CHANGE COLUMN next_index indeks_berikutnya INT NOT NULL,
    CHANGE COLUMN total_bytes jumlah_byte BIGINT NOT NULL,
    CHANGE COLUMN created_at dibuat_pada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6);

ALTER TABLE basai_sidang_sidang
    CHANGE COLUMN hearing_id sidang_id BIGINT NOT NULL,
    CHANGE COLUMN case_id perkara_id BIGINT NOT NULL;

ALTER TABLE basai_setting
    CHANGE COLUMN value_type tipe_nilai VARCHAR(16) NOT NULL DEFAULT 'string',
    CHANGE COLUMN value_json nilai_json LONGTEXT NOT NULL,
    CHANGE COLUMN description keterangan VARCHAR(255) NULL,
    CHANGE COLUMN created_at dibuat_pada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CHANGE COLUMN updated_at diperbarui_pada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6);

ALTER TABLE basai_peran
    CHANGE COLUMN code kode VARCHAR(64) NOT NULL,
    CHANGE COLUMN label nama VARCHAR(100) NOT NULL,
    CHANGE COLUMN enabled aktif TINYINT(1) NOT NULL DEFAULT 1,
    CHANGE COLUMN sort_order urutan INT NOT NULL DEFAULT 0,
    CHANGE COLUMN created_at dibuat_pada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CHANGE COLUMN updated_at diperbarui_pada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6);

ALTER TABLE basai_profil_channel
    CHANGE COLUMN code kode VARCHAR(64) NOT NULL,
    CHANGE COLUMN name nama VARCHAR(120) NOT NULL,
    CHANGE COLUMN channel_count jumlah_channel SMALLINT UNSIGNED NOT NULL,
    CHANGE COLUMN enabled aktif TINYINT(1) NOT NULL DEFAULT 1,
    CHANGE COLUMN created_at dibuat_pada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CHANGE COLUMN updated_at diperbarui_pada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6);

ALTER TABLE basai_detail_profil_channel
    CHANGE COLUMN channel_index nomor_channel SMALLINT UNSIGNED NOT NULL,
    CHANGE COLUMN channel_label nama_channel VARCHAR(100) NOT NULL,
    CHANGE COLUMN role_id peran_id BIGINT UNSIGNED NULL,
    CHANGE COLUMN shared_role_group kelompok_peran_bersama VARCHAR(64) NULL,
    CHANGE COLUMN diarization_enabled pemisahan_pembicara_aktif TINYINT(1) NOT NULL DEFAULT 0,
    CHANGE COLUMN created_at dibuat_pada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CHANGE COLUMN updated_at diperbarui_pada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6);

ALTER TABLE basai_pembicara
    CHANGE COLUMN hearing_id sidang_id BIGINT NOT NULL,
    CHANGE COLUMN case_id perkara_id BIGINT NOT NULL,
    CHANGE COLUMN channel_index nomor_channel SMALLINT UNSIGNED NOT NULL,
    CHANGE COLUMN diarization_speaker_id kode_pembicara VARCHAR(64) NOT NULL,
    CHANGE COLUMN role_id peran_id BIGINT UNSIGNED NOT NULL,
    CHANGE COLUMN confidence tingkat_keyakinan DECIMAL(5,4) NULL,
    CHANGE COLUMN mapping_source sumber_pemetaan VARCHAR(16) NOT NULL DEFAULT 'manual',
    CHANGE COLUMN confirmed_by dikonfirmasi_oleh INT NULL,
    CHANGE COLUMN confirmed_at dikonfirmasi_pada DATETIME(6) NULL,
    CHANGE COLUMN created_at dibuat_pada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CHANGE COLUMN updated_at diperbarui_pada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6);

ALTER TABLE basai_audit_pengaturan
    CHANGE COLUMN created_at dibuat_pada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6);

ALTER TABLE basai_detail_profil_channel
    ADD CONSTRAINT fk_detail_profil_channel_profil
        FOREIGN KEY (profile_id)
        REFERENCES basai_profil_channel (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    ADD CONSTRAINT fk_detail_profil_channel_peran
        FOREIGN KEY (peran_id)
        REFERENCES basai_peran (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL;

ALTER TABLE basai_pembicara
    ADD CONSTRAINT fk_pembicara_peran
        FOREIGN KEY (peran_id)
        REFERENCES basai_peran (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;

SET FOREIGN_KEY_CHECKS = @basai_fk_checks_lama;
