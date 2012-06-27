#! /usr/bin/env python
""" A script to generate a tabular view of url endpoints and method signature from the module inline 
documentation"""

import sys
import os
import inspect
from collections import namedtuple
import sys
import re 
sys.path.insert(0, os.path.abspath('..'))
from Netflix import *

DefaultArg = namedtuple('DefaultArg', 'valid value')

def get_default_arg(args, defaults, i):
    if not defaults:
        return DefaultArg(False, None)
    args_with_no_defaults = len(args) - len(defaults)
    if i < args_with_no_defaults:
        return DefaultArg(False, None)
    else:
        value = defaults[i - args_with_no_defaults]
        if (type(value) is str):
            value = '"%s"' % value
        return DefaultArg(True, value)

Summary = namedtuple('Summary', 'url sig doc')

def get_method_summary(class_obj):
    methods = {}
    summary = []
    for method in dir(class_obj):
        if not method.startswith('_'):
            methods[method] = inspect.getargspec(getattr(class_obj,  method))

    for (method, args) in methods.items():
        i=0
        args_str = []
        for arg in args.args:
            default_arg = get_default_arg(args.args, args.defaults, i)
            if default_arg.valid:
                args_str.append("%s=%s" % (arg, default_arg.value))
            elif arg != 'self':
                args_str.append(arg)
            i += 1
        sig = "%s(%s)" % (method, ", ".join(args_str))

        doc = inspect.getdoc(getattr(class_obj, method))
        #print doc
        url = ""
        if doc:
            m = re.search('url:\s+(\S+)', doc)
            if m:
                url = m.group(1)

        link = ":py:meth:`~%s.%s`" %(class_obj.__name__, method)
        summary.append(Summary(url, sig, link))

    return summary

def print_table(full_summary, name):
    print ".. csv-table:: %s api" % name
    print '    :header: "URL", "Signature", "More"\n'
    for summary in full_summary:
        print '    "*%s*", "%s", "%s"' % (summary.url, summary.sig, summary.doc)

summary_nf = get_method_summary(NetflixAPIV2)
summary_u = get_method_summary(User)

print_table(summary_nf, 'NetflixAPIV2')
print_table(summary_u, 'User')


