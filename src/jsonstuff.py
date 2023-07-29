"""jsonstuff

Author: Ethan Hunt
Creation Date: 2023-06-17

"""

import fnmatch
import os
import json


def reformat_json(path: str, files: list | str = None) -> list:
    """Beautifies a JSON file

    Reformats a JSON/dictionary file from a single line into something more human-readable

    Parameters
    ----------
    path : str
        Directory file(s) will be located in
    files : list or str, optional (default None)
        Specific file(s) to reformat. Will reformat all files in 'path' if not provided.

    Returns
    -------
    list : The basename(s) of the file(s) reformatted.

    Raises
    ------
    FileNotFoundError
        If 'path' does not exist
        If 'file' is provided but does not exist

    """
    if not os.path.isdir(path):
        raise FileNotFoundError(f'Path {path} does not exist!')

    files = [files] if isinstance(files, str) else files  # convert single files to a list
    files = files if isinstance(files, list) else []  # convert to empty list if not already a list type

    name_append = '_reformat'
    json_list = []
    if len(files) == 0:
        for f in os.listdir(path):
            if fnmatch.fnmatch(f, '*.json') and name_append not in f:
                json_list.append(f)
    else:
        for f in files:
            if os.path.isfile(os.path.join(path, f)):
                json_list.append(f)
            else:
                raise FileNotFoundError(f'File {f} does not exist!')  # perhaps a bit aggresive, but don't be stupid!

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
