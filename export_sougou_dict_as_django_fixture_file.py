import download_sougou_dict
import parse_sougou_dict
import os


def get_category(id, name, parent_category_id):
    return {
        "model": "dict_manager.category",
        "fields": {
            "id": id,
            "name": name,
            "parent_category_id": parent_category_id
        }
    }


def get_word(id, name, category_id):
    return {
        "model": "dict_manager.word",
        "fields": {
            "id": id,
            "name": name,
            "category_id": category_id
        }
    }

def export_category_list_to_json():
    dict_dir = "./sougou_dict"
    all_category_id_to_name_dict = download_sougou_dict.get_all_category_id_to_name_dict()

    category_id_counter = 1
    category_list = []

    root_category_id = category_id_counter
    category_list.append(get_category(category_id_counter, "搜狗输入法词库", None))
    category_id_counter += 1

    scel_file_path_to_category_id_dict = dict()

    for parent_category_id in os.listdir(dict_dir):
        if parent_category_id == ".DS_Store":
            continue
        print(all_category_id_to_name_dict[parent_category_id])
        parent_django_id = category_id_counter
        category_list.append(get_category(parent_django_id, all_category_id_to_name_dict[parent_category_id], root_category_id))
        category_id_counter += 1
        for sub_category_id in os.listdir(os.path.join(dict_dir, parent_category_id)):
            if sub_category_id == ".DS_Store":
                continue
            print("\t" + all_category_id_to_name_dict[sub_category_id])
            sub_django_id = category_id_counter
            category_list.append(get_category(sub_django_id, all_category_id_to_name_dict[sub_category_id], parent_django_id))
            category_id_counter += 1
            for scel_file in os.listdir(os.path.join(dict_dir, parent_category_id, sub_category_id)):
                if not scel_file.endswith(".scel"):
                    continue
                if "【官方推荐】" not in scel_file:
                    continue
                filename = scel_file.replace(".scel", "")
                print("\t\t" + filename)
                scel_django_id = category_id_counter
                category_list.append(get_category(scel_django_id, filename, sub_django_id))
                scel_file_path_to_category_id_dict[os.path.join(dict_dir, parent_category_id, sub_category_id, scel_file)] = scel_django_id
                category_id_counter += 1
    # print(category_list)
    import json
    with open("category_list.json", "w", encoding='utf-8') as f:
        json.dump(category_list, f, ensure_ascii=False)
    return scel_file_path_to_category_id_dict


def export_word_list_to_json():
    word_id_counter = 1
    word_list = []
    scel_file_path_to_category_id_dict = export_category_list_to_json()
    for scel_file_path, category_id in scel_file_path_to_category_id_dict.items():
        print("parsing:{}".format(scel_file_path))
        for word in parse_sougou_dict.parse_scel_file(scel_file_path):
            word_list.append(get_word(word_id_counter, word, category_id))
            word_id_counter += 1
    import json
    with open("word_list.json", "w", encoding='utf-8') as f:
        json.dump(word_list, f, ensure_ascii=False)


if __name__ == '__main__':
    export_word_list_to_json()
