""" *************************************
Mod autor: night_dragon_on
Mod file name: modsCore.pyc
Url page: https://goo.gl/TJW6U0

The part of the code from the repository was used:
XFW Library (c) https://modxvm.com 2013-2018
https://bitbucket.org/XVM/
************************************* """
import json, urllib2, traceback

class cfgLoader(object):

    def __init__(self, path, mode):
        self.cfg = None
        self.load(path, mode)
        return

    def __call__(self, path):
        path = path.split('/')
        c = self.cfg
        for x in path:
            if x in c:
                c = c[x]

        return c

    def comments(self, string):
        if string:
            comment = []
            comments = False
            for line in string.split('\n'):
                if '/*' in line:
                    comments = True
                    continue
                if '*/' in line:
                    comments = False
                    continue
                if comments:
                    continue
                line = line.split('// ')[0]
                line = line.split('# ')[0]
                line = line.strip()
                if line:
                    comment.append(line)

            string = ('\n').join(comment)
        return string

    def byteify(self, input):
        if input:
            if isinstance(input, dict):
                return {self.byteify(key):self.byteify(value) for key, value in input.iteritems()}
            if isinstance(input, list):
                return [ self.byteify(element) for element in input ]
            if isinstance(input, unicode):
                return input.encode('utf-8')
            return input
        return input

    def load(self, path, mode):
        try:
            if mode == 'local':
                json_file = open(path, 'r')
            else:
                if mode == 'server':
                    json_file = urllib2.urlopen(path, timeout=3)
        except IOError as e:
            self.cfg = None
            print '[ERROR] - %s' % e
        else:
            file_data = json_file.read().decode('utf-8-sig')
            data = self.byteify(json.loads(self.comments(file_data)))
            json_file.close()
            self.cfg = data

        return


class EventHook(object):

    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        if handler in self.__handlers:
            self.__handlers.remove(handler)
        return self

    def fire(self, *args, **keywargs):
        for handler in self.__handlers:
            handler(*args, **keywargs)

    def clearObjectHandlers(self, inObject):
        for theHandler in self.__handlers:
            if theHandler.im_self == inObject:
                self -= theHandler


def _RegisterEvent(handler, cls, method, prepend=False):
    evt = '__event_%i_%s' % (1 if prepend else 0, method)
    if hasattr(cls, evt):
        e = getattr(cls, evt)
    else:
        newm = '__orig_%i_%s' % (1 if prepend else 0, method)
        setattr(cls, evt, EventHook())
        setattr(cls, newm, getattr(cls, method))
        e = getattr(cls, evt)
        m = getattr(cls, newm)
        setattr(cls, method, lambda *a, **k: __event_handler(prepend, e, m, *a, **k))
    e += handler


def __event_handler(prepend, e, m, *a, **k):
    try:
        if prepend:
            e.fire(*a, **k)
            r = m(*a, **k)
        else:
            r = m(*a, **k)
            e.fire(*a, **k)
        return r
    except StandardError:
        traceback.print_exc()


def _override(cls, method, newm):
    orig = getattr(cls, method)
    if type(orig) is not property:
        setattr(cls, method, newm)
    else:
        setattr(cls, method, property(newm))


def _OverrideMethod(handler, cls, method):
    orig = getattr(cls, method)
    newm = lambda *a, **k: handler(orig, *a, **k)
    _override(cls, method, newm)


def _OverrideStaticMethod(handler, cls, method):
    orig = getattr(cls, method)
    newm = staticmethod(lambda *a, **k: handler(orig, *a, **k))
    _override(cls, method, newm)


def _OverrideClassMethod(handler, cls, method):
    orig = getattr(cls, method)
    newm = classmethod(lambda *a, **k: handler(orig, *a, **k))
    _override(cls, method, newm)


def _hook_decorator(func):

    def decorator1(*a, **k):

        def decorator2(handler):
            func(handler, *a, **k)

        return decorator2

    return decorator1


registerEvent = _hook_decorator(_RegisterEvent)
overrideMethod = _hook_decorator(_OverrideMethod)
overrideStaticMethod = _hook_decorator(_OverrideStaticMethod)
overrideClassMethod = _hook_decorator(_OverrideClassMethod)
