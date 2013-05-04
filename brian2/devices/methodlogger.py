'''
Functions and classes to handle logging of method calls. This is used for
implementing standalone code generation.

TODO: this could probably be done much more cleanly with sys.settrace! (yes, but tricky)
'''
import inspect

__all__ = ['method_logger', 'MethodCall']

class MethodCall(object):
    '''
    Saved information about a logged method call.
    '''
    def __init__(self, returnval, obj, meth, args, kwds):
        self.returnval = returnval #: The object returned by the method call
        self.obj = obj #: The object the method was called on
        self.objclass = obj._original_class #: The original class of the object
        self.meth = meth #: The method object itself
        self.args = args #: The arguments passed to the method
        self.kwds = kwds #: The keywords passed to the method
        self.methname = meth.__name__ #: The name of the method
        self.handlekey = self.objclass #: The key used for handlers
        
        if hasattr(obj, 'name'):
            self.objname = obj.name #: The unique Brian name of the object, or UNKNOWN
        else:
            self.objname = 'UNKNOWN'
            
        argstr = ', '.join(repr(arg) for arg in args)
        kwdstr = ', '.join(k+'='+repr(v) for k, v in kwds.items())
        m = []
        if argstr:
            m.append(argstr)
        if kwdstr:
            m.append(kwdstr)
        
        #: A string representation of the method call
        self.representation = '%s = %s.%s(%s)'%(self.returnval,
                                                self.objname, self.methname,
                                                ', '.join(m))
        self.call_representation = '%s.%s(%s)'%(self.objname, self.methname,
                                                ', '.join(m))

    def __str__(self):
        return self.representation
    __repr__ = __str__
        

class CallLogger(object):
    '''
    Replaces a method object and stores method calls in a list.
    
    Parameters
    ----------
    
    obj : object
        The object the method is bound to.
    meth : method
        The method.
    target : list
        A list to append method calls to.
    runit : bool
        Whether or not to run the method.
    '''
    def __init__(self, obj, meth, target, runit=True):
        self.obj = obj
        self.meth = meth
        self.target = target
        self.runit = runit
    def __call__(self, *args, **kwds):
        if self.runit:
            rv = self.meth(*args, **kwds)
        else:
            rv = None
        mc = MethodCall(rv, self.obj, self.meth, args, kwds)
        self.target.append(mc)
        return rv
    
    
def method_logger(origclass, target, methnames=None):
    '''
    Replaces a class with one that logs its method calls.
    
    Note that only methods that do not start ``__`` will work, with the
    exception of ``__init__`` which is explicitly handled.
    
    Parameters
    ----------
    origclass : class
        The class to replace
    target : list
        An empty list to place the logged method calls in. Each item inserted
        will be of type `MethodCall`.
    methnames : None or dict
        A dict of pairs ``(methodname, runit)`` to log, or None to log all
        (you will get a lot!). The ``runit`` is a boolean flag indicating
        whether or not to run the method.
        
    Returns
    -------
    
    A new class derived from ``origclass`` that will log all the specified
    method calls.
    '''
    def runit(name):
        if methnames is None:
            return True
        else:
            return methnames[name]
    class MethodLogger(origclass):
        _original_class = origclass
        # Have to handle __init__ method separately
        def __init__(self, *args, **kwds):
            origclass.__init__(self, *args, **kwds)
            if methnames is None or '__init__' in methnames:
                cl = self.__init__
                mc = MethodCall(None, self, cl.meth, args, kwds)
                target.append(mc)
        def __getattribute__(self, name):
            obj = origclass.__getattribute__(self, name)
            if inspect.ismethod(obj):
                if methnames is None or name in methnames:
                    obj = CallLogger(self, obj, target, runit=runit(name))
            return obj
    MethodLogger.__name__ = origclass.__name__
    return MethodLogger


if __name__=='__main__':
    from brian2 import *
    logged = []    
    NeuronGroup = method_logger(NeuronGroup, logged,
                                methnames={'set_state': True, 'state': True,
                                           '__init__':True},
                                )
    G = NeuronGroup(1, 'v:1')
    G.v = 1
    print G.v
    for mc in logged:
        print mc.objclass, mc
    #run(10*ms)
    
    