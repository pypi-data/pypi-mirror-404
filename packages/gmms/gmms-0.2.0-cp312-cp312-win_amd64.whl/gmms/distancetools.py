""" Distance tools for GMMs.
    Default back-end: Python. 
    Optional back-end: Cython (user should specify). If fails, defaults to Python. 
"""

__author__ = 'A. Renmin Pretell Ductram'

def select_backend(use_cython=False):

    global _impl, __implementation__

    if use_cython:
        try:
            import gmms.distancetools_cy as _disttools
            _impl = _disttools
            __implementation__ = 'Cython'
            return
        except ImportError:
            print('Cython implementation failed to load. Defaulting to Python.')
            pass

    import gmms.distancetools_py as _disttools
    _impl = _disttools
    __implementation__ = 'Python'

select_backend(use_cython=False)

def get_distances(*args, **kwargs):
    return _impl.get_distances(*args, **kwargs)

def get_bearing(*args, **kwargs):
    return _impl.get_bearing(*args, **kwargs)

def get_Rjb(*args, **kwargs):
    return _impl.get_Rjb(*args, **kwargs)

def get_Rrup(*args, **kwargs):
    return _impl.get_Rrup(*args, **kwargs)

def get_Rx(*args, **kwargs):
    return _impl.get_Rx(*args, **kwargs)

def get_distances(*args, **kwargs):
    return _impl.get_distances(*args, **kwargs)
