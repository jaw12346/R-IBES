"""
File providing conversion methods for the R-IBES system.
"""

from numpy import frombuffer, float64

ndarray_shape = (128,)
__all__ = ['decode_memoryview_to_ndarray', 'encode_ndarray_to_memoryview', 'get_normalized_name',
           'get_denormalized_name', 'ndarray_shape']


def decode_memoryview_to_ndarray(to_convert):
    """
    Convert a hex memoryview to a numpy ndarray

    :param to_convert: Memoryview to convert
    :type to_convert: memoryview
    :return: ndarray(128,)
    """
    return frombuffer(to_convert, dtype=float64).reshape(ndarray_shape)


def encode_ndarray_to_memoryview(encoding):
    """
    Convert a facial encoding in numpy ndarray format to a hex memoryview

    :param encoding: Facial encoding in numpy ndarray format
    :type encoding: ndarray(128,)
    :return: Memoryview of the facial encoding
    :rtype: memoryview
    """
    return memoryview(encoding.tobytes())


def get_normalized_name(name):
    """
    Standard conversion from a name to a normalized name (Jacob Weber -> jacob_weber)

    :param name: Name to normalize
    :type name: str
    :return: Normalized name (lowercase, underscores instead of spaces)
    :rtype: str
    """
    return name.strip().lower().replace(' ', '_')


def get_dbpedia_name(name):
    """
    Standard conversion from a normalized name to a DBPedia name (george_h._w._bush -> George_H._W._Bush)

    :param name: Name to convert to DBPedia format (title/snake_case)
    :type name: str
    :return: DBPedia-formatted name
    :rtype: str
    """
    spaced_name = name.replace('_', ' ')
    titled_name = spaced_name.title()
    return titled_name.replace(' ', '_')


def get_denormalized_name(normalized_name):
    """
    Standard conversion from a normalized name to a denormalized name (jacob_weber -> Jacob Weber)

    :param normalized_name: Name to denormalize
    :type normalized_name: str
    :return: Denormalized name (title case, spaces instead of underscores)
    :rtype: str
    """
    return normalized_name.replace('_', ' ').title()
