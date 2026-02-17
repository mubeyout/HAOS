#!/bin/bash
# 部署修复代码到 Home Assistant
# 将此脚本保存为 deploy_fix.sh 并运行

echo "=== 部署南网阶梯电价修复代码 ==="
echo ""

HA_CONFIG_DIR="/config"
CUSTOM_COMP_DIR="$HA_CONFIG_DIR/custom_components/HA-grid-south-master"

# 检查 HA 配置目录
if [ ! -d "$HA_CONFIG_DIR" ]; then
    echo "错误: HA 配置目录不存在: $HA_CONFIG_DIR"
    echo "请确认 Home Assistant 的配置目录路径"
    echo ""
    echo "如果 HA 在 Docker 中运行，请使用:"
    echo "  docker exec -it homeassistant bash"
    echo "然后运行此脚本"
    exit 1
fi

# 检查自定义组件目录
if [ ! -d "$CUSTOM_COMP_DIR" ]; then
    echo "错误: 集成目录不存在: $CUSTOM_COMP_DIR"
    echo "请确认集成已正确安装"
    exit 1
fi

# 备份原文件
echo "1. 备份原文件..."
BACKUP_DIR="$CUSTOM_COMP_DIR/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp "$CUSTOM_COMP_DIR/csg_client/__init__.py" "$BACKUP_DIR/"
cp "$CUSTOM_COMP_DIR/csg_client/const.py" "$BACKUP_DIR/"
echo "  已备份到: $BACKUP_DIR"
echo ""

# 复制修改后的文件
echo "2. 部署新文件..."
SOURCE_DIR="/Volumes/Samsung_T5/Mubey-Work/HAOS/HA-grid-south-master"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "错误: 源目录不存在: $SOURCE_DIR"
    echo "请确认路径正确"
    exit 1
fi

cp "$SOURCE_DIR/csg_client/__init__.py" "$CUSTOM_COMP_DIR/csg_client/__init__.py"
cp "$SOURCE_DIR/csg_client/const.py" "$CUSTOM_COMP_DIR/csg_client/const.py"
cp "$SOURCE_DIR/sensor.py" "$CUSTOM_COMP_DIR/sensor.py"

echo "  已复制以下文件:"
echo "    - csg_client/__init__.py"
echo "    - csg_client/const.py"
echo "    - sensor.py"
echo ""

# 清除 Python 缓存
echo "3. 清除 Python 缓存..."
find "$CUSTOM_COMP_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find "$CUSTOM_COMP_DIR" -name "*.pyc" -delete 2>/dev/null
echo "  已清除缓存"
echo ""

echo "✓ 部署完成！"
echo ""
echo "下一步操作:"
echo "1. 在 Home Assistant 中重新加载集成"
echo "   或"
echo "2. 重启 Home Assistant"
echo ""
echo "3. 查看日志验证修复:"
echo "   搜索 'Normalized area_code' 或 '050100 -> 050000'"
echo ""
