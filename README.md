# taobao-review-playwright
A Playwright-based automated crawler for Taobao/Tmall product reviews. Featuring a modular architecture including automated login, core scraping engine, and configuration management, this system enables seamless data extraction and structured storage of product feedback.

# 淘宝/天猫评价爬虫项目说明

## 📋 项目简介

这是一个基于 **Playwright** 的淘宝/天猫商品评价自动化抓取系统。系统采用模块化设计，分为登录模块、爬虫模块和配置模块，能够自动登录淘宝、抓取商品评价并保存数据。

### 🎯 核心功能

- ✅ **自动化登录**：扫码登录淘宝，并保存登录状态
- ✅ **评价抓取**：自动抓取商品的用户评价（包括追评）
- ✅ **智能解析**：自动展开折叠的评价，滚动加载更多内容
- ✅ **数据去重**：防止重复抓取同一条评价
- ✅ **进度显示**：实时显示抓取进度
- ✅ **数据导出**：同时保存为CSV和JSON格式

### 🏗️ 项目架构

```
Taobao/
├── config.py              # 配置模块 - 集中管理所有配置参数
├── taobao_login.py        # 登录模块 - 处理淘宝扫码登录
├── taobao_scraper.py      # 爬虫模块 - 抓取商品评价数据
├── auth.json             # 登录态文件（自动生成）
├── data/                 # 数据目录（自动生成）
│   ├── reviews_*.csv
│   └── reviews_*.json
└── logs/                 # 日志目录（自动生成）
    └── taobao_scraper.log
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install playwright pandas tqdm

# 安装 Playwright 浏览器
playwright install chromium
```

### 2. 第一步：登录淘宝

```bash
python taobao_login.py
```

**运行流程**：
1. 自动打开Chrome浏览器
2. 访问淘宝登录页
3. 用手机淘宝APP扫码登录
4. 登录成功后自动保存到 `auth.json`

**重要**：
- ⚠️ 必须使用**淘宝APP**扫码（不是支付宝）
- ⚠️ `auth.json` 文件保存了登录状态，**请勿删除**
- ⚠️ 登录状态可能过期，过期后需要重新登录

### 3. 第二步：抓取评价

编辑 `taobao_scraper.py` 文件（318-321行）：

```python
if __name__ == "__main__":
    # 设置商品URL和抓取数量
    ITEM_URL = "你的商品URL"
    TARGET_COUNT = 100  # 想要抓取的评价数量
    
    scrape_taobao_reviews(ITEM_URL, TARGET_COUNT)
```

运行爬虫：

```bash
python taobao_scraper.py
```

---

## 📁 文件详解

### 1. config.py - 配置模块

**作用**：集中管理所有配置参数，方便修改和维护。

**主要配置项**：

```python
class Config:
    # 文件路径
    AUTH_FILE = "auth.json"          # 登录状态文件
    OUTPUT_DIR = "data/"             # 数据输出目录
    LOG_DIR = "logs/"                # 日志目录
    
    # 浏览器设置
    HEADLESS = False                 # False=显示浏览器窗口
    BROWSER_TYPE = "chromium"
    
    # 等待时间（毫秒）
    PAGE_LOAD_WAIT = 2000           # 页面加载等待
    SCROLL_WAIT = 3000              # 滚动后等待
    
    # 滚动参数
    SCROLL_DISTANCE = 1500          # 每次滚动像素
    MAX_RETRIES = 5                 # 最大空滚动次数
    
    # 数据抓取
    DEFAULT_TARGET_COUNT = 100      # 默认抓取数量
    
    # CSS选择器（淘宝改版时需要更新）
    SELECTORS = {
        "review_tab": 'div[class*="tabDetailItemTitle--"]',
        "comment_card": 'div[class^="Comment--"]',
        # ...更多选择器
    }
```

**如何修改配置**：

直接编辑 `config.py` 文件即可，无需修改主程序代码。

---

### 2. taobao_login.py - 登录模块

**作用**：处理淘宝登录，保存登录状态供爬虫使用。

**核心功能**：

```python
def login_and_save():
    """
    1. 启动浏览器
    2. 打开淘宝登录页
    3. 等待用户扫码登录（60秒超时）
    4. 保存登录状态到 auth.json
    """
```

**技术特点**：

- ✅ 使用 Playwright 控制浏览器
- ✅ 通过 URL 跳转检测登录成功
- ✅ 自动保存 cookies 和 session
- ✅ 完善的错误提示

**运行效果**：

```
============================================================
淘宝登录模块启动
============================================================
正在启动 chromium 浏览器...
✓ 页面加载完成

============================================================
📱 请使用手机淘宝APP扫码登录
⏱️  等待登录中...（超时时间：60秒）
============================================================

✓ 登录成功！
✓ 登录状态已保存

============================================================
🎉 登录成功！
📁 登录状态已保存到: auth.json
💡 下次运行爬虫时无需重复登录
============================================================
```

