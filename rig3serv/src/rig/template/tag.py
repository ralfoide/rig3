#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Template generator

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import re

_RE_FIRST_WORD = re.compile(r"\s*(\w+)\s+(.*)")

#------------------------
class Tag(object):
    """
    A tag definition:
    - has_content (boolean): True if this kind of tag requires a content and
                             an end-tag marker.
    """
    def __init__(self, tag, has_content):
        self.tag = tag
        self.has_content = has_content

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
class TagExpression(Tag):
    """
    Tag that represents an expression expansion.
    Template syntax:
      [[python_expression]]
    """
    def __init__(self):
        super(TagExpression, self).__init__(tag=None, has_content=False)
    
    def Generate(self, tag_node, context):
        result = eval(tag_node.parameters, dict(context))
        return str(result)


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
        params = tag_node.parameters
        
        matches = _RE_FIRST_WORD.match(params)
        var, params = matches.group(1), matches.group(2)
        assert var != ""
        
        matches = _RE_FIRST_WORD.match(params)
        word, params = matches.group(1), matches.group(2)
        assert word == "in"
        assert params != ""
        
        result = eval("[%s for %s in %s]" % (var, var, params), dict(context))
        s = ""
        content = tag_node.content
        for value in result:
            d = dict(context)
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
        result = eval(tag_node.parameters, dict(context))
        if not not result:
            return tag_node.content.Generate(context)
        return ""

#------------------------
ALL_TAGS = [TagComment, TagFor, TagIf]

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
