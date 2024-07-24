"""
Manipulate or transform data in various ways.

The functions and classes of this module take data objects and perform various operations,
including compression and conversion.
"""

import copy
import importlib.resources
import io
import os
import pathlib
import platform
import subprocess
import tempfile
import zipfile

from .._cache import (_check_dependency, _check_file_pathname, _check_rel_pathname,
                      _print_failure_msg)


# ==================================================================================================
# Uncompress data
# ==================================================================================================

def unzip(path_to_zip_file, out_dir=None, verbose=False, **kwargs):
    """
    Extract data from a `Zip
    <https://support.microsoft.com/en-gb/help/14200/windows-compress-uncompress-zip-files>`_
    (compressed) file.

    :param path_to_zip_file: The path where the Zip file is saved.
    :type path_to_zip_file: str | os.PathLike
    :param out_dir: The directory where the extracted data will be saved; defaults to ``None``.
    :type out_dir: str | None
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] Additional parameters for the method `zipfile.ZipFile.extractall()`_.

    .. _`zipfile.ZipFile.extractall()`:
        https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile.extractall

    **Examples**::

        >>> from pyhelpers.store import unzip
        >>> from pyhelpers.dirs import cd, delete_dir
        >>> zip_file_path = cd("tests\\data", "zipped.zip")
        >>> unzip(path_to_zip_file=zip_file_path, verbose=True)
        Extracting "tests\\data\\zipped.zip" to "tests\\data\\zipped\\" ... Done.
        >>> out_file_pathname = cd("tests\\data\\zipped", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test
        >>> output_dir = cd("tests\\data\\zipped_alt")
        >>> unzip(path_to_zip_file=zip_file_path, out_dir=output_dir, verbose=True)
        Extracting "tests\\data\\zipped.zip" to "tests\\data\\zipped_alt\\" ... Done.
        >>> out_file_pathname = cd("tests\\data\\zipped_alt", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test
        >>> # Delete the directories "tests\\data\\zipped\\" and "tests\\data\\zipped_alt\\"
        >>> delete_dir([cd("tests\\data\\zipped"), output_dir], verbose=True)
        To delete the following directories:
            "tests\\data\\zipped\\" (Not empty)
            "tests\\data\\zipped_alt\\" (Not empty)
        ? [No]|Yes: yes
        Deleting "tests\\data\\zipped\\" ... Done.
        Deleting "tests\\data\\zipped_alt\\" ... Done.
    """

    if out_dir is None:
        out_dir = os.path.splitext(path_to_zip_file)[0]

    if not os.path.exists(out_dir):
        os.makedirs(name=out_dir)

    if verbose:
        rel_path = os.path.relpath(path=path_to_zip_file)
        out_dir_ = os.path.relpath(path=out_dir) + ("\\" if not out_dir.endswith("\\") else "")
        print("Extracting \"{}\" to \"{}\"".format(rel_path, out_dir_), end=" ... ")

    try:
        with zipfile.ZipFile(file=path_to_zip_file) as zf:
            zf.extractall(path=out_dir, **kwargs)

        if verbose:
            print("Done.")

    except Exception as e:
        _print_failure_msg(e=e, msg="Failed.")


