"""
淘宝登录模块
用于扫码登录淘宝并保存登录状态
"""
from playwright.sync_api import sync_playwright
from config import Config
import logging

# 配置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler() if Config.LOG_TO_CONSOLE else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)


def login_and_save():
    """
    启动浏览器，打开淘宝登录页，等待用户扫码登录，
    然后保存登录状态到 auth.json
    
    Raises:
        Exception: 如果登录失败或超时
    """
    logger.info("=" * 60)
    logger.info("淘宝登录模块启动")
    logger.info("=" * 60)
    
    # 确保目录存在
    Config.ensure_dirs()
    
    with sync_playwright() as p:
        try:
            # 启动浏览器
            logger.info(f"正在启动 {Config.BROWSER_TYPE} 浏览器...")
            browser = p.chromium.launch(headless=Config.HEADLESS)
            context = browser.new_context()
            page = context.new_page()
            
            # 访问淘宝登录页
            logger.info("正在访问淘宝登录页...")
            page.goto("https://login.taobao.com/")
            logger.info("✓ 页面加载完成")
            
            # 提示用户扫码
            print("\n" + "=" * 60)
            print("📱 请使用手机淘宝APP扫码登录")
            print("⏱️  等待登录中...（超时时间：60秒）")
            print("=" * 60 + "\n")
            
            # 等待用户登录成功（通过检测页面是否跳转到首页来判断）
            try:
                page.wait_for_url(
                    "https://i.taobao.com/**",  # 使用通配符匹配
                    timeout=Config.LOGIN_TIMEOUT
                )
                logger.info("✓ 登录成功！")
            except Exception as e:
                logger.error(f"❌ 登录超时或失败: {e}")
                logger.error("请确保：")
                logger.error("  1. 使用淘宝APP（不是支付宝）扫码")
                logger.error("  2. 扫码后在手机上确认登录")
                logger.error("  3. 网络连接正常")
                raise
            
            # 保存登录状态
            logger.info(f"正在保存登录状态到 {Config.AUTH_FILE}...")
            context.storage_state(path=str(Config.AUTH_FILE))
            logger.info("✓ 登录状态已保存")
            
            # 成功提示
            print("\n" + "=" * 60)
            print("🎉 登录成功！")
            print(f"📁 登录状态已保存到: {Config.AUTH_FILE}")
            print("💡 下次运行爬虫时无需重复登录")
            print("=" * 60 + "\n")
            
        except Exception as e:
            logger.error(f"❌ 登录过程出错: {e}")
            raise
        
        finally:
            # 关闭浏览器
            try:
                browser.close()
                logger.info("✓ 浏览器已关闭")
            except:
                pass


if __name__ == "__main__":
    try:
        login_and_save()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断登录")
    except Exception as e:
        print(f"\n❌ 登录失败: {e}")
        exit(1)
