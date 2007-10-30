#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Template generator

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import re
import cgi
import urllib

_RE_FIRST_WORD = re.compile(r"\s*(\w+)\s+(.*)")
_RE_URL = re.compile(r"(?:(?P<proto>[a-z]+)://)?(?P<host>[^/]+)(?:/(?P<path>.*))?")
                
#------------------------
class Tag(object):
    """
    A tag definition:
    - has_content (boolean): True if this kind of tag requires a content and
                             an end-tag marker.
    """
    def __init__(self, tag, has_content):
        self._tag = tag
        self._has_content = has_content

    def Tag(self):
        return self._tag
    
    def HasContent(self):
        return self._has_content

    def Generate(self, tag_node, context):
        """
        Generates content for the tag node for the given context.
        Returns a string with the generated content.
        """
        raise NotImplementedError("TagDef is abstract")


#------------------------
class TagComment(Tag):
    """
    Tag that represents a comment. It has no content.
    Template syntax:
      [[# .... anything is a comment till the end marker]]
    """
    def __init__(self):
        super(TagComment, self).__init__(tag="#", has_content=False)
    
    def Generate(self, tag_node, context):
        return ""


#------------------------
class TagRaw(Tag):
    """
    Tag that represents a raw expression expansion. The data is represented as-is.
    Template syntax:
      [[raw python_expression]]
    """
    def __init__(self):
        super(TagRaw, self).__init__(tag="raw", has_content=False)
    
    def Generate(self, tag_node, context):
        result = eval(tag_node.Parameters(), dict(context))
        return str(result)


#------------------------
class TagHtml(Tag):
    """
    Tag that represents an expression expansion with html encoding.
    Template syntax:
      [[html python_expression]]
    """
    def __init__(self):
        super(TagHtml, self).__init__(tag="html", has_content=False)
    
    def Generate(self, tag_node, context):
        result = eval(tag_node.Parameters(), dict(context))
        return cgi.escape(str(result))


#------------------------
class TagUrl(Tag):
    """
    Tag that represents an expression expansion with url encoding
    Template syntax:
      [[url python_expression]]
    """
    def __init__(self):
        super(TagUrl, self).__init__(tag="url", has_content=False)
    
    def Generate(self, tag_node, context):
        result = eval(tag_node.Parameters(), dict(context))
        result = _RE_URL.sub(_UrlEncode, str(result))
        return result

def _UrlEncode(m):
    proto = m.group("proto") or ""
    if proto:
        proto = urllib.quote(proto, "") + "://"
    host = m.group("host") or ""
    if host:
        host = urllib.quote(host, ".:@")
    path = m.group("path") or ""
    if path:
        path = "/" + urllib.quote(path, "/")
    return "%s%s%s" % (proto, host, path)


#------------------------
class TagFor(Tag):
    """
    Tag that represents a for loop. It has a content.
    Template syntax:
      [[for x in python_expression]] content [[end]]
    """
    def __init__(self):
        super(TagFor, self).__init__(tag="for", has_content=True)
    
    def Generate(self, tag_node, context):
        params = tag_node.Parameters()
        
        matches = _RE_FIRST_WORD.match(params)
        var, params = matches.group(1), matches.group(2)
        assert var != ""
        
        matches = _RE_FIRST_WORD.match(params)
        word, params = matches.group(1), matches.group(2)
        assert word == "in"
        assert params != ""
        
        result = eval("[%s for %s in %s]" % (var, var, params), dict(context))
        s = ""
        content = tag_node.Content()
        for value in result:
            d = dict(context)  # clone context before udpating it
            d[var] = value
            s += content.Generate(d)

        return s


#------------------------
class TagIf(Tag):
    """
    Tag that represents a conditional if. It has a content.
    There's no "else" or "elif" yet.
    Template syntax:
      [[if python_expression]] content [[end]]
    """
    def __init__(self):
        super(TagIf, self).__init__(tag="if", has_content=True)
    
    def Generate(self, tag_node, context):
        result = eval(tag_node.Parameters(), dict(context))
        if not not result:
            return tag_node.Content().Generate(context)
        return ""

#------------------------
ALL_TAGS = [TagComment, TagFor, TagIf, TagRaw, TagHtml, TagUrl]

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
