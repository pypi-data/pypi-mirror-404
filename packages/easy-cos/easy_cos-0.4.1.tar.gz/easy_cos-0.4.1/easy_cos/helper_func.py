import contextlib
import sys
import os
import shutil

@contextlib.contextmanager
def SuppressPrint():
    """
    A context manager to temporarily suppress print statements.

    Usage:
    with SuppressPrint():
        noisy_function()
    """
    original_stdout = sys.stdout
    with open(os.devnull, 'w') as devnull:
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = original_stdout

def delete_coscli_output(
    coscli_output_dir: str = "./coscli_output"
):
    if os.path.exists(coscli_output_dir):
        shutil.rmtree(coscli_output_dir)
    return None    

def _split_cospath(cos_path: str) -> tuple:
    """
    Split the given COS file path into its components.

    Args:
    path (str): The COS file path to be split.

    Returns:
    tuple: A tuple containing the bucket name, prefix, and file name.
    """
    split_path = cos_path.split("/")
    bucket_name = split_path[0]
    prefix = "/".join(split_path[1:-1])
    file_name = split_path[-1]
    return bucket_name, prefix, file_name

def _split_cosdir(cos_dir: str) -> tuple:
    """
    Split the given COS directory into its components.

    Args:
    path (str): The COS directory to be split.

    Returns:
    tuple: A tuple containing the bucket name, prefix.
    """
    if cos_dir.endswith("/"):
        split_dir = cos_dir.split("/")[:-1]
    else:
        split_dir = cos_dir.split("/")
    bucket_name = split_dir[0]
    prefix = "/".join(split_dir[1:])
    return bucket_name, prefix