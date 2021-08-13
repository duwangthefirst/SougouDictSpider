from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import unquote
import re
import os
import random


def get_html_content(url, get_byte=False):
    response = urlopen(url)
    content = response.read()
    if not get_byte:
        content = content.decode(encoding='utf-8')
    return content


def parse_page(html, pattern):
    result = re.findall(pattern, html)
    return result


def parse_l1_category():
    start_url = r'https://shurufa.baidu.com/dict'
    l1_category_pattern = re.compile(r'cid=(\d+).*?category1(.|\n)*?<span>(.*?)</span>')
    category_id_to_name_dict = dict()
    html = get_html_content(start_url)
    result = parse_page(html, l1_category_pattern)
    for item in result:
        category_id_to_name_dict[item[0]] = item[2]
    return category_id_to_name_dict


def parse_l2_and_l3_category(l1_category_id, l1_category_id_list):
    category_base_url = r'https://shurufa.baidu.com/dict_list?cid='
    url = category_base_url + l1_category_id
    l1_category_pattern = re.compile(r'<a\s*href="/dict_list\?cid=(\d+).*?\s*data-stats="webDictListPage.category1">(.*?)\s*</a>')
    l2_category_pattern = re.compile(r'<a\s*href="/dict_list\?cid=(\d+).*?\s*data-stats="webDictListPage.category2">(.*?)\s*</a>')

    def get_l3_category_pattern(cid):
        return re.compile(r'<a\s*href="/dict_list\?cid={}&l3_cid=(\d+)"\s*data-stats="webDictListPage.category3">(.*?)\s*</a>'.format(cid))

    html = get_html_content(url)
    if l1_category_id == "157":
        l2_category_result = parse_page(html, l1_category_pattern)
    else:
        l2_category_result = parse_page(html, l2_category_pattern)
    l2_category_id_dict = dict()
    category_id_to_name_dict = dict()
    for item in l2_category_result:
        if l1_category_id == "157" and item[0] in l1_category_id_list:  # 防止找城市区划下面的子分类的时候将其他的一级分类都找出来
            continue
        category_id_to_name_dict[item[0]] = item[1]
    l2_category_id_list = [i for i in category_id_to_name_dict.keys()]
    for l2_category_id in l2_category_id_list:
        if l1_category_id == "157":
            l2_category_id_dict[l2_category_id] = {}
        else:
            l3_category_pattern = get_l3_category_pattern(l2_category_id)
            l3_category_result = parse_page(html, l3_category_pattern)
            l3_category_id_dict = dict()
            for item in l3_category_result:
                category_id_to_name_dict[item[0]] = item[1]
                l3_category_id_dict[item[0]] = {}
            l2_category_id_dict[l2_category_id] = l3_category_id_dict

    return category_id_to_name_dict, l2_category_id_dict


def get_all_category_id_dict():
    all_category_id_dict = dict()
    l1_category_id_to_name_dict = parse_l1_category()
    all_category_id_to_name_dict = l1_category_id_to_name_dict.copy()
    for l1_category_id, l1_category_name in l1_category_id_to_name_dict.items():
        l2_category_id_to_name_dict, l2_category_id_dict = parse_l2_and_l3_category(l1_category_id, l1_category_id_to_name_dict.keys())
        all_category_id_dict[l1_category_id] = l2_category_id_dict
        all_category_id_to_name_dict.update(l2_category_id_to_name_dict)
    return all_category_id_dict, all_category_id_to_name_dict


def download_dict_of_category(category_id, dir):
    start_url = r'https://shurufa.baidu.com/dict_list?cid={}'.format(category_id)
    file_base_url = r'https://shurufa.baidu.com/dict_innerid_download?innerid='

    page_pattern = re.compile(r'page=(\d+)#page')  # 非贪婪匹配,查找跳转到其他页面的url
    file_pattern = re.compile(r'dict-name="(.*?)" dict-innerid="(\d+)"')

    downloaded = []

    html = get_html_content(start_url)
    page_result = parse_page(html, page_pattern)
    page_result = [int(page) for page in page_result] if page_result else [1, ]
    page_num = max(page_result)
    # print("page_num:{}".format(page_num))
    page_set = set(range(1, page_num+1))
    while page_set:
        current_page = page_set.pop()
        current_url = start_url + '&page={}#page'.format(current_page)
        try:
            html = get_html_content(current_url)
            file_result = parse_page(html, file_pattern)
            for filename, file_id in file_result:
                file_url = file_base_url+file_id
                if file_url in downloaded:
                    print("\t\t\t跳过已经下载的文件：{}".format(file_url))
                    continue
                print("\t\t\t{} {}".format(filename, file_url))
                download_dict_file(file_url, filename, dir)
                downloaded.append(file_url)
        except HTTPError as e:
            if "404" not in str(e):
                # 遇到一个报404的词库：互猎网 https://shurufa.baidu.com/dict_innerid_download?innerid=4206105738
                page_set.add(current_page)
            print(e)
            print("\t\t\t下载失败，重试中。。。")
            continue


def download_all_dict():
    skip_l1_category = True
    skip_l2_category = True
    all_category_id_dict, all_category_id_to_name_dict = get_all_category_id_dict()
    for l1_id in all_category_id_dict.keys():
        print("{} {}".format(l1_id, all_category_id_to_name_dict[l1_id]))
        if l1_id=="159":
            skip_l1_category = False
        for l2_id, l2_value in all_category_id_dict[l1_id].items():
            print("\t{} {}".format(l2_id, all_category_id_to_name_dict[l2_id]))
            if l2_id == "249":
                skip_l2_category = False
            if skip_l1_category or skip_l2_category:
                continue
            if l2_value:
                # 存在三级分类
                for l3_id in all_category_id_dict[l1_id][l2_id].keys():
                    print("\t\t{} {}".format(l3_id, all_category_id_to_name_dict[l3_id]))
                    download_dict_of_category(l3_id, os.path.join("baidu_dict", l1_id, l2_id, l3_id))
            else:
                # 只有二级分类
                download_dict_of_category(l2_id, os.path.join("baidu_dict", l1_id, l2_id))


def download_dict_file(url, filename, dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    data = get_html_content(url, get_byte=True)
    filename = filename.replace("/", "_")
    save_path = os.path.join(dir, filename + '.bdict')
    with open(save_path, 'wb') as f:
        f.write(data)


if __name__ == '__main__':
   download_all_dict()

