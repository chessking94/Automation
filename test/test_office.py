import os
import unittest

import src.office as office

FILE_DIR = os.path.join(os.path.dirname(__file__), 'files', 'office')


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.cvrt = office.convert()
        self.result_file = ''

    def tearDown(self):
        self.result_file = '' if self.result_file is None else self.result_file
        if os.path.isfile(self.result_file):
            os.remove(self.result_file)

    def test_guess_delimiter(self):
        file = 'extractcolumns1.abc'
        filename = os.path.join(FILE_DIR, file)
        self.assertNotEqual(self.cvrt._guessdelimiter(filename), '|')

    def test_extract_columns_invalid_columns(self):
        file = 'extractcolumns2.csv'
        filename = os.path.join(FILE_DIR, file)
        self.assertRaises(TypeError, self.cvrt.extract_columns, filename, {'column1', 'column3'})

    def test_extract_columns_missing_file(self):
        file = 'DNE.csv'
        self.assertRaises(FileNotFoundError, self.cvrt.extract_columns, file, ['A', 'C'])

    def test_extract_columns_already_processed(self):
        file = 'extractcolumns1.csv'
        filename = os.path.join(FILE_DIR, file)
        self.assertRaises(FileExistsError, self.cvrt.extract_columns, filename, ['column1', 'column3'])

    def test_extract_columns_csv(self):
        file = 'extractcolumns2.csv'
        cvrt_file = 'extractcolumns2_filtered.csv'
        filename = os.path.join(FILE_DIR, file)
        cvrt_filename = os.path.join(FILE_DIR, cvrt_file)
        self.result_file = self.cvrt.extract_columns(filename, ['column1', 'column3'])
        self.assertEqual(self.result_file, cvrt_filename)

    def test_extract_columns_excel(self):
        file = 'extractcolumns1.xlsx'
        cvrt_file = 'extractcolumns1_filtered.xlsx'
        filename = os.path.join(FILE_DIR, file)
        cvrt_filename = os.path.join(FILE_DIR, cvrt_file)
        self.result_file = self.cvrt.extract_columns(filename, ['column1', 'column3'])
        self.assertEqual(self.result_file, cvrt_filename)

    def test_extract_columns_notimplemented(self):
        file = 'extractcolumns1.abc'
        filename = os.path.join(FILE_DIR, file)
        self.result_file = self.cvrt.extract_columns(filename, ['column1', 'column3'])
        self.assertIsNone(self.result_file)

    def test_change_delimiter_missing_file(self):
        file = 'DNE.csv'
        self.assertRaises(FileNotFoundError, self.cvrt.change_delimiter, file, ',', '\t')

    def test_change_delimiter_already_processed(self):
        file = 'changedelimiter1.csv'
        filename = os.path.join(FILE_DIR, file)
        self.assertRaises(FileExistsError, self.cvrt.change_delimiter, filename, ',', '\t')

    def test_change_delimiter(self):
        file = 'changedelimiter2.csv'
        cvrt_file = 'changedelimiter2_delimiter.csv'
        filename = os.path.join(FILE_DIR, file)
        cvrt_filename = os.path.join(FILE_DIR, cvrt_file)
        self.result_file = self.cvrt.change_delimiter(filename, ',', '\t')
        self.assertEqual(self.result_file, cvrt_filename)

    def test_csv_to_excel_missing_file(self):
        file = 'DNE.csv'
        self.assertRaises(FileNotFoundError, self.cvrt.csv_to_excel, file, ',')

    def test_csv_to_excel(self):
        file = 'csvexcel.csv'
        cvrt_file = 'csvexcel.xlsx'
        filename = os.path.join(FILE_DIR, file)
        cvrt_filename = os.path.join(FILE_DIR, cvrt_file)
        self.result_file = self.cvrt.csv_to_excel(filename, ',')
        self.assertEqual(self.result_file, cvrt_filename)

    def test_excel_to_csv_missing_file(self):
        file = 'DNE.xlsx'
        self.assertRaises(FileNotFoundError, self.cvrt.excel_to_csv, file, ',')

    def test_excel_to_csv_invalid_extension(self):
        file = 'excelcsv.xlsb'
        filename = os.path.join(FILE_DIR, file)
        self.assertRaises(NotImplementedError, self.cvrt.excel_to_csv, filename, ',')

    def test_excel_to_csv(self):
        file = 'excelcsv.xlsx'
        cvrt_file = 'excelcsv.txt'
        filename = os.path.join(FILE_DIR, file)
        cvrt_filename = os.path.join(FILE_DIR, cvrt_file)
        self.result_file = self.cvrt.excel_to_csv(filename, '\t')
        self.assertEqual(self.result_file, cvrt_filename)

    def test_word_to_pdf_missing_file(self):
        file = 'DNE.docx'
        self.assertRaises(FileNotFoundError, self.cvrt.word_to_pdf, file)

    def test_word_to_pdf_invalid_extension(self):
        file = 'wordpdf.csv'
        filename = os.path.join(FILE_DIR, file)
        self.assertRaises(NotImplementedError, self.cvrt.word_to_pdf, filename)

    def test_word_to_pdf(self):
        file = 'wordpdf.docx'
        cvrt_file = 'wordpdf.pdf'
        filename = os.path.join(FILE_DIR, file)
        cvrt_filename = os.path.join(FILE_DIR, cvrt_file)
        self.result_file = self.cvrt.word_to_pdf(filename)
        self.assertEqual(self.result_file, cvrt_filename)


# class TestExcel(unittest.TestCase):
#     def setUp(self):
#         self.cvrt = office.excel()
#         self.result_file = ''

#     def tearDown(self):
#         self.result_file = '' if self.result_file is None else self.result_file
#         if os.path.isfile(self.result_file):
#             os.remove(self.result_file)


if __name__ == '__main__':
    unittest.main()
