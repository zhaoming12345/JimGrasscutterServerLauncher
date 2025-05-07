# Jim Grasscutter Server Launcher

# Jim割草机服务器启动器

![JGSL Logo](Assets/JGSL-Logo.ico)

[介绍视频](https://www.bilibili.com/video/BV1B1VqzWEY7)

## 已知问题

打开监控面板有可能会导致服务端日志中多出几百万行的EOF的问题，该问题是Grasscutter.java的341行导致，为偶发性故障且原因不明，如果遇到请在配置文件中禁用控制台(game.enableConsole)并使用opencommand。

## 功能特性

 - 多实例服务器管理，独创集群功能，快速多地区，让服务器管理不再困难。
 - 图形化配置文件编辑器，方便、快捷、简单、易懂，再也不用手动编辑json。
 - 丰富的资源下载，数据库、JDK、卡池、插件、核心，一应俱全。(正在修复权限问题)
 - 完善的监控功能，UpTime、CPU、内存占用、日志，一目了然，还能发送控制台指令。(未来还可能加入群控和异常指令处理！)
 - 多语言国际化支持(在做)
 - 自动更新检查机制(在做)

## 文档导航

 - [目录说明](DirInfo.md)
 - [开源协议](LICENSE)
 - [待办清单](todolist.md)
 - [行为准则](CODE_OF_CONDUCT.md)
 - [锁定列表](edit-lock.md)
 - [忽略列表](.gitignore)

## 快速开始

#### 我们建议普通用户直接下载[Releases](https://github.com/Jimmy32767255/JimGrasscutterServerLauncher/releases)中的打包版本，无需安装依赖，解压缩后即可直接运行。

### 或者，克隆仓库后使用代码：

#### 安装依赖：

```bash
pip install -r requirements.txt
```
#### 运行JGSL：

```bash
./Start.bat
```

## 社交媒体

 - QQ群：985349267

 - [狐狐技术社区 | H.H.T.C.](https://t.me/Jimmy32767255_Community_recover)
