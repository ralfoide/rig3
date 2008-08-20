#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Template generator

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
import re
import cgi
import urllib

_RE_FIRST_WORD = re.compile(r"\s*(\w+)\s+(.*)")
_RE_URL = re.compile(r"(?:(?P<proto>[a-z]+)://(?P<host>[^/#]+))?(?P<path>.*)")

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

    def Generate(self, log, tag_node, context):
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
    
    def Generate(self, log, tag_node, context):
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
    
    def Generate(self, log, tag_node, context):
        try:
            result = eval(tag_node.Parameters(), dict(context))
            result = str(result)
        except Exception, e:
            raise e.__class__("%s\nTag: %s\nContext: %s" % (e, tag_node, context))
        return result


#------------------------
class TagHtml(Tag):
    """
    Tag that represents an expression expansion with html encoding.
    Template syntax:
      [[html python_expression]]
    """
    def __init__(self):
        super(TagHtml, self).__init__(tag="html", has_content=False)
    
    def Generate(self, log, tag_node, context):
        try:
            result = eval(tag_node.Parameters(), dict(context))
            result = cgi.escape(str(result))
        except Exception, e:
            raise e.__class__("%s\nTag: %s\nContext: %s" % (e, tag_node, context))
        return result


#------------------------
class TagXml(Tag):
    """
    Tag that represents an expression expansion with xml encoding.
    Template syntax:
      [[xml python_expression]]
      
    Note: this is implemented exactly like the [[html]] tag. The difference
    is purely semantic.
    """
    def __init__(self):
        super(TagXml, self).__init__(tag="xml", has_content=False)
    
    def Generate(self, log, tag_node, context):
        try:
            result = eval(tag_node.Parameters(), dict(context))
            result = cgi.escape(str(result))
        except Exception, e:
            raise e.__class__("%s\nTag: %s\nContext: %s" % (e, tag_node, context))
        return result


#------------------------
class TagUrl(Tag):
    """
    Tag that represents an expression expansion with url encoding
    Template syntax:
      [[url python_expression]]
    """
    def __init__(self):
        super(TagUrl, self).__init__(tag="url", has_content=False)
    
    def Generate(self, log, tag_node, context):
        try:
            result = eval(tag_node.Parameters(), dict(context))
            result = _RE_URL.sub(_UrlEncode, str(result))
        except Exception, e:
            raise e.__class__("%s\nTag: %s\nContext: %s" % (e, tag_node, context))
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
        path = urllib.quote(path, "/#")
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
    
    def Generate(self, log, tag_node, context):
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
            s += content.Generate(log, d)

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
    
    def Generate(self, log, tag_node, context):
        result = eval(tag_node.Parameters(), dict(context))
        if not not result:
            return tag_node.Content().Generate(log, context)
        return ""


#------------------------
class TagInsert(Tag):
    """
    Tag that represents a template insertion. The expression must
    evaluate to the path of the template to use.
    
    Template syntax:
      [[insert python_expression]]
    """
    def __init__(self):
        super(TagInsert, self).__init__(tag="insert", has_content=False)
    
    def Generate(self, log, tag_node, context):
        filename = eval(tag_node.Parameters(), dict(context))
        
        if not not filename:
            template_file = None

            from rig.template.template import CONTEXT_FILENAME, CONTEXT_DIRS

            # if there's a list of template directories to use in the context
            # look for the template in there first
            for dir in context.get(CONTEXT_DIRS, []):
                full = os.path.join(dir, filename)
                if os.path.exists(full) and os.path.isfile(full):
                    template_file = full
                    break

            if not template_file:            
                # if there's a template_filename setting in the context
                # (set by Template.Generate()) and we can match a relative
                # file, try to do so.
                if CONTEXT_FILENAME in context:
                    full = os.path.join(os.path.dirname(context[CONTEXT_FILENAME]), filename)
                    if os.path.exists(full) and os.path.isfile(full):
                        template_file = full

            if not template_file:
                # was it an absolute path (or at least relative to PWD?
                if os.path.exists(filename) and os.path.isfile(filename):
                    template_file = filename

            if not template_file:
                raise IOError("Template '%s' not found for [[insert]] tag" % filename)

            from rig.template.template import Template
            template = Template(log, file=template_file)
            result = template.Generate(context)
            return result
        return ""


#------------------------
ALL_TAGS = [TagComment, TagFor, TagIf, TagRaw, TagHtml, TagXml, TagUrl, TagInsert]

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
