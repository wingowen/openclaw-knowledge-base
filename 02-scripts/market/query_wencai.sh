#!/bin/bash
# 问财选股查询脚本
# 使用 mcp_query_table 命令行工具

# 选股条件
QUERY="所属行业为[近期热门版块，即此版块具有一定的持续性] 且近10日有放量上涨 且最近3日成交量明显萎缩 且股价在20日均线上方 且非ST股 且非创业板且非科创板且非北交所"

# Chrome CDP 端口
CDP_PORT=${1:-9222}

echo "查询条件: $QUERY"
echo "CDP端口: $CDP_PORT"
echo "---"

# 使用 mcp_query_table 查询
# 注意：需要 Chrome 开启 --remote-debugging-port=$CDP_PORT
python3 -m mcp_query_table \
    --format csv \
    --endpoint "http://127.0.0.1:$CDP_PORT" \
    --transport stdio \
    -- "$QUERY" 2>&1 | tee /root/.openclaw/workspace/wencai_result.csv

echo ""
echo "结果已保存到: /root/.openclaw/workspace/wencai_result.csv"
