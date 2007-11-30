"""
The rig.template namespaces contains the implementation for the Rig3 Template parser.

It can parse a template file with tags and variables and generate the rendered text.
Templates can use variable replacement with URL or HTML encoding, condtional constructs,
for-loops and free python expression evaluation.

Although mainly used for HTML, the template syntax is generic and can be
used for anything else, such as CSS or even regular text.

See the class Template in rig/template/template.py for more information. 
"""