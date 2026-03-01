# ModAPI 文档爬取工具

网易我的世界 ModAPI 文档爬取工具，基于 Playwright 实现，将在线文档爬取为本地 Markdown 文件。

## 功能

- 爬取稳定版 API 接口、事件、枚举值文档
- 爬取 Beta 更新文档
- 自动将 HTML 转换为格式化的 Markdown
- 支持并发爬取，速度快
- 优先使用系统已安装的 Edge/Chrome，无需额外下载浏览器

## 安装

```bash
pip install playwright beautifulsoup4 markdownify mdformat
```

> **浏览器说明**: 程序会自动检测并使用系统已安装的 Edge 或 Chrome 浏览器。  
> 如果系统没有这些浏览器，需要运行 `playwright install chromium` 下载 Playwright 内置的 Chromium。

## 使用

```bash
python main.py                  # 交互式菜单
python main.py --stable         # 爬取所有稳定版文档 (API + 事件 + 枚举值)
python main.py --stable api     # 只爬取 API 接口文档
python main.py --stable events  # 只爬取事件文档
python main.py --stable enums   # 只爬取枚举值文档
python main.py --beta <URL>     # 爬取指定的 Beta 更新文档
```

### Beta 文档 URL 示例

```
https://mc.163.com/dev/mcmanual/mc-dev/mcdocs/1-ModAPI-beta/更新信息/3.7.html
```

## 输出

爬取的文档保存在 `ModAPI/` 目录下，按照原始文档结构组织为 Markdown 文件。

## 配置

可在 `config.py` 中调整以下参数：

| 参数             | 默认值 | 说明                    |
| ---------------- | ------ | ----------------------- |
| `timeout`        | 30000  | 页面加载超时时间 (毫秒) |
| `max_retries`    | 2      | 请求失败最大重试次数    |
| `headless`       | True   | 是否使用无头模式        |
| `max_concurrent` | 16     | 最大并发爬取数          |

---

> 💡 **提示**: 文档内容版权归网易所有，本工具仅提供离线阅读便利。
