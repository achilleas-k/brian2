__all__ = ['function_logger', 'FunctionCall']

class FunctionCall(object):
    def __init__(self, returnval, func, args, kwds):
        self.returnval = returnval #: Value returned by the function call
        self.func = func #: The function itself
        self.funcname = func.__name__ #: The name of the function
        self.args = args #: Arguments passed to function
        self.kwds = kwds #: Keywords passed to function

        argstr = ', '.join(repr(arg) for arg in self.args)
        kwdstr = ', '.join(k+'='+repr(v) for k, v in self.kwds.items())
        m = []
        if argstr:
            m.append(argstr)
        if kwdstr:
            m.append(kwdstr)
        self.representation = '%s = %s(%s)'%(self.returnval, self.funcname,
                                             ', '.join(m))
        self.call_representation = '%s(%s)'%(self.funcname, ', '.join(m))
    
    def __repr__(self):
        return self.representation
    __str__ = __repr__

def function_logger(original_func, target, runit=True):
    def new_func(*args, **kwds):
        if runit:
            obj = original_func(*args, **kwds)
        else:
            obj = None
        fc = FunctionCall(obj, original_func, args, kwds)
        target.append(fc)
        return obj
    new_func.__name__ = original_func.__name__
    return new_func

if __name__=='__main__':
    from brian2 import *
    calls = []
    run = function_logger(run, calls)
    run(10*ms)
    for fc in calls:
        print fc
