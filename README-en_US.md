# Jim Grasscutter Server Launcher

[中文](README.md)

![JGSL Logo](Assets/JGSL-Logo.ico)

[Introduction Video](https://www.bilibili.com/video/BV1B1VqzWEY7)

## Features

- Multi-instance server management with innovative cluster functionality for rapid multi-region deployment (under development)
  
- Graphical configuration file editor - easy, fast, simple and intuitive, no more manual JSON editing
  
- Rich resource downloads including databases, JDK, gacha pools, plugins, and cores - everything you need
  
- Comprehensive monitoring features showing UpTime, CPU usage, memory usage, logs at a glance, plus console command sending (future plans include group control and abnormal command handling!)
  
- Convenient database management supporting import/export, one-click clearing, and graphical editing for operations impossible via commands (like renaming, changing UID)
  
- Multi-language internationalization support (in progress)
  
- Automatic update checking mechanism

## Documentation

- [Directory Structure](DirInfo.md)
  
- [Open Source License](LICENSE)
  
- [ToDo List](todolist.md)
  
- [Code of Conduct](CODE_OF_CONDUCT.md)
  
- [Ignore List](.gitignore)

## Quick Start

#### We recommend regular users download the packaged version from [Releases](https://github.com/Jimmy32767255/JimGrasscutterServerLauncher/releases) which requires no dependency installation - just unzip and run.

###### Note: Packaged versions in Releases may not be the latest!

### Alternatively, clone the repository and use the code:

#### Install dependencies:

```bash
pip install -r requirements.txt
```

#### Run JGSL:

```bash
./Start.bat
```

## Social Media

- QQ Group: 985349267
  
- [H.H.T.C.](https://t.me/Jimmy32767255_Community_recover)

## Known Issues

1. Opening the monitoring panel may cause the server log to generate millions of EOF lines. This issue originates from line 341 of Grasscutter.java and occurs sporadically with unknown causes. If encountered, please disable the console (game.enableConsole) in the configuration file and use opencommand instead.

2. First-time runs may experience unusually high lag despite low resource usage. The cause is unknown, but multiple restarts or prolonged usage may resolve the issue.
