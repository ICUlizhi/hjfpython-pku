__all__ = ['BacktraderError', 'StrategySkipError']


class BacktraderError(Exception):
    '''Base exception for all other exceptions'''
    pass


class StrategySkipError(BacktraderError):
    '''Requests the platform to skip this strategy for backtesting. To be
    raised during the initialization (``__init__``) phase of the instance'''
    pass


class ModuleImportError(BacktraderError):
    '''Raised if a class requests a module to be present to work and it cannot
    be imported'''
    def __init__(self, message, *args):
        super(ModuleImportError, self).__init__(message)
        self.args = args


class FromModuleImportError(ModuleImportError):
    '''Raised if a class requests a module to be present to work and it cannot
    be imported'''
    def __init__(self, message, *args):
        super(FromModuleImportError, self).__init__(message, *args)
