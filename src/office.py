"""office

Author: Ethan Hunt
Date: 2023-06-20
Version: 1.0

"""

import datetime as dt
import logging
import os

import pandas as pd
from win32com import client
import xlsxwriter as xl

from .constants import BOOLEANS as BOOLEANS


class convert():
    def __init__(self):
        pass

    def extract_columns(self, filename: str, columns: list):
        if not os.path.isfile(filename):
            raise FileNotFoundError

        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.csv', '.txt']:
            output_file = f'{os.path.splitext(filename)[0]}_filtered{os.path.splitext(filename)[1]}'
            if os.path.isfile(output_file):
                raise FileExistsError

            df = pd.read_csv(filename, dtype=str)
            df_filtered = df[columns]
            df_filtered.to_csv(output_file, index=False)
        elif ext in ['.xlsx', '.xls']:
            logging.warning(f'Excel conversion not yet developed|{filename}')
        else:
            logging.critical(f'Other extensions not currently supported|{filename}')

    def csv_to_excel(self, filename: str, delim: str = None):
        if not os.path.isfile(filename):
            raise FileNotFoundError

        valid_delim = [',', '\t', '|']
        if delim is not None and delim not in valid_delim:
            raise NotImplementedError(f"invalid delimiter: {delim}")

        path = os.path.dirname(filename)
        file = os.path.basename(filename)
        new_file = f'{os.path.splitext(file)[0]}.xlsx'  # always going to xlsx

        if os.path.isfile(os.path.join(path, new_file)):
            logging.warning(f'File {file} has already been converted to Excel')
        else:
            df = pd.read_csv(filename)
            wb = xl.Workbook(os.path.join(path, new_file))
            ws = wb.add_worksheet()
            text_format = wb.add_format({'num_format': '@'})
            for i, column in enumerate(df.columns):
                ws.set_column(i, i, None, text_format)
                ws.write(0, i, column)
                for j, value in enumerate(df[column]):
                    ws.write(j + 1, i, str(value))
            wb.close()

            if os.path.isdir(os.path.join(path, 'Archive')):
                os.rename(filename, os.path.join(path, 'Archive', file))

    def word_to_pdf(self, filename):
        if not os.path.isfile(filename):
            raise FileNotFoundError

        valid_ext = ['.docx', '.doc']
        if os.path.splitext(filename)[1] not in valid_ext:
            raise NotImplementedError(f"Extension '{os.path.splitext(filename)[1]}' not supported")

        path = os.path.dirname(filename)
        file = os.path.basename(filename)
        new_file = f'{os.path.splitext(file)[0]}.pdf'

        word = client.Dispatch('Word.Application')  # requires Office to be installed
        if os.path.exists(new_file):
            os.remove(new_file)
        worddoc = word.Documents.Open(filename, ReadOnly=1)
        worddoc.SaveAs(os.path.join(path, new_file), FileFormat=17)
        worddoc.Close()

    def excel_to_csv(self, filename: str, delim: str = ','):
        if not os.path.isfile(filename):
            raise FileNotFoundError

        valid_delim = [',', '\t', '|']
        if delim not in valid_delim:
            raise NotImplementedError(f"Delimiter '{delim}' not supported")

        valid_ext = ['.xlsx', '.xls', '.xlsm']
        if os.path.splitext(filename)[1] not in valid_ext:
            raise NotImplementedError(f"Extension '{os.path.splitext(filename)[1]}' not supported")

        ext = '.txt'
        if delim == ',':
            ext = '.csv'

        path = os.path.dirname(filename)
        file = os.path.basename(filename)
        new_file = os.path.splitext(file)[0] + ext

        if os.path.isfile(os.path.join(path, new_file)):
            logging.warning(f'File {file} has already been converted to csv')
        else:
            df = pd.read_excel(filename, engine='openpyxl')
            df.to_csv(os.path.join(path, new_file), sep=delim, encoding='utf-8', index=False)

            if os.path.isdir(os.path.join(path, 'Archive')):
                os.rename(filename, os.path.join(path, 'Archive', file))


class excel():
    def __init__(self):
        pass

    def refresh_file(self, filename: str, save_copy: bool = True):
        save_copy = save_copy if save_copy in BOOLEANS else True

        excel = client.gencache.EnsureDispatch('Excel.Application')
        wb = excel.Workbooks.Open(filename)

        # refresh all data connections, followed by any separate pivot tables
        wb.RefreshAll()
        for sheet in wb.Sheets:
            for pt in sheet.PivotTables():
                if pt.PivotCache().RecordCount == 0:
                    pt.RefreshTable()

        if save_copy:
            dte = dt.datetime.now().strftime('%Y%m%d %H%M')
            new_filename = f'{os.path.splitext(filename)[0]} {dte}{os.path.splitext(filename)[1]}'
            wb.SaveAs(new_filename)
        else:
            wb.Save()

        wb.Close()
        excel.Quit()

    def run_vba(self, filename: str, macro_name: str = None, save_copy: bool = True):
        save_copy = save_copy if save_copy in BOOLEANS else True

        excel = client.Dispatch('Excel.Application')
        wb = excel.Workbooks.Open(filename)

        # run the macro if provided, otherwise run the first (only) macro in the file
        if macro_name is None:
            try:
                macro_ct = wb.VBProject.VBCompenents.Count
            except AttributeError:
                macro_ct = 0
            if macro_ct == 1:
                macro = wb.VBProject.VBComponents(1)
                excel.Run(macro.Name)
            else:
                raise NotImplementedError(f"No macro_name provided, multiple or no macros in file '{filename}'")
        else:
            excel.Application.Run(macro_name)

        if save_copy:
            dte = dt.datetime.now().strftime('%Y%m%d %H%M')
            new_filename = f'{os.path.splitext(filename)[0]} {dte}{os.path.splitext(filename)[1]}'
            wb.SaveAs(new_filename)
        else:
            wb.Save()

        wb.Close()
        excel.Quit()
