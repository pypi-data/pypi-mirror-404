import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import requests
from bs4 import BeautifulSoup
from loguru import logger
import mns_common.component.cookie.cookie_info_service as cookie_info_service


# 获取公司热点
def get_ths_web_zt_reason_info(symbol, ths_cookie):
    try:

        url = "https://basic.10jqka.com.cn/new/" + symbol + "/"

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "cookie": ths_cookie
        }
        cookies = {
            "searchGuide": "sg",
            "skin_color": "white",
            "Hm_lvt_722143063e4892925903024537075d0d": "1725031809,1725842892,1726621825,1727227162",
            "Hm_lvt_929f8b362150b1f77b477230541dbbc2": "1725031809,1725842892,1726621825,1727227162",
            "spversion": "20130314",
            "user": "MDq%2BsNDQcE06Ok5vbmU6NTAwOjYxMzk4NTQ0ODo1LDEsMjA7NiwxLDIwOzcsMTExMTExMTExMTEwLDIwOzgsMTExMTAxMTEwMDAwMTExMTEwMDEwMDEwMDEwMDAwMDAsMjA7MzMsMDAwMTAwMDAwMDAwLDIwOzM2LDEwMDExMTExMDAwMDExMDAxMDExMTExMSwyMDs0NiwwMDAwMTExMTEwMDAwMDExMTExMTExMTEsMjA7NTEsMTEwMDAwMDAwMDAwMDAwMCwyMDs1OCwwMDAwMDAwMDAwMDAwMDAwMSwyMDs3OCwxLDIwOzg3LDAwMDAwMDAwMDAwMDAwMDAwMDAxMDAwMCwyMDsxMTksMDAwMDAwMDAwMDAwMDAwMDAwMTAxMDAwMDAsMjA7MTI1LDExLDIwOzQ0LDExLDQwOzEsMTAxLDQwOzIsMSw0MDszLDEsNDA7MTAyLDEsNDA6Mjc6Ojo2MDM5ODU0NDg6MTcyODQ4NzEyNjo6OjE2MzQ1NjY5ODA6NjA0ODAwOjA6MTRhZjIxYmRiNTgzODUxOTgxZWVjZGQ4NjQxZjA2NDg5OmRlZmF1bHRfNDox",
            "userid": "603985448",
            "u_name": "%BE%B0%D0%D0pM",
            "escapename": "%25u666f%25u884cpM",
            "ticket": "955f0ee44d86aede75787f64ae45bae9",
            "user_status": "0",
            "utk": "2df15e757efe7d4a489cf764fa371ff9",
            "Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1": "1728463065,1728526291,1728541890,1728550124",
            "historystock": "301551%7C*%7C002205%7C*%7C000627%7C*%7C300746%7C*%7C300139",
            "reviewJump": "nojump",
            "usersurvey": "1",
            "v": "A8mumxxpynGwb7YF90Bxvvav2P4mFrxUJwzh32s-RzXtX-dgs2bNGLda8aj4"
        }
        response = requests.get(url, headers=headers, cookies=cookies)
        soup = BeautifulSoup(response.content, "html.parser")
        for a in soup.find_all("a", class_="check_details f12"):
            if "涨停分析" in a.get_text():
                # 找到其后的兄弟节点中 class 为 check_else 的 div，包含详细内容
                parent = a.find_parent("span", class_="performance_trailer")
                if parent:
                    detail_div = parent.find("div", class_="check_else")
                    if detail_div:
                        # 提取div内的完整原始HTML字符串
                        raw_html = detail_div.decode_contents()
                        # 按<br/>切割，精准拆分 涨停原因 + 涨停分析
                        if '<br/>' in raw_html:
                            zt_reason, zt_analysis = raw_html.split('<br/>', 1)  # 只切割1次，核心！
                            # 清洗文本：去除首尾空格/换行，纯文本提取
                            zt_reason = zt_reason.strip()
                            zt_analysis = zt_analysis.strip()
                        else:
                            # 容错：没有br标签的情况，全部给分析
                            zt_reason = ""
                            zt_analysis = detail_div.get_text(strip=True)
            else:
                result_dict = {
                    'zt_reason': '',
                    'zt_analysis': '',
                }
                logger.error("无涨停原因和分析:{}", symbol)
                return result_dict

        result_dict = {
            'zt_reason': zt_reason,
            'zt_analysis': zt_analysis,
        }
        return result_dict
    except BaseException as e:
        logger.error("获取公司涨停信息异常:{},{}", symbol, e)
        result_dict = {
            'zt_reason': '',
            'zt_analysis': '',
        }
        return result_dict


if __name__ == '__main__':
    get_ths_web_zt_reason_info('920021', cookie_info_service.get_ths_cookie())
