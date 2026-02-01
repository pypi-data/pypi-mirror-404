""" Ground motion model by Campbell and Bozorgnia (2019) for Ia and CAV . 
    Default back-end: Python. 
    Optional back-end: Cython (user should specify). If fails, defaults to Python. 
"""

__author__ = 'A. Renmin Pretell Ductram'

def select_backend(use_cython=False):

    global _impl, __implementation__

    if use_cython:
        try:
            import gmms.CampbellBozorgnia2019_cy as _CB19
            _impl = _CB19
            __implementation__ = 'Cython'
            return
        except ImportError:
            print('Cython implementation failed to load. Defaulting to Python.')
            pass

    import gmms.CampbellBozorgnia2019_py as _CB19
    _impl = _CB19
    __implementation__ = 'Python'

select_backend(use_cython=False)

def CampbellBozorgnia2019(*args, **kwargs):
    return _impl.CampbellBozorgnia2019(*args, **kwargs)

def get_mu(*args, **kwargs):
    return _impl.get_mu(*args, **kwargs)

def get_phi(*args, **kwargs):
    return _impl.get_phi(*args, **kwargs)

def get_tau(*args, **kwargs):
    return _impl.get_tau(*args, **kwargs)
