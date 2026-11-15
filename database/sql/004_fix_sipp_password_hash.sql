-- BAS-AI D5G - Samakan hash autentikasi dengan algoritma SIPP legacy
-- Perubahan object hanya di database basai.
-- Berdasarkan source SIPP: arr2md5([code_activation, password]).
-- Laravel tetap mengirim md5(password), bukan plaintext password.

USE basai;

DROP FUNCTION IF EXISTS basai_hash_password_sipp;
DROP PROCEDURE IF EXISTS basai_autentikasi_sipp;

DELIMITER //

CREATE FUNCTION basai_hash_password_sipp(
    p_code_activation VARCHAR(255),
    p_password_md5 CHAR(32)
)
RETURNS CHAR(32)
DETERMINISTIC
NO SQL
BEGIN
    DECLARE v_hasil VARBINARY(32);
    DECLARE v_password_md5 CHAR(32);
    DECLARE v_i INT DEFAULT 1;
    DECLARE v_xor INT;

    IF p_code_activation IS NULL
       OR p_code_activation = ''
       OR p_password_md5 IS NULL
       OR CHAR_LENGTH(p_password_md5) <> 32 THEN
        RETURN NULL;
    END IF;

    SET v_hasil = MD5(p_code_activation);
    SET v_password_md5 = LOWER(p_password_md5);

    WHILE v_i <= 32 DO
        SET v_xor =
            ORD(SUBSTRING(v_hasil, v_i, 1))
            ^ ORD(SUBSTRING(v_password_md5, v_i, 1));

        SET v_hasil =
            INSERT(v_hasil, v_i, 1, CHAR(v_xor));

        SET v_i = v_i + 1;
    END WHILE;

    RETURN MD5(v_hasil);
END//

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
      AND u.code_activation IS NOT NULL
      AND u.code_activation <> ''
      AND LOWER(u.password) = LOWER(
          basai.basai_hash_password_sipp(
              u.code_activation,
              p_password_md5
          )
      )
      AND u.block = 0
      AND (u.user_expired IS NULL OR u.user_expired > NOW())
      AND g.enable = 1
      AND (
          g.groupid IN (1, 30, 430, 500, 1000, 1010)
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
