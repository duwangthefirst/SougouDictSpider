############################################################################
# 搜狗的scel词库就是保存的文本的unicode编码，每两个字节一个字符（中文汉字或者英文字母）
# 找出其每部分的偏移位置即可
# 主要两部分
# 1.全局拼音表，貌似是所有的拼音组合，字典序
#       格式为(index,len,pinyin)的列表
#       index: 两个字节的整数 代表这个拼音的索引
#       len: 两个字节的整数 拼音的字节长度
#       pinyin: 当前的拼音，每个字符两个字节，总长len
#
# 2.汉语词组表
#       格式为(same,py_table_len,py_table,{word_len,word,ext_len,ext})的一个列表
#       same: 两个字节 整数 同音词数量
#       py_table_len:  两个字节 整数
#       py_table: 整数列表，每个整数两个字节,每个整数代表一个拼音的索引
#
#       word_len:两个字节 整数 代表中文词组字节数长度
#       word: 中文词组,每个中文汉字两个字节，总长度word_len
#       ext_len: 两个字节 整数 代表扩展信息的长度，好像都是10
#       ext: 扩展信息 前两个字节是一个整数(不知道是不是词频) 后八个字节全是0
#
#      {word_len,word,ext_len,ext} 一共重复same次 同音词 相同拼音表
#############################################################################
import struct
import os

# 拼音表偏移
startPy = 0x1540

# 汉语词组表偏移
startChinese = 0x2628


def byte2str(data):
    """
    原始字节码转为字符串
    """
    pos = 0
    str = ''
    while pos < len(data):
        c = chr(struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0])
        if c != chr(0):
            str += c
        pos += 2
    return str


def getPyTable(data, GPy_Table):
    """
    获取拼音表
    """
    data = data[4:]
    pos = 0
    while pos < len(data):
        index = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]
        pos += 2
        lenPy = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]
        pos += 2
        py = byte2str(data[pos:pos + lenPy])

        GPy_Table[index] = py
        pos += lenPy


def getWordPy(data, GPy_Table):
    """
    获取一个词组的拼音
    """
    pos = 0
    ret = ''
    while pos < len(data):
        index = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]
        # print(GPy_Table[index])
        ret += "'" + GPy_Table[index]
        pos += 2
    return ret


def getChinese(data, GPy_Table, GTable):
    """
    读取中文表
    """
    pos = 0
    while pos < len(data):
        # 同音词数量
        same = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]

        # 拼音索引表长度
        pos += 2
        py_table_len = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]

        # print("py_table_len:{}".format(py_table_len))

        # 拼音索引表
        pos += 2
        py = getWordPy(data[pos: pos + py_table_len], GPy_Table)

        # 中文词组
        pos += py_table_len
        for i in range(same):
            # 中文词组长度
            c_len = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]
            # 中文词组
            pos += 2
            word = byte2str(data[pos: pos + c_len])
            # 扩展数据长度
            pos += c_len
            ext_len = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]
            # 词频
            pos += 2
            count = struct.unpack('H', bytes([data[pos], data[pos + 1]]))[0]
            # 保存
            GTable.append((count, py, word))
            # 到下个词的偏移位置
            pos += ext_len


def scel2txt(file_name):
    """
    转换scel为txt
    """

    # 全局拼音表
    GPy_Table = {}

    # 解析结果
    # 元组(词频,拼音,中文词组)的列表
    GTable = []

    print('-' * 60)
    with open(file_name, 'rb') as f:
        data = f.read()

    print("词库名：", byte2str(data[0x130:0x338]))  # .encode('GB18030')
    print("词库类型：", byte2str(data[0x338:0x540]))
    print("描述信息：", byte2str(data[0x540:0xd40]))
    print("词库示例：", byte2str(data[0xd40:startPy]))

    getPyTable(data[startPy:startChinese], GPy_Table)
    print(GPy_Table)

    getChinese(data[startChinese:], GPy_Table, GTable)
    return GTable


def parse_scel_file(scel_path):
    try:
        table = scel2txt(scel_path)
    except Exception as e:
        print("解析出错：{}".format(scel_path))
        return []
    return [word for _, _, word in table]


if __name__ == '__main__':
    for word in parse_scel_file("./sougou_dict/167/198/珠海地域名称.scel"):
        print(word)
