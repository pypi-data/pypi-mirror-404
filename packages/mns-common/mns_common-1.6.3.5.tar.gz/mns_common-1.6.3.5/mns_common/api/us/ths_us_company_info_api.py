import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import requests
from bs4 import BeautifulSoup

key_mapping = {
    '公司名称': 'company_mame',
    '公司简称': 'company_short_name',
    '英文名称': 'english_name',
    '所属行业': 'industry',
    '上市场所': 'listing_exchange',
    '公司网址': 'official_website',
    '公司总裁': 'ceo',
    '注册地址': 'registered_address',
    '员工人数': 'employee_count',
    '邮政编码': 'zip_code',
    '联系电话': 'phone_number',
    '联系传真': 'fax_number',
    '办公地址': 'office_address',
    '公司简介': 'company_profile',
    '公司LOGO': 'company_logo_url',
    'LOGO备注': 'logo_remark'
}


# 同花顺 美股地址:https://basic.10jqka.com.cn/168/PINS/company.html

# 获取美股公司信息 https://stockpage.10jqka.com.cn/LMT/company/
def get_us_ths_company_info(stock_code):
    """
    根据股票代码，获取同花顺公司基本信息
    :param stock_code: 股票代码，例如 LMT / AAPL 字符串格式，核心传参参数
    :return: dict 结构化的公司基本信息，失败返回空字典
    """
    # 1. 基础配置：参数化拼接URL + 请求头（必须加，否则会被反爬拦截）
    base_url = f"https://stockpage.10jqka.com.cn/{stock_code}/company/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    company_data = {}  # 存储最终的公司信息

    try:
        # 2. 发起GET请求获取网页源码
        response = requests.get(url=base_url, headers=headers, timeout=10)
        response.raise_for_status()  # 抛出请求异常（404/500等）
        response.encoding = "utf-8"  # 指定编码，防止中文乱码

        # 3. 解析HTML网页结构
        soup = BeautifulSoup(response.text, "html.parser")
        # 精准定位目标表格（唯一核心表格）
        table = soup.find("table", class_="companyinfo-tab")
        if not table:
            print(f"错误：未找到 {stock_code} 的公司信息表格")
            return company_data

        # 4. 提取所有表格内的文本内容+清洗数据
        all_tds = table.find_all("td")
        for td in all_tds:
            td_text = td.get_text(strip=True)  # 自动去除首尾空格/换行
            if not td_text:
                continue
            # 按【字段名：字段值】的格式拆分数据，封装到字典
            if "：" in td_text:
                key, value = td_text.split("：", 1)  # 只分割第一个冒号
                if key in key_mapping:
                    company_data[key_mapping[key]] = value

        # 单独提取：公司LOGO图片地址（补充信息，可选）
        logo_img = table.find("img")
        if logo_img:
            company_data[key_mapping['公司LOGO']] = logo_img.get("src", "")
            company_data[key_mapping['LOGO备注']] = logo_img.get("alt", "")

        # 特殊清洗：公司简介 去除多余空格/换行符，格式化展示
        if "公司简介" in company_data:
            company_data[key_mapping['公司简介']] = company_data["公司简介"].replace("\r", "").replace("\n", "").strip()



    except requests.exceptions.RequestException as e:
        print(f"请求失败：{e}")
    except Exception as e:
        print(f"解析数据异常：{e}")

    return company_data


def get_us_ths_company_info_v2(stock_code, market_code):
    """
    根据股票代码，获取同花顺公司基本信息
    :param stock_code: 股票代码，例如 LMT / AAPL 字符串格式，核心传参参数
    :return: dict 结构化的公司基本信息，失败返回空字典
    """
    # 1. 基础配置：参数化拼接URL + 请求头（必须加，否则会被反爬拦截）
    base_url = f"https://basic.10jqka.com.cn/{market_code}/{stock_code}/company.html"
    """
       根据股票代码爬取同花顺公司详情页的完整公司信息
       :param stock_code: 股票代码 如 PINS、LMT、NVDA
       :return: dict 清洗后的英文key结构化公司信息，异常返回空字典
       """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    result = {}

    try:
        res = requests.get(base_url, headers=headers, timeout=15)
        res.raise_for_status()  # 捕获404/500等请求错误

        # ========== 【核心修复1：解决编码乱码的关键代码】 ==========
        res.encoding = res.apparent_encoding  # 自动识别网页真实编码，替代手动指定utf-8

        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', class_='companyinfo-tab')
        if not table:
            print(f"错误：未找到{stock_code}的公司信息表格")
            return result

        # 提取LOGO
        logo_img = table.find('img')
        if logo_img:
            result[key_mapping['公司LOGO']] = clean_text(logo_img.get('src', ''))

        # ========== 【核心修复2：提取所有表格数据+超级清洗+兼容冒号】 ==========
        all_td = table.find_all('td')
        for td in all_td:
            # 提取td内所有文本，先做超级清洗
            td_text = clean_text(td.get_text())
            # 过滤空内容的td
            if not td_text:
                continue
            # 兼容：页面中同时存在【全角冒号 ：】和【半角冒号 :】，统一替换为全角再拆分
            td_text_unify = td_text.replace(":", "：")
            if '：' not in td_text_unify:
                continue
            # 拆分字段名和字段值，只拆分第一个冒号，防止值里有冒号导致拆分失败
            key, value = td_text_unify.split('：', 1)
            key = clean_text(key)
            value = clean_text(value)
            # 映射为英文key并存入
            if key in key_mapping:
                result[key_mapping[key]] = value

    except Exception as e:
        print(f"爬取/解析失败：{str(e)}")

    return result


def clean_text(content):
    """
    超级文本清洗函数 - 根治所有乱码/空白/占位符问题
    :param content: 待清洗的文本内容
    :return: 干净无乱码的纯文本
    """
    if not content:
        return ""
    # 1. 清理所有Unicode不可见空白符+占位符（覆盖所有网页乱码源）
    content = content.replace('\u00a0', '').replace('\xa0', '').replace('\u3000', '')
    content = content.replace('\r', ' ').replace('\n', ' ').replace('\t', '')
    # 2. 把多个连续空格 替换成 单个空格，避免内容中间的冗余空白
    while "  " in content:
        content = content.replace("  ", " ")
    # 3. 去除首尾空格，返回纯净文本
    return content.strip()


# ------------------- 核心调用：参数传参 测试 -------------------
if __name__ == "__main__":
    # 股票代码 作为参数传入函数，满足你的核心要求 ✅
    stock_code_param = "GEV"  # 这里可替换任意股票代码，例如：AAPL、MSFT
    result = get_us_ths_company_info(stock_code_param)

    result1 = get_us_ths_company_info_v2('META', '168')

    # 格式化打印结果
    print(f"===== {stock_code_param} 公司基本信息 =====")
    for k, v in result.items():
        print(f"{k}: {v}")