def seven_zip(path_to_zip_file, out_dir=None, mode='aoa', verbose=False, seven_zip_exe=None,
              **kwargs):
    """
    Extract data from a compressed file using `7-Zip <https://www.7-zip.org/>`_.

    :param path_to_zip_file: The path where the compressed file is saved.
    :type path_to_zip_file: str | os.PathLike
    :param out_dir: The directory where the extracted data will be saved; defaults to ``None``.
    :type out_dir: str | None
    :param mode: The extraction mode; defaults to ``'aoa'``.
    :type mode: str
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param seven_zip_exe: The path to the executable "*7z.exe*";
        If ``seven_zip_exe=None`` (default), the default installation path will be used, e.g.
        "*C:\\\\Program Files\\\\7-Zip\\\\7z.exe*" (on Windows).
    :type seven_zip_exe: str | None
    :param kwargs: [Optional] Additional parameters for the function `subprocess.run()`_.

    .. _`subprocess.run()`: https://docs.python.org/3/library/subprocess.html#subprocess.run

    **Examples**::

        >>> from pyhelpers.store import seven_zip
        >>> from pyhelpers.dirs import cd, delete_dir
        >>> zip_file_pathname = cd("tests\\data", "zipped.zip")
        >>> seven_zip(path_to_zip_file=zip_file_pathname, verbose=True)
        7-Zip 20.00 alpha (x64) : Copyright (c) 1999-2020 Igor Pavlov : 2020-02-06

        Scanning the drive for archives:
        1 file, 158 bytes (1 KiB)

        Extracting archive: \\tests\\data\\zipped.zip
        --
        Path = \\tests\\data\\zipped.zip
        Type = zip
        Physical Size = 158

        Everything is Ok

        Size:       4
        Compressed: 158

        Done.

        >>> out_file_pathname = cd("tests\\data\\zipped", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test
        >>> output_dir = cd("tests\\data\\zipped_alt")
        >>> seven_zip(path_to_zip_file=zip_file_pathname, out_dir=output_dir, verbose=False)
        >>> out_file_pathname = cd("tests\\data\\zipped_alt", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test
        >>> # Extract a .7z file
        >>> zip_file_path = cd("tests\\data", "zipped.7z")
        >>> seven_zip(path_to_zip_file=zip_file_path, out_dir=output_dir)
        >>> out_file_pathname = cd("tests\\data\\zipped", "zipped.txt")
        >>> with open(out_file_pathname) as f:
        ...     print(f.read())
        test
        >>> # Delete the directories "tests\\data\\zipped\\" and "tests\\data\\zipped_alt\\"
        >>> delete_dir([cd("tests\\data\\zipped"), output_dir], verbose=True)
        To delete the following directories:
            "tests\\data\\zipped\\" (Not empty)
            "tests\\data\\zipped_alt\\" (Not empty)
        ? [No]|Yes: yes
        Deleting "tests\\data\\zipped\\" ... Done.
        Deleting "tests\\data\\zipped_alt\\" ... Done.
    """

    exe_name = "7z.exe"
    optional_pathnames = {exe_name, f"C:/Program Files/7-Zip/{exe_name}"}
    seven_zip_exists, seven_zip_exe_ = _check_file_pathname(
        name=exe_name, options=optional_pathnames, target=seven_zip_exe)

    if seven_zip_exists:
        if out_dir is None:
            out_dir = os.path.splitext(path_to_zip_file)[0]

        try:
            # subprocess.run(
            #     '"{}" x "{}" -o"{}" -{}'.format(seven_zip_exe_, path_to_zip_file, out_dir, mode),
            #     **kwargs)
            command_args = [seven_zip_exe_, 'x', path_to_zip_file, '-o' + out_dir, '-' + mode]
            if not verbose:
                command_args += ['-bso0', '-bsp0']

            rslt = subprocess.run(command_args, **kwargs)

            if verbose:
                print("\nDone." if rslt.returncode == 0 else "\nFailed.")

        except Exception as e:
            if verbose:
                print("An error occurred: {}.".format(e))

    else:
        print('"7-Zip" (https://www.7-zip.org/) is required to run this function; '
              'however, it is not found on this device.\nInstall it and then try again.')


# ==================================================================================================
# Convert data
# ==================================================================================================

