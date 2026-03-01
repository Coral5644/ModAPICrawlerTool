# -*- coding: utf-8 -*-
"""
ModAPI文档爬取工具 - 命令行入口

用法:
    python main.py                    # 显示交互式菜单
    python main.py --stable           # 爬取所有稳定版文档
    python main.py --stable api       # 只爬取API文档
    python main.py --stable events    # 只爬取事件文档
    python main.py --stable enums     # 只爬取枚举值文档
    python main.py --beta <url>       # 爬取指定的Beta更新文档
"""

import os
import sys
import asyncio
import argparse
import unicodedata
from urllib.parse import unquote

from config import STABLE_DOCS, BETA_CONFIG
from crawler import ModAPICrawler


def get_display_width(s):
    """计算字符串在终端中的显示宽度 (处理中文字符)"""
    width = 0
    for char in s:
        if unicodedata.east_asian_width(char) in ("F", "W", "A"):
            width += 2
        else:
            width += 1
    return width


def print_banner():
    """打印工具横幅"""
    width = 62
    lines = [
        "网易我的世界 ModAPI 文档爬取工具",
        "Netease MC ModAPI Crawler",
        "(Playwright 版本)",
    ]

    print("╔" + "═" * width + "╗")
    for line in lines:
        content_width = get_display_width(line)
        padding = (width - content_width) // 2
        left_padding = " " * padding
        right_padding = " " * (width - content_width - padding)
        print(f"║{left_padding}{line}{right_padding}║")
    print("╚" + "═" * width + "╝")


async def crawl_stable_docs_async(doc_type=None):
    """
    异步爬取稳定版文档

    Args:
        doc_type: 文档类型 (api/events/enums), 为None时爬取全部
    """
    if doc_type:
        if doc_type not in STABLE_DOCS:
            print(f"错误: 未知的文档类型 '{doc_type}'")
            print(f"可用类型: {', '.join(STABLE_DOCS.keys())}")
            return
        docs_to_crawl = {doc_type: STABLE_DOCS[doc_type]}
    else:
        docs_to_crawl = STABLE_DOCS

    total_pages = 0
    crawler = ModAPICrawler()

    for key, config in docs_to_crawl.items():
        print(f"\n{'=' * 60}")
        print(f"正在爬取: {config['name']}")
        print(f"{'=' * 60}")

        count = await crawler.crawl_documentation(
            index_url=config["index_url"],
            section_name=config["nav_section"],
            output_dir=config["output_dir"],
        )
        total_pages += count

    print(f"\n{'=' * 60}")
    print(f"全部完成! 共爬取 {total_pages} 个页面")
    print(f"{'=' * 60}")


async def crawl_beta_doc_async(url):
    """
    异步爬取Beta更新文档

    Args:
        url: Beta文档URL
    """
    print(f"\n{'=' * 60}")
    print(f"正在爬取Beta更新文档")
    print(f"{'=' * 60}")

    crawler = ModAPICrawler()
    await crawler.crawl_beta_page(url, BETA_CONFIG["output_dir"])


def crawl_stable_docs(doc_type=None):
    """同步包装器"""
    asyncio.run(crawl_stable_docs_async(doc_type))


def crawl_beta_doc(url):
    """同步包装器"""
    asyncio.run(crawl_beta_doc_async(url))


def interactive_menu():
    """交互式菜单"""
    while True:
        print("\n" + "=" * 60)
        print("请选择操作:")
        print("=" * 60)
        print("1. 爬取所有稳定版文档 (API + 事件 + 枚举值)")
        print("2. 仅爬取API接口文档")
        print("3. 仅爬取事件文档")
        print("4. 仅爬取枚举值文档")
        print("5. 爬取Beta更新文档 (需输入URL)")
        print("6. 退出")
        print("-" * 60)

        choice = input("请输入选项 [1-6]: ").strip()

        if choice == "1":
            crawl_stable_docs()
        elif choice == "2":
            crawl_stable_docs("api")
        elif choice == "3":
            crawl_stable_docs("events")
        elif choice == "4":
            crawl_stable_docs("enums")
        elif choice == "5":
            print("\n请输入Beta更新文档URL:")
            print("示例: https://mc.163.com/dev/mcmanual/mc-dev/mcdocs/1-ModAPI-beta/更新信息/3.7.html")
            url = input("URL: ").strip()
            if url:
                crawl_beta_doc(url)
            else:
                print("URL不能为空!")
        elif choice == "6":
            print("\n感谢使用，再见!")
            break
        else:
            print("无效选项，请重新选择!")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="网易我的世界ModAPI文档爬取工具 (Playwright版本)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 显示交互式菜单
  python main.py --stable           # 爬取所有稳定版文档
  python main.py --stable api       # 只爬取API文档
  python main.py --stable events    # 只爬取事件文档
  python main.py --stable enums     # 只爬取枚举值文档
  python main.py --beta <url>       # 爬取指定的Beta更新文档

Beta文档URL示例:
  https://mc.163.com/dev/mcmanual/mc-dev/mcdocs/1-ModAPI-beta/更新信息/3.7.html

注意: 首次运行需要安装Playwright浏览器:
  playwright install chromium
        """,
    )

    parser.add_argument(
        "--stable",
        nargs="?",
        const="all",
        metavar="TYPE",
        help="爬取稳定版文档。TYPE可选: api, events, enums。不指定则爬取全部",
    )

    parser.add_argument("--beta", metavar="URL", help="爬取指定的Beta更新文档URL")

    args = parser.parse_args()

    print_banner()

    # 检查依赖
    try:
        import playwright
        from bs4 import BeautifulSoup
    except ImportError as e:
        print(f"错误: 缺少依赖库 - {e}")
        print("\n请运行以下命令安装依赖:")
        print("  pip install playwright beautifulsoup4")
        print("  playwright install chromium")
        return

    # 根据参数执行不同操作
    if args.stable:
        if args.stable == "all":
            crawl_stable_docs()
        else:
            crawl_stable_docs(args.stable)
    elif args.beta:
        crawl_beta_doc(args.beta)
    else:
        # 无参数时显示交互式菜单
        interactive_menu()


if __name__ == "__main__":
    main()
