"""
The rig.site namespace contains the implementation of the site generators.
There's one site generator per kind of template.
They should derive from rig.SiteBase.

The pattern for files in this directory is <site_theme.py>.

E.g. for a template "xyz", the file is rig/site/site_xyz.py and the class is
rig.site.SiteXyz(rig.site_base.SiteBase).
"""

from rig.site.site_default import SiteDefault
from rig.site.site_plain import SitePlain
from rig.site.site_ralf import SiteRalf
from rig.site.site_magic import SiteMagic

THEMES = {
    "default": SiteDefault,
    "plain":   SitePlain,
    "ralf":    SiteRalf,
    "magic":   SiteMagic
}

#------------------------
def CreateSite(log, dry_run, settings):
    """
    Instantiate the site generator for a specific template.
    """
    theme = settings.theme
    if theme in THEMES:
        return THEMES[theme](log, dry_run, settings)
    else:
        err = "Theme '%s' is not defined. Known themes: %s" % (
              theme, THEMES.keys())
        log.Error(err)
        raise NotImplementedError(err)