def markdown_to_rst(path_to_md, path_to_rst, reverse=False, engine=None, pandoc_exe=None,
                    verbose=False, **kwargs):
    """
    Convert a `Markdown <https://daringfireball.net/projects/markdown/>`_ (.md) file to a
    `reStructuredText <https://docutils.readthedocs.io/en/sphinx-docs/user/rst/quickstart.html>`_
    (.rst) file.

    This function relies on `Pandoc <https://pandoc.org/>`_ or
    `pypandoc <https://github.com/bebraw/pypandoc>`_, given the specified ``engine``.

    :param path_to_md: The path where the Markdown file is saved.
    :type path_to_md: str | os.PathLike
    :param path_to_rst: The path where the reStructuredText file will be saved.
    :type path_to_rst: str | os.PathLike
    :param reverse: Specifies whether to convert an .rst file to a .md file; defaults to ``False``.
    :type reverse: bool
    :param engine: The engine/module used for performing the conversion;
        if ``engine=None`` (default), the function utilises `Pandoc <https://pandoc.org/>`_,
        ``'pypandoc'`` otherwise.
    :type engine: None | str
    :param pandoc_exe: The path to the executable "*pandoc.exe*";
        If ``pandoc_exe=None`` (default), the default installation path will be used, e.g.
        "*C:\\\\Program Files\\\\Pandoc\\\\pandoc.exe*" (on Windows).
    :type pandoc_exe: str | None
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] Additional parameters for the function `subprocess.run()`_
        (if ``engine=None``) or `pypandoc.convert_file()`_ (if ``engine='pypandoc'``).

    .. _`subprocess.run()`: https://docs.python.org/3/library/subprocess.html#subprocess.run
    .. _`pypandoc.convert_file()`: https://github.com/NicklasTegner/pypandoc#usage

    **Examples**::

        >>> from pyhelpers.store import markdown_to_rst
        >>> from pyhelpers.dirs import cd
        >>> dat_dir = cd("tests\\documents")
        >>> path_to_md_file = cd(dat_dir, "readme.md")
        >>> path_to_rst_file = cd(dat_dir, "readme.rst")
        >>> markdown_to_rst(path_to_md_file, path_to_rst_file, verbose=True)
        Converting "tests\\data\\markdown.md" to "tests\\data\\markdown.rst" ... Done.
        >>> markdown_to_rst(path_to_md_file, path_to_rst_file, engine='pypandoc', verbose=True)
        Updating "readme.rst" at "tests\\documents\\" ... Done.
    """

    exe_name = "pandoc.exe"
    optional_pathnames = {exe_name, f"C:\\Program Files\\Pandoc\\{exe_name}"}
    pandoc_exists, pandoc_exe_ = _check_file_pathname(
        name=exe_name, options=optional_pathnames, target=pandoc_exe)

    input_path, output_path = path_to_md, path_to_rst
    arg_f, arg_t = 'markdown+smart', 'rst+smart'
    if reverse:
        input_path, output_path = output_path, input_path
        arg_f, arg_t = arg_t, arg_f

    abs_input_path, abs_output_path = map(pathlib.Path, [input_path, output_path])
    # assert abs_from_path.suffix == ".md" and abs_to_path.suffix == ".rst"

    if verbose:
        rel_input_path, rel_output_path = map(
            lambda x: pathlib.Path(_check_rel_pathname(x)), (abs_input_path, abs_output_path))

        if not os.path.exists(abs_output_path):
            msg = f"Converting \"{rel_input_path}\" to \"{rel_output_path}\""
        else:
            msg = f"Updating \"{rel_output_path.name}\" at \"{rel_output_path.parent}\\\""
        print(msg, end=" ... ")

    try:
        if engine is None:
            if pandoc_exists:
                cmd_args = [
                    pandoc_exe_, '--wrap=preserve', abs_input_path, '-f', arg_f, '-t', arg_t]
                if reverse:
                    cmd_args += ['-o', abs_output_path]
                else:
                    cmd_args += ['-s', '-o', abs_output_path]
                rslt = subprocess.run(cmd_args, **kwargs)
                ret_code = rslt.returncode

            else:
                ret_code = -1

        else:
            py_pandoc = _check_dependency(name='pypandoc')

            if 'extra_args' in kwargs:
                kwargs['extra_args'].append(['--wrap=preserve'])
            else:
                kwargs.update({'extra_args': ['--wrap=preserve']})
            rslt = py_pandoc.convert_file(
                source_file=str(abs_input_path), to=arg_t, outputfile=str(abs_output_path),
                **kwargs)

            ret_code = 0 if rslt == '' else -2

        if verbose:
            if ret_code == 0:
                print("Done.")
            elif ret_code == -1:
                print(
                    "Failed."
                    "\n\"Pandoc\" is required to proceed with `engine=None`; "
                    "however, it is not found on this device."
                    "\nInstall it (https://pandoc.org/) and then try again; "
                    "or, try instead `engine='pypandoc'`")
            else:
                print("Failed.")

    except Exception as e:
        print("An error occurred: {}".format(e))


