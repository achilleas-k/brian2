import sys
import inspect

class Tracer(object):
    def __init__(self):
        sys.settrace(self)
    def __call__(self, frame, event, arg):
        if event=='call':
            filename = frame.f_code.co_filename
            #print filename
            if '__main__' in filename:
                lineno = frame.f_lineno
                # Here I'm printing the file and line number, 
                # but you can examine the frame, locals, etc too.
                print "%s @ %s" % (filename, lineno)
        return
    
if __name__=='__main__':
    print __file__
    from brian2 import *
    tracer = Tracer()
    G = NeuronGroup(1, 'v:1')
    G.v = 1
    G.v
