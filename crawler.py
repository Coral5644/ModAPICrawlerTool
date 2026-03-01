# -*- coding: utf-8 -*-
"""
ModAPI文档爬虫核心模块 - 使用Playwright处理JavaScript渲染页面
优化版：使用markdownify进行HTML转MD转换，支持并发爬取
"""

import os
import re
import asyncio
from urllib.parse import urljoin, urlparse, unquote
from playwright.async_api import async_playwright, Page, Browser
from markdownify import markdownify as md
import mdformat
from config import CRAWL_CONFIG, OUTPUT_CONFIG


class ModAPICrawler:
    """ModAPI文档爬虫类"""

    def __init__(self):
        self.browser: Browser = None
        self.context = None
        self.playwright = None
        self.visited_urls = set()

    async def init_browser(self):
        """初始化浏览器（优先使用系统已安装的 Edge/Chrome）"""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            # 优先尝试使用系统已安装的浏览器，避免下载 Playwright 自带的 Chromium
            for channel in ("msedge", "chrome", None):
                try:
                    launch_args = {"headless": CRAWL_CONFIG["headless"]}
                    if channel:
                        launch_args["channel"] = channel
                    self.browser = await self.playwright.chromium.launch(**launch_args)
                    if channel:
                        print(f"  使用系统浏览器: {channel}")
                    break
                except Exception:
                    if channel is None:
                        raise  # 所有方式都失败，抛出原始异常
                    continue
            self.context = await self.browser.new_context()

    async def close_browser(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def fetch_page_content(self, url: str, retries: int = 0) -> tuple:
        """
        获取页面内容

        Args:
            url: 页面URL
            retries: 当前重试次数

        Returns:
            (标题, HTML内容) 或 (None, None)
        """
        page = None
        try:
            page = await self.context.new_page()
            page.set_default_timeout(CRAWL_CONFIG["timeout"])

            await page.goto(url, wait_until="networkidle")
            await page.wait_for_selector(".theme-default-content", timeout=15000)

            # 提取标题和内容
            result = await page.evaluate(
                """() => {
                const content = document.querySelector('.theme-default-content');
                if (!content) return null;
                
                // 获取标题
                const h1 = content.querySelector('h1');
                let title = '';
                if (h1) {
                    title = h1.textContent.replace(/^#\\s*/, '').trim();
                }
                
                // 克隆并清理内容
                const clone = content.cloneNode(true);
                
                // 移除不需要的元素（但保留代码块）
                const removeSelectors = [
                    'script', 'style', '.header-anchor', '.page-nav',
                    '.page-edit', '.contributors', '.edit-link', '.last-updated'
                ];
                for (const selector of removeSelectors) {
                    clone.querySelectorAll(selector).forEach(el => el.remove());
                }
                
                // 只移除复制按钮，不移除代码块容器
                clone.querySelectorAll('button').forEach(el => {
                    if (el.textContent.includes('复制') || el.className.includes('copy')) {
                        el.remove();
                    }
                });
                
                // 清理代码块外的extra-class容器中的非代码元素
                clone.querySelectorAll('.extra-class').forEach(el => {
                    // 如果不包含pre标签，则移除
                    if (!el.querySelector('pre') && !el.matches('pre')) {
                        // 检查是否是代码块的直接父元素
                        const hasPre = el.querySelector('pre');
                        if (!hasPre) {
                            el.remove();
                        }
                    }
                });
                
                return {
                    title: title,
                    html: clone.innerHTML
                };
            }"""
            )

            if result:
                return result["title"], result["html"]
            return None, None

        except Exception as e:
            if retries < CRAWL_CONFIG["max_retries"]:
                await asyncio.sleep(1)
                return await self.fetch_page_content(url, retries + 1)
            print(f"  ✗ 获取失败: {unquote(url)[:60]}... - {str(e)[:50]}")
            return None, None
        finally:
            if page:
                await page.close()

    def html_to_markdown(self, html: str) -> str:
        """
        将HTML转换为Markdown
        """
        if not html:
            return ""

        # 使用markdownify转换
        markdown = md(
            html,
            heading_style="ATX",
            bullets="-",
            code_language_callback=self._get_code_language,
            strip=["script", "style", "nav", "aside"],
        )

        # 清理转换结果
        markdown = self._clean_markdown(markdown)

        return markdown

    def _get_code_language(self, el):
        """获取代码块语言"""
        classes = el.get("class", [])
        if isinstance(classes, str):
            classes = classes.split()
        for cls in classes:
            if cls.startswith("language-"):
                return cls[9:]
            if cls.startswith("lang-"):
                return cls[5:]
        return ""

    def _clean_markdown(self, markdown: str) -> str:
        """清理Markdown内容"""
        # 将相对路径链接转换为完整URL
        base_url = "https://mc.163.com"
        markdown = re.sub(r"\]\(/dev/mcmanual/", f"]({base_url}/dev/mcmanual/", markdown)
        # 处理其他相对路径
        markdown = re.sub(r"\]\(\.\./", f"]({base_url}/dev/mcmanual/mc-dev/mcdocs/", markdown)

        # 移除多余的空行
        markdown = re.sub(r"\n{4,}", "\n\n\n", markdown)

        # 移除行尾空白
        lines = markdown.split("\n")
        lines = [line.rstrip() for line in lines]

        # 处理表格：确保表格前后有空行，移除表格行的缩进
        result_lines = []
        in_table = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            is_table_line = stripped.startswith("|") and stripped.endswith("|")

            if is_table_line:
                if not in_table:
                    # 表格开始，确保前面有空行
                    if result_lines and result_lines[-1] != "":
                        result_lines.append("")
                    in_table = True
                # 移除表格行的前导缩进
                result_lines.append(stripped)
            else:
                if in_table:
                    # 表格结束，确保后面有空行
                    if stripped != "":
                        result_lines.append("")
                    in_table = False
                result_lines.append(line)

        markdown = "\n".join(result_lines)

        # 移除开头的空行
        markdown = markdown.lstrip("\n")

        # 清理一些常见问题
        markdown = markdown.replace("\\#", "#")
        markdown = re.sub(
            r"复制\s*(python|lua|json|javascript|typescript|text|bash|shell)?",
            "",
            markdown,
        )

        # 移除指向原文档站点的链接，只保留文本
        markdown = re.sub(r"\[([^\]]+)\]\(https://mc\.163\.com[^)]*\)", r"\1", markdown)

        # 确保代码块前后有空行
        markdown = re.sub(r"([^\n])\n```", r"\1\n\n```", markdown)
        markdown = re.sub(r"```\n([^\n])", r"```\n\n\1", markdown)

        # 移除多余的连续空行
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)

        # 修复表格空单元格（两个空格改为一个空格）
        markdown = re.sub(r"\|  \|", "| |", markdown)

        # 用反引号包裹方括号内的值，避免被当作链接引用
        # 匹配 [0,1], [0~360], [True, False], [1.0, 1.0, 1.0f] 等
        markdown = re.sub(r"\[([0-9.,~\s]+f?)\]", r"`[\1]`", markdown)  # 数字范围
        markdown = re.sub(r"\[((?:True|False)(?:,\s*(?:True|False|[0-9.]+))*)\]", r"`[\1]`", markdown)  # 布尔值组合

        # 用反引号包裹代码内容，避免被误解析且渲染更美观
        # 匹配 ['xxx'] 或 ["xxx"] 格式的列表 (如 ['minecraft:is_food'])
        markdown = re.sub(r"(\['.+?'\]|\[\".+?\"\])", r"`\1`", markdown)
        # 匹配 list(xxx), dict(xxx), tuple(xxx) 等类型标注
        markdown = re.sub(r"\b((?:list|dict|tuple|set)\([^)]+\))", r"`\1`", markdown)
        # 匹配 list[xxx], dict[xxx] 等类型标注（方括号形式）
        markdown = re.sub(r"\b((?:list|dict|tuple|set)\[[^\]]+\])", r"`\1`", markdown)

        return markdown.strip()

    async def get_section_links(self, page: Page, section_name: str) -> list:
        """
        获取指定区块的所有链接
        """
        try:
            links_data = await page.evaluate(
                """
                (sectionName) => {
                    const links = [];
                    const sidebar = document.querySelector('.sidebar');
                    if (!sidebar) return links;
                    
                    // 找到ModAPI或ModAPI-beta区块
                    let modapiSection = null;
                    const topItems = sidebar.querySelectorAll(':scope > ul > li');
                    for (const item of topItems) {
                        const heading = item.querySelector(':scope > section > .sidebar-heading');
                        if (heading) {
                            const text = heading.textContent.trim();
                            if (text === 'ModAPI' || text === 'ModAPI-beta') {
                                modapiSection = item;
                                break;
                            }
                        }
                    }
                    
                    if (!modapiSection) return links;
                    
                    // 找目标区块
                    let targetSection = null;
                    const subItems = modapiSection.querySelectorAll('li');
                    for (const item of subItems) {
                        const heading = item.querySelector(':scope > section > .sidebar-heading');
                        if (heading && heading.textContent.trim() === sectionName) {
                            targetSection = item;
                            break;
                        }
                    }
                    
                    if (!targetSection) return links;
                    
                    // 获取所有链接
                    const allLinks = targetSection.querySelectorAll('a');
                    for (const link of allLinks) {
                        const text = link.textContent.trim();
                        let href = link.getAttribute('href');
                        if (!href || !text) continue;
                        
                        // 跳过纯锚点链接
                        if (href.startsWith('#')) continue;
                        if (href.includes('#') && !href.includes('.html')) continue;
                        
                        // 移除锚点
                        href = href.split('#')[0];
                        
                        if (!href.includes('.html')) continue;
                        
                        if (!links.some(l => l.url === href)) {
                            links.push({ name: text, url: href });
                        }
                    }
                    
                    return links;
                }
            """,
                section_name,
            )

            # 转换为绝对URL
            current_url = page.url
            result = []
            seen = set()

            for item in links_data:
                abs_url = urljoin(current_url, item["url"])
                clean_url = abs_url.split("?")[0].split("#")[0]
                if clean_url not in seen:
                    seen.add(clean_url)
                    result.append((item["name"], clean_url))

            return result

        except Exception as e:
            print(f"  获取链接失败: {e}")
            return []

    def url_to_filename(self, url: str) -> str:
        """将URL转换为文件名"""
        parsed = urlparse(url)
        path = unquote(parsed.path)

        # 提取ModAPI之后的路径
        for prefix in ["/1-ModAPI/", "/1-ModAPI-beta/"]:
            if prefix in path:
                idx = path.find(prefix)
                path = path[idx + len(prefix) :]
                break

        path = path.lstrip("/")

        if path.endswith(".html"):
            path = path[:-5] + OUTPUT_CONFIG["file_extension"]

        if not path or path == OUTPUT_CONFIG["file_extension"]:
            path = "index" + OUTPUT_CONFIG["file_extension"]

        # 清理非法字符
        path = re.sub(r'[<>:"|?*]', "_", path)

        return path

    def save_markdown(self, content: str, filepath: str, title: str = ""):
        """保存Markdown文件"""
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        # 添加标题
        if title and not content.startswith(f"# {title}"):
            if not content.startswith("# "):
                content = f"# {title}\n\n{content}"

        # 移除无效的锚点后缀 (如 #模型1, #联机大厅-2)
        def fix_anchor(match):
            anchor = match.group(1)
            # 移除末尾的 -数字
            anchor = re.sub(r"-\d+$", "", anchor)
            # 移除末尾的数字（但不是 %XX 编码的一部分）
            while anchor and anchor[-1].isdigit():
                if len(anchor) >= 3 and anchor[-3] == "%" and anchor[-2] in "0123456789ABCDEFabcdef":
                    break
                anchor = anchor[:-1]
            return f"(#{anchor})"

        content = re.sub(r"\(#([^)]+)\)", fix_anchor, content)

        # 使用 mdformat 格式化，确保符合 Markdown 规范
        try:
            content = mdformat.text(content)
        except Exception as e:
            print(f"  mdformat 格式化失败: {e}")

        with open(filepath, "w", encoding=OUTPUT_CONFIG["encoding"]) as f:
            f.write(content)

    async def crawl_pages_concurrent(self, links: list, output_dir: str, max_concurrent: int = 5) -> int:
        """
        并发爬取多个页面
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        count = 0

        async def crawl_one(name: str, url: str):
            nonlocal count
            async with semaphore:
                clean_url = url.split("?")[0].split("#")[0]
                if clean_url in self.visited_urls:
                    return

                self.visited_urls.add(clean_url)

                title, html = await self.fetch_page_content(url)
                if html:
                    markdown = self.html_to_markdown(html)
                    if markdown:
                        filename = self.url_to_filename(url)
                        filepath = os.path.join(output_dir, filename)
                        self.save_markdown(markdown, filepath, title or name)
                        count += 1
                        print(f"  ✓ {name}")
                        return

                print(f"  ✗ {name}")

        # 创建所有任务
        tasks = [crawl_one(name, url) for name, url in links]
        await asyncio.gather(*tasks)

        return count

    async def crawl_documentation(self, index_url: str, section_name: str, output_dir: str) -> int:
        """
        爬取整个文档区块
        """
        print(f"\n开始爬取 {section_name}...")
        print(f"输出目录: {output_dir}")

        self.visited_urls.clear()

        await self.init_browser()

        try:
            # 获取索引页的链接
            page = await self.context.new_page()
            page.set_default_timeout(CRAWL_CONFIG["timeout"])

            print(f"  访问索引页...")
            await page.goto(index_url, wait_until="networkidle")
            await page.wait_for_selector(".theme-default-content", timeout=15000)

            links = await self.get_section_links(page, section_name)
            await page.close()

            if not links:
                print(f"  未找到任何链接!")
                return 0

            print(f"  找到 {len(links)} 个文档")
            print(f"  开始并发爬取 (最大并发: {CRAWL_CONFIG.get('max_concurrent', 5)})...\n")

            count = await self.crawl_pages_concurrent(links, output_dir, CRAWL_CONFIG.get("max_concurrent", 5))

            print(f"\n完成! 共爬取 {count} 个页面")
            return count

        finally:
            await self.close_browser()

    async def crawl_beta_page(self, url: str, output_dir: str) -> bool:
        """
        爬取Beta版本更新页面
        """
        print(f"\n爬取Beta更新文档...")
        print(f"URL: {unquote(url)}")
        print(f"输出: {output_dir}")

        await self.init_browser()

        try:
            title, html = await self.fetch_page_content(url)

            if not html:
                print("获取页面失败!")
                return False

            markdown = self.html_to_markdown(html)

            if not markdown:
                print("页面内容为空!")
                return False

            filename = self.url_to_filename(url)
            filepath = os.path.join(output_dir, filename)

            self.save_markdown(markdown, filepath, title)
            print(f"  ✓ 已保存: {filepath}")

            return True

        finally:
            await self.close_browser()


def run_crawler_sync(coro):
    """同步运行异步爬虫"""
    return asyncio.run(coro)