def _xlsx_to_csv_prep(path_to_xlsx, path_to_csv=None, vbscript=None):
    """
    Prepare paths and VBScript for converting an Excel spreadsheet (*.xlsx*/*.xls*) to a
    `CSV <https://en.wikipedia.org/wiki/Comma-separated_values>`_ file.

    :param path_to_xlsx: The path of the Excel spreadsheet (in .xlsx format).
    :type path_to_xlsx: str | os.PathLike
    :param path_to_csv: The path of the CSV file:

        - When ``path_to_csv=None``, a temporary file is generated;
        - When ``path_to_csv=""``, the CSV file is generated in the same directory as the source
          Excel spreadsheet;
        - Otherwise, it specifies a specific path.

    :type path_to_csv: str | os.PathLike | None
    :param vbscript: The path of the VB script used for converting *.xlsx*/*.xls* to *.csv*;
        when ``vbscript=None``, a default script is used.
    :type vbscript: str | None
    :return: A tuple containing the path of the VB script and the path of the CSV file.
    :rtype: tuple[str, str]
    """

    if vbscript is None:
        vbscript_ = str(importlib.resources.files(__package__).joinpath("../data/xlsx2csv.vbs"))
    else:
        vbscript_ = copy.copy(vbscript)

    if path_to_csv is None:
        temp_file = tempfile.NamedTemporaryFile()
        csv_pathname = temp_file.name + ".csv"
    elif path_to_csv == "":
        csv_pathname = str(path_to_xlsx).replace(".xlsx", ".csv")
    else:
        csv_pathname = copy.copy(path_to_csv)

    return vbscript_, csv_pathname


def _xlsx_to_csv(xlsx_pathname, csv_pathname, sheet_name='1', vbscript=None, **kwargs):
    """
    Convert a `Microsoft Excel <https://en.wikipedia.org/wiki/Microsoft_Excel>`_ spreadsheet
    (*.xlsx*/*.xls*) to a `CSV <https://en.wikipedia.org/wiki/Comma-separated_values>`_ file
    using `VBScript <https://en.wikipedia.org/wiki/VBScript>`_.

    Reference: https://stackoverflow.com/questions/1858195/.

    :param xlsx_pathname: The path of the `Microsoft Excel`_ spreadsheet (in .xlsx format).
    :type xlsx_pathname: str
    :param csv_pathname: The path of the CSV file.
    :type csv_pathname: str | None
    :param sheet_name: The name of the target worksheet in the given `Microsoft Excel`_ file;
        defaults to ``'1'``.
    :type sheet_name: str
    :param vbscript: The path of the VB script used for converting *.xlsx*/*.xls* to *.csv*;
        defaults to ``None``.
    :type vbscript: str | None
    :param kwargs: [Optional] Additional parameters for the function `subprocess.run()`_.
    :return: The result code from running the VBScript.
    :rtype: int

    .. _`Microsoft Excel`: https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`CSV`: https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`subprocess.run()`: https://docs.python.org/3/library/subprocess.html#subprocess.run
    """

    command_args = ["cscript.exe", "//Nologo", vbscript, xlsx_pathname, csv_pathname, sheet_name]
    if platform.system() == 'Linux':
        command_args = ["wine"] + command_args

    rslt = subprocess.run(command_args, **kwargs)
    ret_code = rslt.returncode

    return ret_code


