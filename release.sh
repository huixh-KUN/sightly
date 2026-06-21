#!/bin/bash

# Sightly 自动发布脚本
# 用于在本地设置版本号，创建标签并推送，触发GitHub Actions自动构建和发布

echo "=== Sightly 自动发布脚本 ==="

# 检查git状态
echo "1. 检查git状态..."
if [ -n "$(git status --porcelain)" ]; then
    echo "错误：当前有未提交的更改，请先提交或 stash 更改！"
    exit 1
fi

# 获取当前版本号
echo "2. 获取当前版本信息..."
current_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "sightly_V1.0")
echo "当前版本标签：$current_tag"

# 提示输入新的版本号
echo "3. 请输入新的版本号："
echo "   格式示例：sightly_V1.1 或 sightly_V2.0"
read -p "新版本号：" new_tag

# 验证版本号格式
if [[ ! $new_tag =~ ^sightly_V[0-9]+\.[0-9]+$ ]]; then
    echo "错误：版本号格式不正确，请使用 sightly_VX.Y 格式（X和Y为数字）"
    exit 1
fi

# 提示输入版本描述
echo "4. 请输入版本描述（可选）："
read -p "版本描述：" tag_description

# 创建并推送标签
echo "5. 创建并推送标签..."
# 检查标签是否已存在
if git tag -l "$new_tag" >/dev/null 2>&1; then
    echo "ℹ️  标签 $new_tag 已存在，跳过创建步骤"
else
    git tag -a "$new_tag" -m "$tag_description"
    echo "✅ 标签 $new_tag 已创建成功！"
fi
# 推送标签（无论是否新创建，确保远程仓库有该标签）
git push origin "$new_tag" || echo "ℹ️  标签 $new_tag 已存在于远程仓库，跳过推送步骤"
echo "✅ 标签 $new_tag 处理完成！"

# 推送代码到master分支（如果有更新）
echo "6. 推送代码到master分支..."
git push origin master
echo "✅ 代码已推送成功！"

# 完成提示
echo "\n=== 发布流程已启动 ==="
echo "GitHub Actions正在构建并发布版本 $new_tag..."
echo "请访问 https://github.com/[your-username]/sightly/actions 查看构建状态"
echo "构建完成后，发布包将自动上传到 GitHub Releases"
echo "\n发布成功！🎉"
