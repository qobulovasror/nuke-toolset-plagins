def uni_str(text):
    """For Py2<>Py3 compatibility. Make sure text is unicode"""
    try:
        # Python2
        return unicode(text)
    except NameError:
        # Python3
        return str(text)

try:
    # python2
    range = xrange
except:
    # python3
    range = range