def xlsx_to_csv(path_to_xlsx, path_to_csv=None, engine=None, if_exists='replace', vbscript=None,
                sheet_name='1', ret_null=False, verbose=False, **kwargs):
    """
    Convert a `Microsoft Excel`_ spreadsheet to a `CSV`_ file.

    See also [`STORE-XTC-1 <https://stackoverflow.com/questions/1858195/>`_].

    :param path_to_xlsx: The path of the Microsoft Excel spreadsheet (in *.xlsx* format).
    :type path_to_xlsx: str | os.PathLike
    :param path_to_csv: The path of the CSV file:

        - When ``path_to_csv=None`` (default), a temporary file is generated
          using `tempfile.NamedTemporaryFile()`_.
        - When ``path_to_csv=""``, the CSV file is generated in the same directory as the source
          Microsoft Excel spreadsheet.
        - Otherwise, it specifies a specific path.

    :type path_to_csv: str | os.PathLike | None
    :param engine: The engine used for converting *.xlsx*/*.xls* to .csv:

        - When ``engine=None`` (default), a `VBScript`_ (Visual Basic Script) is used.
        - When ``engine='xlsx2csv'``, the function relies on `xlsx2csv`_.

    :type engine: str | None
    :param if_exists: The action to take if the target CSV file exists; defaults to ``'replace'``.
    :type if_exists: str
    :param vbscript: The path of the VBScript used for converting *.xlsx*/*.xls* to *.csv*;
        defaults to ``None``.
    :type vbscript: str | None
    :param sheet_name: The name of the target worksheet in the given Excel file;
        defaults to ``'1'``.
    :type sheet_name: str
    :param ret_null: Whether to return a value depending on the specified ``engine``;
        defaults to ``False``.
    :type ret_null: bool
    :param verbose: Whether to print relevant information to the console; defaults to ``False``.
    :type verbose: bool | int
    :param kwargs: [Optional] Additional parameters for the function `subprocess.run()`_.
    :return: The path of the generated CSV file or ``None`` when ``engine=None``;
        an `io.StringIO()`_ buffer when ``engine='xlsx2csv'``.
    :rtype: str | _io.StringIO | None

    .. _`Microsoft Excel`:
        https://en.wikipedia.org/wiki/Microsoft_Excel
    .. _`CSV`:
        https://en.wikipedia.org/wiki/Comma-separated_values
    .. _`VBScript`:
        https://en.wikipedia.org/wiki/VBScript
    .. _`tempfile.NamedTemporaryFile()`:
        https://docs.python.org/3/library/tempfile.html#tempfile.NamedTemporaryFile
    .. _`xlsx2csv`:
        https://github.com/dilshod/xlsx2csv
    .. _`io.StringIO()`:
        https://docs.python.org/3/library/io.html#io.StringIO
    .. _`subprocess.run()`:
        https://docs.python.org/3/library/subprocess.html#subprocess.run

    **Examples**::

        >>> from pyhelpers.store import xlsx_to_csv, load_csv
        >>> from pyhelpers.dirs import cd
        >>> import os
        >>> path_to_test_xlsx = cd("tests\\data", "dat.xlsx")
        >>> path_to_temp_csv = xlsx_to_csv(path_to_test_xlsx, verbose=True)
        Converting "tests\\data\\dat.xlsx" to a (temporary) CSV file ... Done.
        >>> os.path.isfile(path_to_temp_csv)
        True
        >>> data = load_csv(path_to_temp_csv, index=0)
        >>> data
                     Longitude    Latitude
        City
        London      -0.1276474  51.5073219
        Birmingham  -1.9026911  52.4796992
        Manchester  -2.2451148  53.4794892
        Leeds       -1.5437941  53.7974185
        >>> # Set `engine='xlsx2csv'`
        >>> temp_csv_buffer = xlsx_to_csv(path_to_test_xlsx, engine='xlsx2csv', verbose=True)
        Converting "tests\\data\\dat.xlsx" to a (temporary) CSV file ... Done.
        >>> # import pandas as pd; data_ = pandas.read_csv(io_buffer, index_col=0)
        >>> data_ = load_csv(temp_csv_buffer, index=0)
        >>> data_
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418
        >>> data.astype('float16').equals(data_.astype('float16'))
        True
        >>> # Remove the temporary CSV file
        >>> os.remove(path_to_temp_csv)
    """

    if verbose:
        rel_path = _check_rel_pathname(path_to_xlsx)
        print(f"Converting \"{rel_path}\" to a (temporary) CSV file", end=" ... ")

    if engine is None:
        vbscript_, csv_pathname = _xlsx_to_csv_prep(
            path_to_xlsx=path_to_xlsx, path_to_csv=path_to_csv, vbscript=vbscript)

        if os.path.exists(csv_pathname):
            if if_exists == 'replace':
                os.remove(csv_pathname)
            elif if_exists == 'pass':
                if verbose:
                    print("Cancelled.")
                return csv_pathname

        ret_code = _xlsx_to_csv(
            xlsx_pathname=path_to_xlsx, csv_pathname=csv_pathname, sheet_name=sheet_name,
            vbscript=vbscript_, **kwargs)

        if verbose:
            print("Done." if ret_code == 0 else "Failed.")

        if not ret_null and ret_code == 0:
            return csv_pathname

    elif engine == 'xlsx2csv':
        xlsx2csv = _check_dependency(name='xlsx2csv')

        buffer = io.StringIO()
        try:
            xlsx2csv.Xlsx2csv(
                xlsxfile=path_to_xlsx, sheet_name=sheet_name, outputencoding="utf-8").convert(
                buffer)
            buffer.seek(0)

            if verbose:
                print("Done.")

            return buffer

        except Exception as e:
            _print_failure_msg(e=e, msg="Failed.")
            buffer.close()
