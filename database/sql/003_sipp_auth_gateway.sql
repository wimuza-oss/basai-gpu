-- BAS-AI D5E - Gateway autentikasi SIPP
-- Perubahan object hanya di database basai.
-- Runtime basai_app tidak diberi SELECT langsung ke database soreang.
-- Jalankan sebagai account DBA yang memiliki SELECT ke soreang.sys_*.

USE basai;

DROP PROCEDURE IF EXISTS basai_autentikasi_sipp;

DELIMITER //

CREATE PROCEDURE basai_autentikasi_sipp(
    IN p_username VARCHAR(30),
    IN p_password_md5 CHAR(32)
)
SQL SECURITY DEFINER
READS SQL DATA
BEGIN
    SELECT
        u.userid,
        u.fullname,
        u.username,
        MAX(CASE
            WHEN g.groupid = 1 AND g.enable = 1 THEN 1
            ELSE 0
        END) AS admin_basai
    FROM soreang.sys_users AS u
    INNER JOIN soreang.sys_user_group AS ug
        ON ug.userid = u.userid
    INNER JOIN soreang.sys_groups AS g
        ON g.groupid = ug.groupid
    WHERE u.username = p_username
      AND LOWER(u.password) = LOWER(p_password_md5)
      AND u.block = 0
      AND (u.user_expired IS NULL OR u.user_expired > NOW())
      AND g.enable = 1
      AND (
          g.groupid IN (1, 30, 500)
          OR g.name LIKE 'Panmud %'
          OR g.description LIKE 'Panitera Muda %'
      )
    GROUP BY
        u.userid,
        u.fullname,
        u.username
    LIMIT 1;
END//

DELIMITER ;

GRANT EXECUTE ON PROCEDURE basai.basai_autentikasi_sipp
TO 'basai_app'@'192.168.16.236';
