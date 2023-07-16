"""jsonstuff

Author: Ethan Hunt
Creation Date: 2023-06-17

"""

import fnmatch
import os
import json


def reformat_json(path: str, file: str = None) -> list:
    # TODO: Make file parameter a list so multiple files can be passed
    """Beautifies a JSON file

    Reformats a JSON/dictionary file from a single line into something more human-readable

    Parameters
    ----------
    path : str
        Directory file(s) will be located in
    file : str, optional (default None)
        Name of file to reformat. Will reformat all files in 'path' if not provided.

    Returns
    -------
    list : The basename(s) of the file(s) reformatted.

    Raises
    ------
    FileNotFoundError
        If 'path' does not exist
        If 'file' is provided but does not exist

    Examples
    --------
    >>> file_list = reformat_json('/my/path')
    >>> print(file_list)
    ['file1_reformat.json', 'file2_reformat.json']

    """
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
