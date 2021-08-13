### SougouDictSpider
用于下载搜狗输入法全部词库的python脚本，使用方法：
```bash
python3 download_sougou_dict.py
```

注意事项：

**开发环境**

脚本需要在python3下运行，基本都是使用的内置的库，不需要安装额外依赖：
```python
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import unquote
import re
import os
```

**关于本脚本的有效性**

最近一次正常运行的时间是：2021年8月12日
如果搜狗输入法官网页面的跳转逻辑和下载机制发生变化，则可能导致本脚本失效

**关于本脚本的用途**

下载的词库文件将被进一步解析并按照分类结构存入关系型数据库，为作者个人后续【自然语言处理】的学习打下基础

感谢搜狗输入法和百度输入法的开放词库的做法

作者个人对于国内几大输入法提供的词库的评价：
- 搜狗输入法（12个一级分类，8179个文件，454M），词库最大，推荐使用带有"【官方推荐】"字样的词库文件，内容质量比较高
- QQ输入法，词库几乎都是抄的搜狗的（词库文件名字都没改，就改了个格式）
- 百度输入法（9个一级分类，3767个文件，221M）

**关于保存目录**

- 词库默认下载到当前目录下的`sougou_dict`目录，该目录下包含一级分类的子目录
- 一级分类目录下包含二级分类目录
- 二级分类目录下包含当前分类下所有的词库文件

**关于下载中断**

- 如果下载中断（例如，发生HTTPError），需要在文件资源管理器中按照最近修改时间排序查看一级分类和二级分类文件夹结构，找到中断发生时位于的一级分类和二级分类的id
- 然后取消download_all_dict()方法中注释掉的部分，并对应修改if判断条件中的分类id，即可跳过下载之前下载过的词库文件：
```python
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
```