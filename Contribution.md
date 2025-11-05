# 如何贡献
[参考](https://docs.maa.plus/zh-cn/develop/development.html)
## 完整环境配置流程（Windows）

1. 如果以前Fork过，现在自己仓库的 `Settings`里翻到最下面，删除
2. 打开[主仓库](https://github.com/UnsleepingDawn/SMCLabDailyManager)，点击`Fork`，继续点击`Create fork`
3. 克隆你自己仓库下的 dev 分支到本地，并拉取子模块

```bash
git clone --recurse-submodules <你的仓库的 git 链接> -b dev
```
注意：如果正在使用 Visual Studio 等不附带 --recurse-submodules 参数的 Git GUI，则需在克隆后再执行 git submodule update --init 以拉取子模块。

4. 需要有 Python 环境，请自行搜索 Python 安装教程
5. 配置环境
6. 开发过程中，每一定数量，记得提交一个 Commit, 别忘了写上 Message

## Commit Message格式（约定式提交）

类型 | 描述 | 示例 
---|---|---
feat | 新功能 | feat: 添加用户登录功能
fix |修复bug|fix: 解决首页图片无法加载的问题
docs|仅文档修改|docs: 更新API接口文档
style|代码风格调整（不影响代码逻辑）|style: 按照ESLint规则格式化代码
refactor|代码重构（既非新增功能，也非修复bug）|refactor: 优化用户模块的数据查询方法
perf|性能优化|perf: 使用缓存优化列表渲染速度
test|增加或修改测试用例|test: 为用户注册功能添加单元测试
build|构建系统或外部依赖的更改|build: 更新webpack配置/ build: 升级axios到最新版本
ci|持续集成相关的更改|ci: 在GitHub Actions中配置自动化测试
chore|杂项事务（非src或test文件的修改）|chore: 更新package.json中的脚本命令
revert|回滚之前的提交|revert: 回滚某次错误的提交