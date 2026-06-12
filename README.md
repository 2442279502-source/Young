# 工程算量小助手

Web 版建筑工程算量工具。输入构件尺寸，自动计算混凝土方量、钢筋估重、模板面积，支持导出 Excel 报表。

## 功能

- 输入构件尺寸（长/宽/高），自动计算
- 混凝土方量、钢筋估重、模板面积
- 多个构件汇总统计
- 一键导出 Excel 报表
- 浏览器 Web 界面

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3 + Flask |
| 前端 | HTML + CSS（原生） |
| 模板 | Jinja2 |
| 报表 | openpyxl |

## 快速启动

```bash
# 1. 安装依赖
pip install flask openpyxl

# 2. 启动应用
python app.py

# 3. 浏览器打开
# http://127.0.0.1:5001
```

## 项目结构

```
quantity-calc/
├── calc.py              # 核心计算函数
├── app.py               # Flask Web 应用
├── requirements.txt     # 依赖列表
├── .gitignore
├── templates/
│   └── index.html       # 前端页面
└── static/              # 导出的 Excel 文件
```

## 简历要点

> **工程算量小助手**（2026.06）
> - 独立开发 Web 版建筑工程算量工具，覆盖混凝土、钢筋、模板三类核心工程量计算
> - 基于 Flask + openpyxl 实现浏览器端交互式算量与 Excel 报表一键导出
> - 结合土木工程专业知识，将手工算量流程转化为自动化工具

## 作者

杨炜臻 · 佛山大学 2026 届土木工程
