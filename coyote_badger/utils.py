import os

from PyPDF2 import PdfFileReader
from PyPDF2 import PdfFileMerger
from PyPDF2 import PdfFileWriter
from PIL import Image
from string import printable
from sanitize_filename import sanitize


def img2pdf(in_path, out_path=None):
    '''Converts an image to a pdf.

    :param in_path: The path to the input image
    :type in_path: str
    :param out_path: The path to the output pdf, defaults to None
    :type out_path: str, optional
    :returns: The path to the output pdf
    :rtype: {str}
    '''
    out_path = out_path or '{}.pdf'.format(os.path.splitext(in_path)[0])
    img = Image.open(in_path).convert('RGB')
    img.save(out_path)
    return out_path


def merge(paths, save_as_path):
    '''Merges multiple PDFs.

    :param paths: The filepaths to merge
    :type paths: [str]
    :param save_as_path: The filename to save the result as
    :type save_as_path: str
    '''
    merger = PdfFileMerger()
    for path in paths:
        merger.append(path)
    merger.write(save_as_path)
    merger.close()


def remove_first_page(path):
    '''Removes the first page of a PDF.

    :param path: The filepath of the PDF
    :type path: str
    '''
    infile = PdfFileReader(path, 'rb')
    output = PdfFileWriter()
    for i in range(1, infile.getNumPages()):
        p = infile.getPage(i)
        output.addPage(p)
    with open(path, 'wb') as f:
        output.write(f)


def clean_string(string):
    '''Cleans a string.

    Removes non-visible characters and extra whitespace from a string.
    :param string: The string
    :type string: str
    :returns: The clean string
    :rtype: {str}
    '''
    new_string = ''.join(char for char in string if char in printable)
    new_string = new_string.strip()
    return new_string


def clean_filename(filename):
    '''Cleans a filename.

    Removes any non-allowed characters from a filename.
    :param filename: The name of the file
    :type filename: str
    :returns: The clean name of the file
    :rtype: {str}
    '''
    new_filename = clean_string(filename)
    if not new_filename:
        return new_filename
    new_filename = sanitize(new_filename)
    return new_filename
