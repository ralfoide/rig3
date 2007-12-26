"""
The rig.site namespace contains the implementation of the site generators.
There's one site generator per kind of template. They should derive from rig.SiteBase.

For a template "xyz", the file is rig/site/site_xyz.py and the class is
rig.site.SiteXyz(rig.site_base.SiteBase).
"""

#------------------------
def CreateSite(log, dry_run, settings):
    """
    """
    theme = settings.theme
    if theme == "default":
        from rig.site.site_default import SiteDefault
        return SiteDefault(log, dry_run, settings)
    elif theme == "ralf":
        from rig.site.site_ralf import SiteRalf
        return SiteRalf(log, dry_run, settings)
    elif theme == "magic":
        from rig.site.site_magic import SiteMagic
        return SiteMagic(log, dry_run, settings)
    else:
        raise NotImplementedError("Theme %s is not implemented" % theme)
