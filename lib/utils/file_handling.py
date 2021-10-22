import os


def absolute_file_paths(directory):
    """Return list of absolute filepaths in directory.

    Args:
        directory (directory): [description]

    Returns:
        list: list of absolute filepaths
    """
    path = os.path.abspath(directory)
    return [entry.path for entry in os.scandir(path) if entry.is_file()]
