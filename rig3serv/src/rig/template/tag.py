#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Template generator

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

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

class TagComment(Tag):
    def __init__(self):
        super(TagComment, self).__init__(tag="#", has_content=False)
    
    def Generates(self, tag_node, context):
        return ""

class TagFor(Tag):
    def __init__(self):
        super(TagFor, self).__init__(tag="for", has_content=True)
    
    def Generates(self, tag_node, context):
        raise NotImplementedError("TBD")
        return ""


class TagIf(Tag):
    def __init__(self):
        super(TagIf, self).__init__(tag="if", has_content=True)
    
    def Generates(self, tag_node, context):
        raise NotImplementedError("TBD")
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