---

### 3. taobao_scraper.py - 爬虫模块

**作用**：使用保存的登录状态，自动抓取商品评价。

**核心类**：`TaobaoScraper`

**主要方法**：

| 方法 | 功能 |
|------|------|
| `__init__()` | 初始化爬虫，验证参数 |
| `_init_browser()` | 启动浏览器，加载登录状态 |
| `_goto_review_page()` | 访问商品页，切换到评价标签 |
| `_expand_folded_reviews()` | 展开折叠的评价 |
| `_extract_reviews()` | 提取当前页面的所有评价 |
| `scrape()` | 主抓取流程 |
| `save_data()` | 保存数据为CSV和JSON |

**抓取流程**：

```
1. 加载登录状态（auth.json）
   ↓
2. 访问商品页面
   ↓
3. 点击"用户评价"标签
   ↓
4. 点击"查看全部评价"
   ↓
5. 循环执行：
   a. 检测并展开折叠的评价
   b. 提取当前可见的所有评价
   c. 数据去重
   d. 滚动页面加载更多
   e. 重复直到达到目标数量
   ↓
6. 保存数据为CSV和JSON
```

**技术亮点**：

```python
# 1. 折叠评价处理
def _expand_folded_reviews(self):
    """淘宝会折叠部分评价，需要主动展开"""
    fold_btn = self.page.locator(Config.SELECTORS['fold_button'])
    if fold_btn.is_visible():
        fold_btn.click()

# 2. 数据去重
uid = f"{user}_{content[:15]}"  # 用户名+评价前15字符
if uid not in self.seen_uids:
    self.seen_uids.add(uid)
    self.final_data.append({...})

# 3. 追评处理
if append_box.count() > 0:
    append_content = append_box.locator(...).inner_text()

# 4. 进度显示
pbar = tqdm(total=self.target_count, desc="抓取进度", unit="条")
pbar.update(batch_count)
```

**运行效果**：

```
============================================================
淘宝评价爬虫启动
============================================================
目标URL: https://detail.tmall.com/item.htm?id=...
目标数量: 50
============================================================
正在启动浏览器...
✓ 浏览器启动成功
正在访问商品页...
✓ 页面加载完成
✓ 已切换到用户评价标签
✓ 已进入全量评价模式

抓取进度: 35/50 [███████░░░] 70% | 0:01:23

>>> 发现折叠区域，正在解锁隐藏评价...

抓取进度: 50/50 [██████████] 100% | 0:01:45

✓ 已达到目标数量 50
🎉 抓取成功！共获得 50 条评价
✓ CSV文件已保存: data/reviews_1234567890.csv
✓ JSON备份已保存: data/reviews_1234567890.json

============================================================
🎉 数据保存成功！
📁 CSV文件: data/reviews_1234567890.csv
📁 JSON文件: data/reviews_1234567890.json
📊 总计: 50 条评价
============================================================
```

---

## 📊 输出数据格式

### CSV/JSON字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| 用户名 | 评价用户昵称 | "t\*\*\*5" |
| 元数据 | 评价日期和购买信息 | "2026年1月3日\n已购：白色 128GB" |
| 初次评价 | 首次评价内容 | "手机很不错，物流快..." |
| 追评内容 | 追加评价（如有） | "用了一周，电池续航很好" |
| 评价日期 | 提取的日期 | "2026年1月3日" |

### 数据示例

```csv
用户名,元数据,初次评价,追评内容,评价日期
t***5,"2026年1月3日\n已购：白色 128GB",手机很不错物流快,用了一周很满意,2026年1月3日
l***8,"2026年1月2日\n已购：黑色 256GB",外观漂亮性能强大,,2026年1月2日
```

---

## ⚙️ 配置说明

### 修改抓取数量

在 `taobao_scraper.py` 中：

```python
TARGET_COUNT = 200  # 改为200条
```

或在 `config.py` 中设置默认值：

```python
DEFAULT_TARGET_COUNT = 200
```

### 修改等待时间

如果网速慢，可以增加等待时间（在 `config.py` 中）：

```python
PAGE_LOAD_WAIT = 3000    # 改为3秒
SCROLL_WAIT = 5000       # 改为5秒
```

### 修改滚动距离

```python
SCROLL_DISTANCE = 2000   # 改为2000像素（滚动更快）
```

### 后台运行（无头模式）

```python
HEADLESS = True   # 不显示浏览器窗口
```

---

## 🔧 工作原理

### 1. 登录状态保存

Playwright 使用 `storage_state` 保存浏览器状态：

```python
# 保存
context.storage_state(path="auth.json")

# 加载
context = browser.new_context(storage_state="auth.json")
```

**auth.json 内容**：
```json
{
  "cookies": [...],
  "origins": [...]
}
```

