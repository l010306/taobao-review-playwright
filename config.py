"""
淘宝爬虫配置文件
"""
import os
from pathlib import Path

class Config:
    """配置类 - 集中管理所有配置参数"""
    
    # ==================== 文件路径配置 ====================
    BASE_DIR = Path(__file__).parent
    AUTH_FILE = BASE_DIR / "auth.json"  # 登录状态文件
    OUTPUT_DIR = BASE_DIR / "data"      # 数据输出目录
    LOG_DIR = BASE_DIR / "logs"         # 日志目录
    
    # ==================== 浏览器配置 ====================
    HEADLESS = False                    # 是否无头模式
    BROWSER_TYPE = "chromium"           # 浏览器类型: chromium, firefox, webkit
    
    # ==================== 等待时间配置（毫秒） ====================
    LOGIN_TIMEOUT = 60000               # 登录等待超时（60秒）
    PAGE_LOAD_WAIT = 2000               # 页面加载等待（2秒）
    SCROLL_WAIT = 3000                  # 滚动后等待（3秒）
    CLICK_WAIT = 1000                   # 点击后等待（1秒）
    
    # ==================== 滚动参数配置 ====================
    SCROLL_DISTANCE = 1500              # 每次滚动距离（像素）
    MAX_RETRIES = 5                     # 最大重试次数（连续无新数据）
    
    # ==================== 数据抓取配置 ====================
    DEFAULT_TARGET_COUNT = 100          # 默认抓取评价数量
    CHECKPOINT_INTERVAL = 20            # 每抓取N条保存一次断点
    ENABLE_CHECKPOINT = False           # 是否启用断点续传（实验性功能）
    
    # ==================== 日志配置 ====================
    LOG_LEVEL = "INFO"                  # 日志级别: DEBUG, INFO, WARNING, ERROR
    LOG_TO_FILE = True                  # 是否保存日志到文件
    LOG_TO_CONSOLE = True               # 是否在控制台显示日志
    
    # ==================== CSS 选择器配置 ====================
    # 淘宝可能会改版，如果选择器失效，请在这里更新
    SELECTORS = {
        # 评价标签页
        "review_tab": 'div[class*="tabDetailItemTitle--"]',
        "show_all_button": 'div[class*="ShowButton--"]',
        
        # 折叠区域
        "fold_button": 'div[class*="foldInfoContent--"]',
        
        # 评论卡片
        "comment_card": 'div[class^="Comment--"]',
        "user_name": 'div[class^="userName--"]',
        "meta_info": 'div[class^="meta--"]',
        "content": 'div[class^="contentWrapper--"] div[class^="content--"]',
        "append_box": 'div[class^="append--"]',
        "append_content": 'div[class^="content--"]',
    }
    
    @classmethod
    def ensure_dirs(cls):
        """确保必要的目录存在"""
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        if cls.LOG_TO_FILE:
            cls.LOG_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_log_file(cls):
        """获取日志文件路径"""
        if not cls.LOG_TO_FILE:
            return None
        return cls.LOG_DIR / "taobao_scraper.log"
