import os
import csv
import tempfile
import shutil


def create_temp_text(contents):
    """
    Create a temporary UTF-8 text file and return its path.
    """

    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        encoding="utf-8",
        newline=""
    )

    tmp.write(contents)
    tmp.close()

    return tmp.name


def create_temp_csv(rows):
    """
    Create a temporary CSV file.

    rows should be a list of lists.
    """

    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        encoding="utf-8",
        newline=""
    )

    writer = csv.writer(tmp)

    for row in rows:
        writer.writerow(row)

    tmp.close()

    return tmp.name


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def remove_file(path):
    if os.path.exists(path):
        os.remove(path)


def create_temp_directory():
    return tempfile.mkdtemp()


def remove_temp_directory(path):
    shutil.rmtree(path, ignore_errors=True)