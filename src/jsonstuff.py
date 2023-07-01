"""jsonstuff

Author: Ethan Hunt
Date: 2023-06-17
Version: 1.0

"""

import fnmatch
import os
import json


def reformat_json(path: str, file: str = None) -> list:
    if not os.path.isdir(path):
        raise FileNotFoundError(f'Path {path} does not exist!')

    name_append = '_reformat'
    json_list = []
    if file is None:
        for f in os.listdir(path):
            if fnmatch.fnmatch(f, '*.json') and name_append not in f:
                json_list.append(f)
    else:
        if os.path.isfile(os.path.join(path, file)):
            json_list.append(file)
        else:
            raise FileNotFoundError(f'File {file} does not exist!')

    file_list = []
    for json_orig in json_list:
        json_reformat = f'{os.path.splitext(json_orig)[0]}{name_append}.json'
        orig_file = os.path.join(path, json_orig)
        reformat_file = os.path.join(path, json_reformat)

        if not os.path.isfile(reformat_file):
            with open(file=orig_file, mode='r', encoding='utf-8') as f:
                json_data = json.load(f)
                with open(file=reformat_file, mode='w', encoding='utf-8') as wf:
                    json.dump(json_data, wf, indent=4)
                    file_list.append(reformat_file)

    return file_list
