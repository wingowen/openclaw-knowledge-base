# 03-knowledge/rules/ - 配置规则

存放 YAML/JSON 配置文件：
- Notion 同步规则
- MCP 配置
- 其他系统配置

## 规则

- 修改前备份：`cp xxx.yaml xxx.yaml.bak`
- 格式校验：`python3 -c "import yaml; yaml.safe_load(open('xxx.yaml'))"`
