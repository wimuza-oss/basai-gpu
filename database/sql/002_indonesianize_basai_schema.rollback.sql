-- BAS-AI D5C rollback - kembali ke nama tabel/kolom Inggris sebelumnya
-- Scope: database basai ONLY

USE basai;

SET @basai_fk_checks_lama := @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE basai_detail_profil_kanal
    DROP FOREIGN KEY fk_detail_profil_kanal_profil,
    DROP FOREIGN KEY fk_detail_profil_kanal_peran;

ALTER TABLE basai_pemetaan_pembicara
    DROP FOREIGN KEY fk_pemetaan_pembicara_peran;

ALTER TABLE basai_media_sidang
    CHANGE COLUMN pemilik_id owner_id INT NOT NULL,
    CHANGE COLUMN sidang_id hearing_id BIGINT NOT NULL,
    CHANGE COLUMN perkara_id case_id BIGINT NOT NULL,
    CHANGE COLUMN tanggal_sidang hearing_date DATE NOT NULL,
    CHANGE COLUMN jenis kind VARCHAR(10) NOT NULL,
    CHANGE COLUMN tipe_mime mime VARCHAR(50) NOT NULL,
    CHANGE COLUMN terputus interrupted TINYINT(1) NOT NULL,
    CHANGE COLUMN indeks_berikutnya next_index INT NOT NULL,
    CHANGE COLUMN jumlah_byte total_bytes BIGINT NOT NULL,
    CHANGE COLUMN dibuat_pada created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6);

ALTER TABLE basai_penyelesaian_sidang
    CHANGE COLUMN sidang_id hearing_id BIGINT NOT NULL,
    CHANGE COLUMN perkara_id case_id BIGINT NOT NULL,
    CHANGE COLUMN sudah_selesai is_completed TINYINT(1) NOT NULL,
    CHANGE COLUMN diselesaikan_oleh completed_by INT NOT NULL,
    CHANGE COLUMN diselesaikan_pada completed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CHANGE COLUMN dibuka_kembali_oleh reopened_by INT NULL,
    CHANGE COLUMN dibuka_kembali_pada reopened_at DATETIME(6) NULL;

ALTER TABLE basai_pengaturan
    CHANGE COLUMN kelompok_pengaturan setting_group VARCHAR(64) NOT NULL,
    CHANGE COLUMN kunci_pengaturan setting_key VARCHAR(128) NOT NULL,
    CHANGE COLUMN tipe_nilai value_type VARCHAR(16) NOT NULL DEFAULT 'string',
    CHANGE COLUMN nilai_json value_json LONGTEXT NOT NULL,
    CHANGE COLUMN keterangan description VARCHAR(255) NULL,
    CHANGE COLUMN diperbarui_oleh updated_by INT NULL,
    CHANGE COLUMN dibuat_pada created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CHANGE COLUMN diperbarui_pada updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6);

ALTER TABLE basai_peran
    CHANGE COLUMN kode code VARCHAR(64) NOT NULL,
    CHANGE COLUMN nama label VARCHAR(100) NOT NULL,
    CHANGE COLUMN aktif enabled TINYINT(1) NOT NULL DEFAULT 1,
    CHANGE COLUMN urutan sort_order INT NOT NULL DEFAULT 0,
    CHANGE COLUMN dibuat_pada created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CHANGE COLUMN diperbarui_pada updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6);

ALTER TABLE basai_profil_kanal
    CHANGE COLUMN kode code VARCHAR(64) NOT NULL,
    CHANGE COLUMN nama name VARCHAR(120) NOT NULL,
    CHANGE COLUMN jumlah_kanal channel_count SMALLINT UNSIGNED NOT NULL,
    CHANGE COLUMN aktif enabled TINYINT(1) NOT NULL DEFAULT 1,
    CHANGE COLUMN utama is_default TINYINT(1) NOT NULL DEFAULT 0,
    CHANGE COLUMN dibuat_pada created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CHANGE COLUMN diperbarui_pada updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6);

ALTER TABLE basai_detail_profil_kanal
    CHANGE COLUMN profil_id profile_id BIGINT UNSIGNED NOT NULL,
    CHANGE COLUMN nomor_kanal channel_index SMALLINT UNSIGNED NOT NULL,
    CHANGE COLUMN nama_kanal channel_label VARCHAR(100) NOT NULL,
    CHANGE COLUMN peran_id role_id BIGINT UNSIGNED NULL,
    CHANGE COLUMN kelompok_peran_bersama shared_role_group VARCHAR(64) NULL,
    CHANGE COLUMN pemisahan_pembicara_aktif diarization_enabled TINYINT(1) NOT NULL DEFAULT 0,
    CHANGE COLUMN dibuat_pada created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CHANGE COLUMN diperbarui_pada updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6);

ALTER TABLE basai_pemetaan_pembicara
    CHANGE COLUMN sidang_id hearing_id BIGINT NOT NULL,
    CHANGE COLUMN perkara_id case_id BIGINT NOT NULL,
    CHANGE COLUMN nomor_kanal channel_index SMALLINT UNSIGNED NOT NULL,
    CHANGE COLUMN kode_pembicara diarization_speaker_id VARCHAR(64) NOT NULL,
    CHANGE COLUMN peran_id role_id BIGINT UNSIGNED NOT NULL,
    CHANGE COLUMN tingkat_keyakinan confidence DECIMAL(5,4) NULL,
    CHANGE COLUMN sumber_pemetaan mapping_source VARCHAR(16) NOT NULL DEFAULT 'manual',
    CHANGE COLUMN dikonfirmasi_oleh confirmed_by INT NULL,
    CHANGE COLUMN dikonfirmasi_pada confirmed_at DATETIME(6) NULL,
    CHANGE COLUMN dibuat_pada created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CHANGE COLUMN diperbarui_pada updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6);

ALTER TABLE basai_audit_pengaturan
    CHANGE COLUMN pelaku_id actor_id INT NULL,
    CHANGE COLUMN aksi action VARCHAR(32) NOT NULL,
    CHANGE COLUMN jenis_entitas entity_type VARCHAR(80) NOT NULL,
    CHANGE COLUMN kunci_entitas entity_key VARCHAR(160) NOT NULL,
    CHANGE COLUMN sebelum_json before_json LONGTEXT NULL,
    CHANGE COLUMN sesudah_json after_json LONGTEXT NULL,
    CHANGE COLUMN alamat_ip ip_address VARCHAR(45) NULL,
    CHANGE COLUMN dibuat_pada created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6);

RENAME TABLE
    basai_media_sidang TO basai_captures,
    basai_detail_profil_kanal TO basai_channel_profile_items,
    basai_profil_kanal TO basai_channel_profiles,
    basai_penyelesaian_sidang TO basai_hearing_completions,
    basai_peran TO basai_roles,
    basai_audit_pengaturan TO basai_setting_audits,
    basai_pengaturan TO basai_settings,
    basai_pemetaan_pembicara TO basai_speaker_mappings;

ALTER TABLE basai_channel_profile_items
    ADD CONSTRAINT fk_basai_channel_profile_items_profile
        FOREIGN KEY (profile_id)
        REFERENCES basai_channel_profiles (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    ADD CONSTRAINT fk_basai_channel_profile_items_role
        FOREIGN KEY (role_id)
        REFERENCES basai_roles (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL;

ALTER TABLE basai_speaker_mappings
    ADD CONSTRAINT fk_basai_speaker_mappings_role
        FOREIGN KEY (role_id)
        REFERENCES basai_roles (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;

SET FOREIGN_KEY_CHECKS = @basai_fk_checks_lama;
