"""
淘宝评价爬虫模块
用于抓取淘宝/天猫商品的用户评价
"""
import time
import pandas as pd
from playwright.sync_api import sync_playwright
from config import Config
import logging
from pathlib import Path
from tqdm import tqdm

# 配置日志
Config.ensure_dirs()
handlers = []
if Config.LOG_TO_CONSOLE:
    handlers.append(logging.StreamHandler())
if Config.LOG_TO_FILE:
    handlers.append(logging.FileHandler(Config.get_log_file(), encoding='utf-8'))

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)


class TaobaoScraper:
    """淘宝评价爬虫类"""
    
    def __init__(self, target_url, target_count=100):
        """
        初始化爬虫
        
        Args:
            target_url: 商品页面URL
            target_count: 目标抓取数量
            
        Raises:
            ValueError: 参数验证失败
            FileNotFoundError: 登录状态文件不存在
        """
        # 参数验证
        self._validate_params(target_url, target_count)
        
        self.target_url = target_url.strip()
        self.target_count = target_count
        self.final_data = []
        self.seen_uids = set()
        self.browser = None
        self.context = None
        self.page = None
        
    def _validate_params(self, url, count):
        """验证参数"""
        if not url or not isinstance(url, str):
            raise ValueError("❌ URL不能为空且必须是字符串")
        
        url = url.strip()
        if not url.startswith("http"):
            raise ValueError(f"❌ 无效的URL: {url}")
        
        if not isinstance(count, int) or count <= 0:
            raise ValueError("❌ target_count 必须是大于0的整数")
        
        if not Config.AUTH_FILE.exists():
            raise FileNotFoundError(
                f"❌ 未找到登录状态文件: {Config.AUTH_FILE}\n"
                f"请先运行 'python taobao_login.py' 完成登录"
            )
    
    def _init_browser(self):
        """初始化浏览器"""
        logger.info("正在启动浏览器...")
        p = sync_playwright().start()
        self.browser = p.chromium.launch(headless=Config.HEADLESS)
        self.context = self.browser.new_context(
            storage_state=str(Config.AUTH_FILE)
        )
        self.page = self.context.new_page()
        logger.info("✓ 浏览器启动成功")
    
    def _goto_review_page(self):
        """访问商品页并进入评价区"""
        logger.info(f"正在访问商品页...")
        self.page.goto(self.target_url)
        logger.info("✓ 页面加载完成")
        
        # 点击"用户评价"标签
        try:
            review_tab = self.page.locator(
                Config.SELECTORS['review_tab']
            ).filter(has_text="用户评价")
            
            if review_tab.is_visible():
                review_tab.click()
                self.page.wait_for_timeout(Config.PAGE_LOAD_WAIT)
                logger.info("✓ 已切换到用户评价标签")
            
            # 点击"查看全部评价"
            show_all = self.page.locator(
                Config.SELECTORS['show_all_button']
            ).filter(has_text="查看全部评价")
            
            if show_all.is_visible():
                show_all.click()
                self.page.wait_for_timeout(Config.PAGE_LOAD_WAIT)
                logger.info("✓ 已进入全量评价模式")
                
        except Exception as e:
            logger.warning(f"⚠️  初始化评价区时出现问题: {e}")
            logger.warning("继续尝试抓取...")
    
    def _expand_folded_reviews(self):
        """展开折叠的评价"""
        try:
            fold_btn = self.page.locator(Config.SELECTORS['fold_button'])
            if fold_btn.is_visible():
                logger.info(">>> 发现折叠区域，正在解锁隐藏评价...")
                fold_btn.click()
                self.page.wait_for_timeout(Config.CLICK_WAIT)
                return True
        except Exception as e:
            logger.debug(f"检查折叠区域时出错: {e}")
        return False
    
    def _extract_reviews(self):
        """提取当前页面的所有评价"""
        items = self.page.locator(Config.SELECTORS['comment_card']).all()
        current_batch_count = 0
        
        for item in items:
            try:
                # 提取数据字段
                user = item.locator(Config.SELECTORS['user_name']).inner_text().strip()
                meta = item.locator(Config.SELECTORS['meta_info']).inner_text().strip()
                content = item.locator(Config.SELECTORS['content']).first.inner_text().strip()
                
                # 检查是否有追评
                append_content = ""
                append_box = item.locator(Config.SELECTORS['append_box'])
                if append_box.count() > 0:
                    try:
                        append_content = append_box.locator(
                            Config.SELECTORS['append_content']
                        ).inner_text().strip()
                    except:
                        pass
                
                # 生成唯一 ID 防止重复记录
                uid = f"{user}_{content[:15]}"
                if uid not in self.seen_uids:
                    self.seen_uids.add(uid)
                    self.final_data.append({
                        "用户名": user,
                        "元数据": meta,
                        "初次评价": content,
                        "追评内容": append_content
                    })
                    current_batch_count += 1
                    
            except Exception as e:
                logger.debug(f"提取单条评价失败: {e}")
                continue
        
        return current_batch_count
    
    def scrape(self):
        """
        开始抓取评价
        
        Returns:
            DataFrame: 抓取到的评价数据
        """
        logger.info("=" * 60)
        logger.info("淘宝评价爬虫启动")
        logger.info("=" * 60)
        logger.info(f"目标URL: {self.target_url}")
        logger.info(f"目标数量: {self.target_count}")
        logger.info("=" * 60)
        
        try:
            # 初始化浏览器
            self._init_browser()
            
            # 进入评价页
            self._goto_review_page()
            
            # 核心循环：滚动 + 展开 + 抓取
            retry_count = 0
            pbar = tqdm(total=self.target_count, desc="抓取进度", unit="条")
            
            while len(self.final_data) < self.target_count:
                # 展开折叠评价
                self._expand_folded_reviews()
                
                # 抓取当前页面
                batch_count = self._extract_reviews()
                
                # 更新进度条
                if batch_count > 0:
                    pbar.update(batch_count)
                
                # 检查是否达到目标
                if len(self.final_data) >= self.target_count:
                    logger.info(f"✓ 已达到目标数量 {self.target_count}")
                    break
                
                # 执行滚动
                self.page.mouse.wheel(0, Config.SCROLL_DISTANCE)
                self.page.wait_for_timeout(Config.SCROLL_WAIT)
                
                # 如果连续多次抓不到新数据，说明到底了
                if batch_count == 0:
                    retry_count += 1
                    if retry_count > Config.MAX_RETRIES:
                        logger.info("页面已到底，或无更多新评价加载")
                        break
                else:
                    retry_count = 0
            
            pbar.close()
            
            # 处理数据
            if self.final_data:
                df = pd.DataFrame(self.final_data)
                
                # 提取评价日期
                df['评价日期'] = df['元数据'].apply(
                    lambda x: x.split('\n')[0] if '\n' in str(x) else x[:11]
                )
                
                logger.info(f"🎉 抓取成功！共获得 {len(df)} 条评价")
                return df
            else:
                logger.warning("❌ 未抓取到任何数据")
                logger.warning("可能的原因：")
                logger.warning("  1. 页面弹出了验证码")
                logger.warning("  2. 登录状态已过期")
                logger.warning("  3. 商品页面结构改变")
                return None
                
        except Exception as e:
            logger.error(f"❌ 抓取过程出错: {e}")
            raise
        
        finally:
            # 关闭浏览器
            if self.browser:
                try:
                    self.browser.close()
                    logger.info("✓ 浏览器已关闭")
                except:
                    pass
    
    def save_data(self, df):
        """
        保存数据到文件
        
        Args:
            df: DataFrame数据
        """
        if df is None or df.empty:
            logger.warning("没有数据需要保存")
            return
        
        try:
            # 生成文件名
            timestamp = int(time.time())
            csv_file = Config.OUTPUT_DIR / f"reviews_{timestamp}.csv"
            json_file = Config.OUTPUT_DIR / f"reviews_{timestamp}.json"
            
            # 保存CSV
            df.to_csv(csv_file, index=False, encoding="utf-8-sig")
            logger.info(f"✓ CSV文件已保存: {csv_file}")
            
            # 保存JSON备份
            df.to_json(json_file, orient='records', force_ascii=False, indent=2)
            logger.info(f"✓ JSON备份已保存: {json_file}")
            
            print("\n" + "=" * 60)
            print("🎉 数据保存成功！")
            print(f"📁 CSV文件: {csv_file}")
            print(f"📁 JSON文件: {json_file}")
            print(f"📊 总计: {len(df)} 条评价")
            print("=" * 60 + "\n")
            
        except Exception as e:
            logger.error(f"❌ 保存数据失败: {e}")
            # 尝试紧急备份
            try:
                temp_file = Config.OUTPUT_DIR / f"temp_backup_{int(time.time())}.csv"
                df.to_csv(temp_file, index=False, encoding="utf-8-sig")
                logger.warning(f"⚠️  数据已紧急备份到: {temp_file}")
            except:
                logger.error("紧急备份也失败了，数据可能丢失！")


def scrape_taobao_reviews(item_url, target_count=100):
    """
    抓取淘宝/天猫商品评价的便捷函数
    
    Args:
        item_url: 商品URL
        target_count: 目标抓取数量
        
    Returns:
        DataFrame: 评价数据
    """
    scraper = TaobaoScraper(item_url, target_count)
    df = scraper.scrape()
    if df is not None:
        scraper.save_data(df)
    return df


if __name__ == "__main__":
    # 使用示例
    ITEM_URL = "https://detail.tmall.com/item.htm?id=674605142427"
    TARGET_COUNT = 50  # 测试用，可以改为更大的数字
    
    try:
        scrape_taobao_reviews(ITEM_URL, TARGET_COUNT)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断抓取")
    except Exception as e:
        print(f"\n❌ 抓取失败: {e}")
        exit(1)
