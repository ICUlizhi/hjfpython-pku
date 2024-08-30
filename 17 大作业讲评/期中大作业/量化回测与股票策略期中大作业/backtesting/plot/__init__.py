import sys


try:
    import matplotlib
except ImportError:
    raise ImportError(
        'Matplotlib seems to be missing. Needed for plotting support')
else:
    touse = 'TKAgg' if sys.platform != 'darwin' else 'MacOSX'
    try:
        matplotlib.use(touse)
    except:
        
        
        pass


from .plot import Plot, Plot_OldSync
from .scheme import PlotScheme
