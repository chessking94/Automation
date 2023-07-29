"""office

Author: Ethan Hunt
Creation Date: 2023-06-20

"""

import csv
import datetime as dt
import logging
import os

import pandas as pd
from win32com import client
import xlsxwriter as xl

from .constants import BOOLEANS as BOOLEANS
from .constants import VALID_DELIMS as VALID_DELIMS


class convert():
    """Class to perform common file conversions"""
    def __init__(self):
        pass

    def _guessdelimiter(self, filename: str) -> str:
        """Class function to guess the delimiter in a csv file"""
        with open(filename, mode='r', encoding='utf-8') as f:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(f.readline())
        delim = dialect.delimiter
        logging.debug(f'delim guess|{delim}')
        return delim

    def extract_columns(self, filename: str, columns: list | str | int) -> str:
        """Extract specific columns from a csv file

        Parameters
        ----------
        filename : str
            The full name of the original file
        columns : list, str, or int
            The headers or 0-based positions of the columns to extract

        Returns
        -------
        str : The full name of the output file

        Raises
        ------
        TypeError
            If 'columns' is not a list or contains an element that is not a string or integer
        FileNotFoundError
            If 'filename' does not exist
        FileExistsError
            If file with the same name as the would-be extracted file already exists
        NotImplementedError
            If columns passed are a mix of string names and integer positions
            If the guessed delimiter in the csv file is not in a predefined list

        """
        columns = [columns] if isinstance(columns, str) else columns  # convert single column passed as str to a list
        columns = [columns] if isinstance(columns, int) else columns  # convert single column passed as int to a list
        if not isinstance(columns, list):
            raise TypeError('invalid columns')

        # validate columns
        isstr = False
        isint = False
        for i in columns:
            if isinstance(i, str):
                isstr = True
            else:
                if isinstance(i, int):
                    isint = True
                else:
                    raise TypeError('invalid columns')
        if isstr and isint:
            raise NotImplementedError('mix of string and integer column references')

        if not os.path.isfile(filename):
            raise FileNotFoundError

        output_file = f'{os.path.splitext(filename)[0]}_filtered{os.path.splitext(filename)[1]}'
        if os.path.isfile(output_file):
            raise FileExistsError

        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.csv', '.txt']:
            delim = self._guessdelimiter(filename)
            if delim not in VALID_DELIMS:
                raise NotImplementedError(f"invalid delimiter: {delim}")

            df = pd.read_csv(filename, dtype=str, sep=delim)
            if isstr:
                df_filtered = df[columns]
            else:
                df_filtered = df.iloc[:, columns]
            df_filtered.to_csv(output_file, index=False)
        elif ext in ['.xlsx', '.xls', '.xlsm']:
            df = pd.read_excel(filename, engine='openpyxl')
            if isstr:
                df_filtered = df[columns]
            else:
                df_filtered = df.iloc[:, columns]
            df_filtered.to_excel(output_file, index=False)
        else:
            output_file = None
            logging.critical(f'Other extensions not currently supported|{filename}')

        return output_file

    def change_delimiter(self, filename: str, old_delim: str = None, new_delim: str = None) -> str:
        """Change the delimiter of a csv file

        Parameters
        ----------
        filename : str
            The full name of the original file
        old_delim : str, optional (default None)
            Original delimiter of the csv file. Uses method self._guessdelimiter if not provided
        new_delim : str, optional (default None)
            Delimiter to change into

        Returns
        -------
        str : The full name of the output file

        Raises
        ------
        FileNotFoundError
            If 'filename' does not exist
        FileExistsError
            If file with the same name as the newly-delimited file already exists
        NotImplementedError
            If the guessed delimiter in the csv file is not in a predefined list

        """
        if not os.path.isfile(filename):
            raise FileNotFoundError

        output_file = f'{os.path.splitext(filename)[0]}_delimiter{os.path.splitext(filename)[1]}'
        if os.path.isfile(output_file):
            raise FileExistsError

        if new_delim is None or len(new_delim) == 0:
            raise NotImplementedError(f"invalid delimiter: {new_delim}")

        old_delim = self._guessdelimiter(filename) if old_delim is None else old_delim

        with open(filename, mode='r', newline='\n') as inpfile:
            reader = csv.reader(inpfile, delimiter=old_delim, quotechar='"')
            with open(output_file, mode='w', newline='') as outfile:
                writer = csv.writer(outfile, delimiter=new_delim)
                writer.writerows(reader)

        return output_file

    def csv_to_excel(self, filename: str, delim: str = None) -> str:
        """Convert a csv file into Excel (xlsx)

        Parameters
        ----------
        filename : str
            The full name of the original file
        delim : str, optional (default None)
            Delimiter of the csv file. Uses method self._guessdelimiter if not provided

        Returns
        -------
        str : The full name of the output file

        Raises
        ------
        FileNotFoundError
            If 'filename' does not exist
        NotImplementedError
            If the guessed delimiter in the csv file is not in a predefined list

        Notes
        -----
        All columns of the new Excel file will be formatted as text

        """
        if not os.path.isfile(filename):
            raise FileNotFoundError

        delim = self._guessdelimiter(filename) if delim is None else delim
        if delim not in VALID_DELIMS:
            raise NotImplementedError(f"invalid delimiter: {delim}")

        path = os.path.dirname(filename)
        file = os.path.basename(filename)
        new_file = f'{os.path.splitext(file)[0]}.xlsx'  # always going to xlsx
        output_file = os.path.join(path, new_file)

        if os.path.isfile(output_file):
            logging.warning(f"File '{file}' has already been converted to Excel")
        else:
            df = pd.read_csv(filename, sep=delim)
            wb = xl.Workbook(output_file)
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

        return output_file

    def excel_to_csv(self, filename: str, delim: str = ',') -> str:
        """Convert an Excel file into csv

        Parameters
        ----------
        filename : str
            The full name of the original file
        delim : str, optional (default None)
            Delimiter to use for the csv file

        Returns
        -------
        str : The full name of the output file

        Raises
        ------
        FileNotFoundError
            If 'filename' does not exist
        NotImplementedError
            If 'delim' is not in a predefined list
            If the extension of the Excel file is not in a predefined list

        """
        if not os.path.isfile(filename):
            raise FileNotFoundError

        if delim not in VALID_DELIMS:
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
        output_file = os.path.join(path, new_file)

        if os.path.isfile(os.path.join(path, new_file)):
            logging.warning(f'File {file} has already been converted to csv')
        else:
            df = pd.read_excel(filename, engine='openpyxl')
            df.to_csv(output_file, sep=delim, encoding='utf-8', index=False)

            if os.path.isdir(os.path.join(path, 'Archive')):
                os.rename(filename, os.path.join(path, 'Archive', file))

        return output_file

    def word_to_pdf(self, filename: str) -> str:
        """Convert a Word file into pdf

        Parameters
        ----------
        filename : str
            The full name of the original file

        Returns
        -------
        str : The full name of the output file

        Raises
        ------
        FileNotFoundError
            If 'filename' does not exist
        NotImplementedError
            If the extension of the Word file is not in a predefined list

        """
        if not os.path.isfile(filename):
            raise FileNotFoundError

        valid_ext = ['.docx', '.doc']
        if os.path.splitext(filename)[1] not in valid_ext:
            raise NotImplementedError(f"Extension '{os.path.splitext(filename)[1]}' not supported")

        path = os.path.dirname(filename)
        file = os.path.basename(filename)
        new_file = f'{os.path.splitext(file)[0]}.pdf'
        output_file = os.path.join(path, new_file)

        word = client.Dispatch('Word.Application')  # requires Office to be installed
        if os.path.isfile(output_file):
            os.remove(output_file)
        worddoc = word.Documents.Open(filename, ReadOnly=1)
        worddoc.SaveAs(output_file, FileFormat=17)
        worddoc.Close()

        return output_file