### 2. 折叠评价问题

淘宝会折叠部分评价，显示"展开折叠评价"按钮。如果不展开，抓取会在43条左右停止。

**解决方案**：
```python
fold_btn = page.locator('div[class*="foldInfoContent--"]')
if fold_btn.is_visible():
    fold_btn.click()  # 展开隐藏评价
```

### 3. 数据去重原理

```python
# 生成唯一标识
uid = f"{user}_{content[:15]}"

# 使用set去重
if uid not in seen_uids:
    seen_uids.add(uid)
    final_data.append({...})
```

**为什么取前15字符**：
- 避免完全相同的评价重复
- 允许不同用户发表相似评价

### 4. 滚动加载机制

```python
# 滚动页面
page.mouse.wheel(0, SCROLL_DISTANCE)

# 等待新内容加载
page.wait_for_timeout(SCROLL_WAIT)

# 检测是否到底
if batch_count == 0:
    retry_count += 1
    if retry_count > MAX_RETRIES:
        break  # 连续5次无新数据，停止
```

---

## ⚠️ 常见问题

### 1. 登录失败

**错误**：`登录超时或失败`

**原因**：
- 没有用淘宝APP扫码（用了支付宝）
- 扫码后没有在手机上确认
- 网络问题

**解决方案**：
- 确保使用淘宝APP
- 扫码后点击手机上的"确认登录"
- 检查网络连接

### 2. 抓取失败

**错误**：`未找到登录状态文件: auth.json`

**解决方案**：
```bash
python taobao_login.py  # 先运行登录
```

### 3. 评价抓不到

**错误**：`未抓取到任何数据`

**可能原因**：
1. 页面弹出验证码
2. 登录状态过期
3. 淘宝改版，CSS选择器失效

**解决方案**：
1. 手动完成验证码
2. 重新运行 `taobao_login.py`
3. 检查并更新 `config.py` 中的 `SELECTORS`

### 4. 抓取数量不足

**问题**：设置100条，只抓到50条

**原因**：商品评价总数少于目标数量

**解决方案**：
- 检查日志 `logs/taobao_scraper.log`
- 查看是否显示"页面已到底"
- 减小 `TARGET_COUNT`

---

## 💡 使用技巧

### 技巧1：分批抓取大量数据

```python
# 第一次抓取100条
scrape_taobao_reviews(ITEM_URL, 100)

# 休息5分钟，避免被检测

# 第二次抓取100条
scrape_taobao_reviews(ITEM_URL, 100)
```

### 技巧2：数据分析

```python
import pandas as pd

# 读取数据
df = pd.read_csv('data/reviews_1234567890.csv')

# 统计
print(f"总评价数: {len(df)}")
print(f"追评比例: {df['追评内容'].notna().sum() / len(df) * 100:.1f}%")

# 评价长度分析
df['评价长度'] = df['初次评价'].str.len()
print(df['评价长度'].describe())
```

### 技巧3：自动化运行

创建 `run_scraper.sh`：

```bash
#!/bin/bash
# 多个商品批量抓取

python3 taobao_scraper.py --url "商品1URL" --count 100
sleep 300  # 休息5分钟

python3 taobao_scraper.py --url "商品2URL" --count 100
sleep 300

python3 taobao_scraper.py --url "商品3URL" --count 100
```

---

## 🎯 适用场景

- 📊 **产品评价分析**：了解用户对产品的真实反馈
- 💬 **用户情感分析**：分析用户满意度
- 🔍 **竞品调研**：研究竞品用户评价
- 📈 **数据分析学习**：练习数据抓取和分析
- 🎓 **学术研究**：电商评价研究

---

## 🔒 法律声明

- ⚠️ 本项目仅供学习研究使用
- ⚠️ 请遵守淘宝/天猫的 robots.txt 和服务条款
- ⚠️ 不要用于商业目的
- ⚠️ 控制抓取频率，避免给服务器造成压力
- ⚠️ 抓取的数据不应公开传播

---

## 📝 技术栈

- **Playwright** - 浏览器自动化框架
- **Pandas** - 数据处理和分析
- **tqdm** - 进度条显示
- **Python 3.7+**

---

## 🎓 项目特点

### 代码质量
- ✅ 模块化设计，职责清晰
- ✅ 面向对象编程（TaobaoScraper类）
- ✅ 详细的注释和文档字符串
- ✅ 完善的错误处理
- ✅ 符合PEP 8规范

### 用户体验
- ✅ 实时进度条显示
- ✅ 详细的日志记录
- ✅ 友好的错误提示
- ✅ 自动创建必要目录

### 数据质量
- ✅ 自动去重
- ✅ 数据验证
- ✅ 双格式保存（CSV + JSON）
- ✅ 时间戳文件名

---

**Happy Crawling! 🎉**
