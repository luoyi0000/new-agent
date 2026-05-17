-- =============================================================================
-- Migration: 001_add_conversation_logs_fts
-- Description: 为 conversation_logs 表添加 PostgreSQL 全文搜索索引
--
-- conversation_logs 表存储用户与 AI 助手的会话历史（L3 冷检索）。
-- 该表的 user_message 和 agent_reply 字段频繁用于 ILIKE 模糊搜索。
-- 当数据量增长（>10万行）时，ILIKE 搜索性能退化严重。
--
-- 解决方案：
-- 使用 PostgreSQL GIN 索引 + to_tsvector 实现全文搜索，
-- 比 ILIKE 快 10-100 倍，支持词干分析和排名。
--
-- 使用方法：
--   psql -U library_user -d library -f scripts/migrations/001_add_conversation_logs_fts.sql
-- =============================================================================

-- 1. 创建 TSVECTOR 列（存储预处理后的文本向量）
ALTER TABLE conversation_logs
    ADD COLUMN IF NOT EXISTS fts_vector tsvector
    GENERATED ALWAYS AS (
        to_tsvector('simple',
            COALESCE(user_message, '') || ' ' || COALESCE(agent_reply, '')
        )
    ) STORED;

-- 2. 创建 GIN 索引（加速全文搜索）
CREATE INDEX IF NOT EXISTS idx_conversation_logs_fts
    ON conversation_logs
    USING GIN (fts_vector);

-- 3. 创建复合索引（按用户过滤后的全文搜索加速）
CREATE INDEX IF NOT EXISTS idx_conversation_logs_user_fts
    ON conversation_logs
    USING GIN (user_id, fts_vector);

-- 4. 创建 created_at 降序索引（加速"最近记录"查询）
CREATE INDEX IF NOT EXISTS idx_conversation_logs_user_created
    ON conversation_logs (user_id, created_at DESC);

-- 5. 创建 intent 过滤索引（按意图分类查询）
CREATE INDEX IF NOT EXISTS idx_conversation_logs_intent
    ON conversation_logs (user_id, intent, created_at DESC);

-- =============================================================================
-- 回滚脚本（如果需要）
-- =============================================================================
-- DROP INDEX IF EXISTS idx_conversation_logs_intent;
-- DROP INDEX IF EXISTS idx_conversation_logs_user_created;
-- DROP INDEX IF EXISTS idx_conversation_logs_user_fts;
-- DROP INDEX IF EXISTS idx_conversation_logs_fts;
-- ALTER TABLE conversation_logs DROP COLUMN IF EXISTS fts_vector;
