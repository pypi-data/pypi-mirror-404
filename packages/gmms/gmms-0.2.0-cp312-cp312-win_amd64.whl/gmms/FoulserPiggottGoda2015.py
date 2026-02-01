""" Ground motion model by Faulser-Piggott and Goda (2015) for Ia and CAV.
    Default back-end: Python. 
    Optional back-end: Cython (user should specify). If fails, defaults to Python. 
"""

__author__ = 'A. Renmin Pretell Ductram'

def select_backend(use_cython=False):

    global _impl, __implementation__

    if use_cython:
        try:
            import gmms.FoulserPiggottGoda2015_cy as _FPG15
            _impl = _FPG15
            __implementation__ = 'Cython'
            return
        except ImportError:
            print('Cython implementation failed to load. Defaulting to Python.')
            pass

    import gmms.FoulserPiggottGoda2015_py as _FPG15
    _impl = _FPG15
    __implementation__ = 'Python'

select_backend(use_cython=False)

def FoulserPiggottGoda2015(*args, **kwargs):
    return _impl.FoulserPiggottGoda2015(*args, **kwargs)

def get_mu(*args, **kwargs):
    return _impl.get_mu(*args, **kwargs)

def get_phi(*args, **kwargs):
    return _impl.get_phi(*args, **kwargs)

def get_tau(*args, **kwargs):
    return _impl.get_tau(*args, **kwargs)
