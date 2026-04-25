-- ============================================
-- Super Agent MySQL 初始化脚本
-- 用 root 用户执行: mysql -u root -p < init_db.sql
-- ============================================

CREATE DATABASE IF NOT EXISTS my_agent_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'agent'@'localhost' IDENTIFIED BY '123456';
CREATE USER IF NOT EXISTS 'agent'@'%' IDENTIFIED BY '123456';

GRANT ALL PRIVILEGES ON my_agent_db.* TO 'agent'@'localhost';
GRANT ALL PRIVILEGES ON my_agent_db.* TO 'agent'@'%';

FLUSH PRIVILEGES;

SELECT 'Database my_agent_db created, user agent granted.' AS Result;
