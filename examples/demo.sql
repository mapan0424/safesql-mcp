-- SafeSQL MCP 示例 SQL 文件
-- 用于演示风险审查功能

-- ✅ 低风险：带 WHERE 条件的安全查询
SELECT id, name, email FROM users WHERE status = 'active';

-- ✅ 低风险：安全的 INSERT
INSERT INTO orders (user_id, product_id, quantity) VALUES (1, 100, 2);

-- ✅ 低风险：安全的 UPDATE
UPDATE products SET stock = stock - 1 WHERE id = 100 AND stock > 0;

-- ✅ 低风险：安全的 DELETE
DELETE FROM sessions WHERE expired_at < NOW() - INTERVAL '7 days';

-- ⚠️ 中风险：SELECT * 会返回所有列
SELECT * FROM users WHERE department = 'engineering';

-- ⚠️ 中风险：前缀通配符
SELECT * FROM products WHERE name LIKE '%phone%';

-- ⚠️ 中风险：缺少列名的 INSERT
INSERT INTO logs VALUES (1, 'error', '2026-01-01');

-- 🔴 高风险：DROP TABLE 将被拦截
-- DROP TABLE users;

-- 🔴 高风险：无条件删除将被拦截
-- DELETE FROM orders;

-- 🔴 高风险：无条件更新将被拦截
-- UPDATE users SET status = 'inactive';

-- 🔴 高风险：权限操作将被拦截
-- GRANT ALL PRIVILEGES ON DATABASE mydb TO public;