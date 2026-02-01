""" Ground motion model by Campbell and Bozorgnia (2011) for CAVdp.
    Default back-end: Python. 
    Optional back-end: Cython (user should specify). If fails, defaults to Python. 
"""

__author__ = 'A. Renmin Pretell Ductram'

def select_backend(use_cython=False):

    global _impl, __implementation__

    if use_cython:
        try:
            import gmms.CampbellBozorgnia2011_cy as _CB11
            _impl = _CB11
            __implementation__ = 'Cython'
            return
        except ImportError:
            print('Cython implementation failed to load. Defaulting to Python.')
            pass

    import gmms.CampbellBozorgnia2011_py as _CB11
    _impl = _CB11
    __implementation__ = 'Python'

select_backend(use_cython=False)

def CampbellBozorgnia2011(*args, **kwargs):
    return _impl.CampbellBozorgnia2011(*args, **kwargs)

def get_mu(*args, **kwargs):
    return _impl.get_mu(*args, **kwargs)

def get_phi(*args, **kwargs):
    return _impl.get_phi(*args, **kwargs)

def get_tau(*args, **kwargs):
    return _impl.get_tau(*args, **kwargs)

def get_alpha(*args, **kwargs):
    return _impl.get_alpha(*args, **kwargs)
