# ModAPI 文档爬取工具

网易我的世界 ModAPI 文档爬取工具，基于 Playwright 实现。

## 安装

```bash
pip install playwright beautifulsoup4 markdownify mdformat && playwright install chromium
```

## 使用

```bash
python main.py              # 交互式菜单
python main.py --stable     # 爬取所有稳定版文档
python main.py --stable api # 只爬取 API/events/enums
python main.py --beta <URL> # 爬取 Beta 文档
```

---

> 💡 **提示**: 文档内容版权归网易所有，本工具仅提供离线阅读便利。
