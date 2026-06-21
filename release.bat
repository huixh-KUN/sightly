@echo off
chcp 65001 >nul

echo === Sightly 自动发布脚本 ===
echo.

rem 检查git状态
echo 1. 检查git状态...
git status --porcelain > git_status.txt
set /p git_status=<git_status.txt
del git_status.txt
if not "%git_status%" == "" (
    echo 错误：当前有未提交的更改，请先提交或 stash 更改！
    pause
    exit /b 1
)

rem 获取当前版本号
echo 2. 获取当前版本信息...
for /f "tokens=*" %%i in ('git describe --tags --abbrev^=0 2^>nul') do set current_tag=%%i
if "%current_tag%" == "" set current_tag=sightly_V1.0
echo 当前版本标签：%current_tag%

rem 提示输入新的版本号
echo 3. 请输入新的版本号：
echo    格式示例：sightly_V1.1 或 sightly_V2.0
set /p new_tag=新版本号：

rem 验证版本号格式
echo %new_tag% | findstr /r "^sightly_V[0-9][0-9]*\.[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo 错误：版本号格式不正确，请使用 sightly_VX.Y 格式（X和Y为数字）
    pause
    exit /b 1
)

rem 提示输入版本描述
echo 4. 请输入版本描述（可选）：
set /p tag_description=版本描述：

rem 创建并推送标签
echo 5. 创建并推送标签...
rem 检查标签是否已存在
git tag -l "%new_tag%" > git_tag_check.txt
set /p tag_exists=<git_tag_check.txt
del git_tag_check.txt
if not "%tag_exists%" == "" (
    echo ℹ️  标签 %new_tag% 已存在，跳过创建步骤
) else (
    git tag -a "%new_tag%" -m "%tag_description%"
    echo ✅ 标签 %new_tag% 已创建成功！
)
rem 推送标签（无论是否新创建，确保远程仓库有该标签）
git push origin "%new_tag%" 2>nul || echo ℹ️  标签 %new_tag% 已存在于远程仓库，跳过推送步骤
echo ✅ 标签 %new_tag% 处理完成！

rem 推送代码到master分支
echo 6. 推送代码到master分支...
git push origin master
echo ✅ 代码已推送成功！

echo.
echo === 发布流程已启动 ===
echo GitHub Actions正在构建并发布版本 %new_tag%...
echo 请访问 https://github.com/[your-username]/sightly/actions 查看构建状态
echo 构建完成后，发布包将自动上传到 GitHub Releases
echo.
echo 发布成功！🎉
pause
