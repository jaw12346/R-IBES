import numpy as np

ndarray_shape = (128,)
__all__ = ['decode_memoryview_to_ndarray', 'encode_ndarray_to_memoryview', 'get_normalized_name',
           'get_denormalized_name', 'ndarray_shape']


def decode_memoryview_to_ndarray(mv):
    """
    Convert a hex memoryview to a numpy ndarray

    :param mv: Memoryview to convert
    :type mv: memoryview
    :return: ndarray(128,)
    """
    return np.frombuffer(mv, dtype=np.float64).reshape(ndarray_shape)


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


def get_denormalized_name(normalized_name):
    """
    Standard conversion from a normalized name to a denormalized name (jacob_weber -> Jacob Weber)
    :param normalized_name: Name to denormalize
    :type normalized_name: str
    :return: Denormalized name (title case, spaces instead of underscores)
    :rtype: str
    """
    return normalized_name.replace('_', ' ').title()
