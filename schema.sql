-- 极客科技数字员工系统 - 数据库初始化脚本
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS digital_employee CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE digital_employee;

-- 对话历史记录表
CREATE TABLE IF NOT EXISTS conversation_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL COMMENT '会话ID',
    role ENUM('user', 'assistant', 'system') NOT NULL COMMENT '消息角色',
    content TEXT NOT NULL COMMENT '消息内容',
    intent VARCHAR(20) DEFAULT NULL COMMENT '意图：knowledge/action/human',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_thread_id (thread_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50) PRIMARY KEY,
    status VARCHAR(20) NOT NULL DEFAULT '待处理',
    logistics TEXT,
    items TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 工单表
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    issue_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT '待处理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入初始模拟订单数据（可选）
INSERT INTO orders (order_id, status, logistics, items) VALUES
('ORD-20260411-1234', '已发货', '中通快递 运单号：ZT123456789，预计4月13日送达', '极客智能音箱 x1'),
('ORD-20260410-5678', '待发货', '仓库处理中，预计今日发货', '极客无线耳机 x2'),
('ORD-20260409-9999', '已签收', '顺丰快递 运单号：SF123456789，已于4月11日签收', '极客机械键盘 x1')
ON DUPLICATE KEY UPDATE order_id=order_id;

-- 可选：创建检查点表（如果使用 LangGraph MySQLSaver，首次启动会自动创建，此处预留）