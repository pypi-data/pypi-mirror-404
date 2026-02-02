
# raytoolsbox

一个不断进化的 **个人 Python 工具合集（Toolbox）**。  
包含常用开发工具、实用脚本、个人算法、桌面应用助手、Web 小工具等。

项目以 **模块化、可扩展、易维护** 为目标，为日常开发与个人项目提供稳定的工具支持。

---

## ✨ 特性（Features）

- 📧 **邮件工具**  
  简洁易用的邮件发送函数，可自动读取本地或用户目录的配置文件，自动处理 SSL、中文昵称等问题。

- 🔐 **个人加密算法（计划中）**  
  自定义加密/解密模块，适用于本地存储与信息传输。

- 🌐 **Web 工具（计划中）**  
  轻量级 FastAPI/Flask 封装，用于快速构建本地服务或 API。

- 🖥️ **屏幕工具 & GUI 工具（计划中）**  
  自动 DPI 检测、屏幕尺寸工具、Tkinter/Qt 通用辅助函数。

- 🧰 **更多工具持续加入中……**

---

## 📦 安装（Installation）

### 使用 uv（推荐）
```
uv add raytoolsbox
```

### 使用 pip
```
pip install raytoolsbox
```

---

## 🚀 快速开始（Quick Start）



---

## 📂 目录结构（Project Layout）

```
raytoolsbox/
│
├── pyproject.toml         # 项目信息 + 依赖管理（uv）
├── README.md              # 项目文档
├── src/
│   └── raytoolsbox/
│       ├── __init__.py
│       └── maillToPhone.py
│
└── tests/
    └── test_send_email.py # pytest 单元测试
```

---

## 🧪 测试（Testing）

本项目使用 pytest：

```
uv run pytest
```

全部测试应通过：

```
2 passed
```

---

## 🛠️ 开发路线图（Roadmap）

### 已完成
- [x] 邮件发送工具封装
- [x] 可本地覆盖的配置系统
- [x] pytest 自动化测试（mock 网络发送）
- [x] 个人加密算法模块（AES + 自定义混淆）
- [x] 计时工具

### 开发中 / 计划中
- [ ] Web 工具（FastAPI/Flask 封装）
- [ ] 屏幕工具（DPI、尺寸测量、窗口工具）
- [ ] Tkinter / PySide6 GUI 工具类
- [ ] 文件操作工具（临时文件、下载器）
- [ ] 日期工具、定时工具、任务提醒系统
- [ ] 扩展 CLI（命令行使用工具箱）

如果你有想加入的功能欢迎告诉我！

---

## 🤝 贡献（Contributing）

欢迎 Issue 或 PR！  
可提交：

- Bug 报告  
- 新功能建议  
- 工具模块  
- 文档改进  

---

## 📄 License

使用 MIT License，自由商用/修改/发布。

---
