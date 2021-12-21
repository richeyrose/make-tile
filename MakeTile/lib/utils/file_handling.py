import os
import re


def rchop(s, suffix):
    """Return right chopped string.

    Parameters
    s : str
        string to chop
    suffix : str
        suffix to remove from string
    """
    if suffix and s.endswith(suffix):
        return s[:-len(suffix)]
    return s


def absolute_file_paths(directory):
    """Return list of absolute filepaths in directory.

    Args:
        directory (directory): [description]

    Returns:
        list: list of absolute filepaths
    """
    path = os.path.abspath(directory)
    return [entry.path for entry in os.scandir(path) if entry.is_file()]


def find_and_rename(slug, current_slugs):
    """Recursively search for and rename ID object based on slug.

    Recursively searches for the passed in slug in current slugs and
    appends and increments a number to the slug if found until slug is unique.

    Parameters
    obj : bpy.types.ID
    slug : str
    current_slugs : list of str

    Returns
    slug : str
    """
    if slug not in current_slugs:
        current_slugs.append(slug)
        return slug

    match = re.search(r'\d+$', slug)
    if match:
        slug = rchop(slug, match.group())
        slug = slug + str(int(match.group()) + 1).zfill(3)
        slug = find_and_rename(slug, current_slugs)
    else:
        slug = slug + '.001'
        slug = find_and_rename(slug, current_slugs)
    return slug
