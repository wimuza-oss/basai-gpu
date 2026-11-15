-- BAS-AI D5E rollback
-- Perubahan hanya di database basai.

USE basai;

REVOKE EXECUTE ON PROCEDURE basai.basai_autentikasi_sipp
FROM 'basai_app'@'192.168.16.236';

DROP PROCEDURE IF EXISTS basai_autentikasi_sipp;
