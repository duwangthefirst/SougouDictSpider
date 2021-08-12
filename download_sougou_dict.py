from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import unquote
import re
import os


def get_html_content(url, get_byte=False):
    response = urlopen(url)
    content = response.read()
    if not get_byte:
        content = content.decode(encoding='utf-8')
    return content


def get_all_category_dict():
    all_category_dict = dict()
    for parent_category_id in get_parent_category_dict().keys():
        all_category_dict[parent_category_id] = get_sub_category_dict(parent_category_id)
    return all_category_dict


def get_parent_category_dict():
    base_url = 'http://pinyin.sogou.com/dict/'
    html = get_html_content(base_url)
    # <a href="/dict/cate/index/167?rf=dictindex&amp;pos=dict_rcmd" target="_blank">城市信息大全</a>
    parent_category_pattern = re.compile(r"href='/dict/cate/index/(\d+).*?>(.*?)<")
    result = re.findall(parent_category_pattern, html)
    category_dict = dict()
    for item in result:
        category_dict[item[0]] = item[1]
    return category_dict


def get_sub_category_dict(parent_category_id):
    base_url = 'http://pinyin.sogou.com/dict/cate/index/' + str(parent_category_id)
    html = get_html_content(base_url)

    sub_category_pattern = r'href="/dict/cate/index/(\d+)">(.*?)<'
    result = re.findall(sub_category_pattern, html)
    category_dict = dict()
    for item in result:
        if len(item[1]) == 0:
            continue
        # category_dict["{}_{}".format(parent_category_id, item[0])] = item[1]
        category_dict["{}".format(item[0])] = item[1]
    return category_dict


def download_dict(url, dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    data = get_html_content(url, get_byte=True)
    filename_quote = re.findall('name=(.*)$', url)[0]
    filename = unquote(filename_quote)
    filename = filename.replace('/', '_')
    save_path = os.path.join(dir, filename + '.scel')
    with open(save_path, 'wb') as f:
        f.write(data)


def download_all_dict_of_category(category_id, dir):
    start_url = 'http://pinyin.sogou.com/dict/cate/index/%s' % category_id
    file_base_url = 'http://download.pinyin.sogou.com'

    page_pattern = re.compile(r'href="/dict/cate/index/%s/default(.*?)"' % category_id)
    file_pattern = re.compile(r'href="http://download.pinyin.sogou.com(.*?)"')

    url_to_parse = [start_url, ]
    visited_url_list = []
    downloaded_file_list = []

    while len(url_to_parse) > 0:
        current_url = url_to_parse.pop()
        if current_url in visited_url_list:
            continue
        visited_url_list.append(current_url)
        html = get_html_content(current_url, get_byte=False)

        page_result = re.findall(page_pattern, html)
        for page in page_result:
            new_url = start_url + '/default' + page
            if new_url not in visited_url_list:
                url_to_parse.append(new_url)
        file_result = re.findall(file_pattern, html)
        for file in file_result:
            file_url = file_base_url + file
            if file_url in downloaded_file_list:
                continue
            downloaded_file_list.append(file_url)
            download_dict(file_url, dir)
        print("\t\tnew file num:{}".format(len(file_result)))


def download_all_dict():
    # skip_parent_category = True
    # skip_sub_category = True
    all_category_dict = get_all_category_dict()
    for parent_category_id, sub_category_dict in all_category_dict.items():
        print('download for category:{}'.format(parent_category_id))
        # if parent_category_id=="96":
        #     skip_parent_category = False
        for sub_category_id in sub_category_dict.keys():
            # if sub_category_id=="116":
            #     skip_sub_category = False
            # if skip_parent_category or skip_sub_category:
            #     continue
            print('\tdownload for category:{}'.format(sub_category_id))
            download_all_dict_of_category(sub_category_id, os.path.join('sougou_dict', parent_category_id, sub_category_id))


def test_get_all_category_dict():
    all_category_dict = get_all_category_dict()
    print(all_category_dict)


def test_download_dict():
    url = u"https://pinyin.sogou.com/d/dict/download_cell.php?id=20647&name=%E4%B8%AD%E5%9B%BD%E9%AB%98%E7%AD%89%E9%99%A2%E6%A0%A1%EF%BC%88%E5%A4%A7%E5%AD%A6%EF%BC%89%E5%A4%A7%E5%85%A8%E3%80%90%E5%AE%98%E6%96%B9%E6%8E%A8%E8%8D%90%E3%80%91&f=detail"
    download_dict(url, "sougou_dict")


# 分类列出所有词库
if __name__ == '__main__':
    # test_get_all_category_dict()
    # test_download_dict()
    download_all_dict()
