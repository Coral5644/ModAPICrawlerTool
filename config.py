# -*- coding: utf-8 -*-
"""
ModAPI文档爬取工具配置文件
"""

# 基础URL
BASE_URL = "https://mc.163.com/dev/mcmanual/mc-dev/mcdocs"

# 稳定版API文档URL（使用URL编码的版本确保兼容性）
# 输出目录统一为 output/stable，子目录由URL路径决定（接口/事件/枚举值）
STABLE_DOCS = {
    "api": {
        "name": "接口文档",
        "index_url": f"{BASE_URL}/1-ModAPI/%E6%8E%A5%E5%8F%A3/Api%E7%B4%A2%E5%BC%95%E8%A1%A8.html?catalog=1",
        "nav_section": "接口",
        "output_dir": "ModAPI",
    },
    "events": {
        "name": "事件文档",
        "index_url": f"{BASE_URL}/1-ModAPI/%E4%BA%8B%E4%BB%B6/%E4%BA%8B%E4%BB%B6%E7%B4%A2%E5%BC%95%E8%A1%A8.html?catalog=1",
        "nav_section": "事件",
        "output_dir": "ModAPI",
    },
    "enums": {
        "name": "枚举值文档",
        "index_url": f"{BASE_URL}/1-ModAPI/%E6%9E%9A%E4%B8%BE%E5%80%BC/%E7%B4%A2%E5%BC%95.html?catalog=1",
        "nav_section": "枚举值",
        "output_dir": "ModAPI",
    },
}

# Beta文档配置
BETA_CONFIG = {"name": "Beta更新文档", "output_dir": "ModAPI/beta"}

# 爬取配置
CRAWL_CONFIG = {
    "timeout": 30000,  # 页面超时时间(毫秒)
    "max_retries": 2,  # 最大重试次数
    "headless": True,  # 是否使用无头模式
    "max_concurrent": 16,  # 最大并发数
}

# 输出配置
OUTPUT_CONFIG = {"encoding": "utf-8", "file_extension": ".md"}

# 需要排除的内容选择器
EXCLUDE_SELECTORS = [
    "script",
    "style",
    "nav",
    "header",
    "footer",
    "aside",
    ".sidebar",
    ".nav",
    ".menu",
    ".toc",
    ".navigation",
    ".breadcrumb",
    ".search",
    ".header-anchor",
    ".sidebar-links",
    ".page-nav",
    ".page-edit",
    ".contributors",
]