class excel():
    """Class for often-used Excel functionality"""
    def __init__(self):
        pass

    def refresh_file(self, filename: str, save_copy: bool = True) -> str:
        """Refresh all data connections

        Parameters
        ----------
        filename : str
            The full name of the original file
        save_copy : bool, optional (default True)
            Indicator whether to save a new copy of 'filename', with "yyyymmdd HHMM" appended

        Returns
        -------
        str : The full name of the output file

        Raises
        ------
        FileNotFoundError
            If 'filename' does not exist

        TODO
        ----
        Custom naming convention option when save_copy is True
        Way to check if there is any data in a refreshed table?

        """
        save_copy = save_copy if save_copy in BOOLEANS else True

        if not os.path.isfile(filename):
            raise FileNotFoundError

        excel = client.gencache.EnsureDispatch('Excel.Application')
        wb = excel.Workbooks.Open(filename)
        dte = dt.datetime.now().strftime('%Y%m%d %H%M')

        # refresh all data connections, followed by any separate pivot tables
        wb.RefreshAll()
        for sheet in wb.Sheets:
            for pt in sheet.PivotTables():
                if pt.PivotCache().RecordCount == 0:
                    pt.RefreshTable()

        output_file = filename
        if save_copy:
            new_filename = f'{os.path.splitext(filename)[0]} {dte}{os.path.splitext(filename)[1]}'
            wb.SaveAs(new_filename)
            output_file = new_filename
        else:
            wb.Save()

        wb.Close()
        excel.Quit()

        return output_file

    def run_vba(self, filename: str, macro_name: str = None, save_copy: bool = True) -> str:
        """Execute VBA

        Parameters
        ----------
        filename : str
            The full name of the original file
        macro_name : str, optional (default None)
            Name of the macro to run; if provided, will use the name of the first (only) macro in the file
        save_copy : bool, optional (default True)
            Indicator whether to save a new copy of 'filename', with "yyyymmdd HHMM" appended

        Returns
        -------
        str : The full name of the output file

        Raises
        ------
        FileNotFoundError
            If 'filename' does not exist
        NotImplementedError
            If no value was provided for 'macro_name' and the file does not have exactly 1 macro

        TODO
        ----
        Custom naming convention option when save_copy is True
        Way to check if there is any data in a refreshed table?

        """
        save_copy = save_copy if save_copy in BOOLEANS else True

        if not os.path.isfile(filename):
            raise FileNotFoundError

        excel = client.Dispatch('Excel.Application')
        wb = excel.Workbooks.Open(filename)

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

        output_file = filename
        if save_copy:
            dte = dt.datetime.now().strftime('%Y%m%d %H%M')
            new_filename = f'{os.path.splitext(filename)[0]} {dte}{os.path.splitext(filename)[1]}'
            wb.SaveAs(new_filename)
            output_file = new_filename
        else:
            wb.Save()

        wb.Close()
        excel.Quit()

        return output_file
