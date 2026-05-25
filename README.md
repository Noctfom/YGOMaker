# 🃏 YGOMaker — 游戏王制卡器

> Special thanks to [kooriookami/yugioh-card](https://github.com/kooriookami/yugioh-card) for the excellent Canvas-based card rendering engine.

一个面向游戏王自制卡的**一体化工具**，集卡图制作、CDB 数据管理、strings.conf 字段维护、官方数据库同步于一身。

---

## ✨ 功能

| 模块 | 说明 |
|------|------|
| 🃏 **制卡** | 可视化编辑卡片属性（类型/种族/攻击/效果文本…），Canvas 实时预览，一键写入 `cards.cdb` |
| 🖼️ **卡图** | 导入本地图片并正方形裁剪 |
| 📚 **卡片列表** | 搜索/浏览全部卡片（官方 + 自制），编辑已有卡片 |
| ⚙️ **数据管理** | 添加/删除自定义系列名、指示物、胜利条件 |
| 🔄 **官方同步** | 从萌卡仓库拉取最新 CDB / strings.conf / Lua 脚本 |
| 🔀 **增量融合** | 更新官方数据时自动保留自制卡和自定义字段 |
| 📥 **导入合并** | 导入他人的自制卡和配置，自动去重 |
| 📦 **导出** | 导出完整 `cards.cdb` / `strings.conf`，支持分享 |
| 🌐 **脚本库** | 自动同步 `ygopro-scripts`（13,000+ 官方 Lua 脚本） |

---

## 🚀 快速开始

### 环境要求

- **Python 3.11+**（必需）
- **Git**（可选 — 仅用于"拉取官方数据"功能，日常制卡不需要）

### 运行

```
双击根目录的 start.bat
浏览器自动打开 http://localhost:8848
```

首次启动会自动安装 Python 依赖（约 3 秒）。前端已预构建，无需 Node.js。

---

## 📁 项目结构

```
e:\YGOMaker\
├── start.bat                 # 一键启动
├── cards.cdb                 # 卡片数据库（SQLite3）
├── strings.conf              # 系统字符串/系列名表
├── script/                   # Lua 脚本库
├── ygmaker-server/           # Python 后端
│   ├── server.py             # FastAPI 主服务
│   ├── card_writer.py        # CDB 读写模块
│   ├── strings_parser.py     # strings.conf 解析器
│   ├── local_mods_tracker.py # 本地修改追踪
│   ├── card_reader.py        # CDB 读取工具
│   ├── update_tools.py       # 远程更新工具
│   ├── config.py             # 配置
│   └── backup/               # CDB 自动备份
└── yugioh-card-master/       # 前端（Vue 3 + Vite）
    ├── dist/                 # 生产构建
    └── src/                  # 源代码
```

---

## 🛠 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3, Vite, Element Plus, LeaferJS (Canvas 渲染) |
| 卡片渲染 | [yugioh-card](https://github.com/kooriookami/yugioh-card) |
| 后端 | Python 3, FastAPI, SQLite3 |
| 卡密策略 | 9 位数段 (100000000+) 避开官方 ID 空间 |

---

## 📄 License

本项目基于 [yugioh-card](https://github.com/kooriookami/yugioh-card)（ISC License）构建。

YGOMaker 部分同样以 ISC License 发布 — 自由使用、修改、分发。
