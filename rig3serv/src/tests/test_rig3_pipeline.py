#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Rig3 site generation.

This is not a live test. It simulates the various steps of the "pipeline"
from rig3, manually. It's more designed to be a concrete example of what's
going on and depends a lot on implementation details of Rig3 and SiteBase
to kind of mirror what's going on behind the scene.

Part of Rig3.
Copyright (C) 2007-2009 ralfoide gmail com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
__author__ = "ralfoide gmail com"

import types
import os

from tests.rig_test_case import RigTestCase
from rig3 import Rig3
from rig.site_base import SiteBase
from rig.site import CreateSite

_DEST_DIR = "test_dest"  # in testdata dir

#------------------------
class RenderPipeline(RigTestCase):

    def setUp(self):
        self._pwd = os.getcwd()
        self._testdata = self.getTestDataPath()
        # all paths are relative to the testdata dir
        os.chdir(self._testdata)
        # cleanup output and make sure it's not there anymore
        self.RemoveDir(_DEST_DIR)
        self.assertFalse(os.path.exists(_DEST_DIR))
        os.mkdir(_DEST_DIR)
        self.assertTrue(os.path.exists(_DEST_DIR))

    def tearDown(self):
        os.chdir(self._pwd)

    def testRig3Pipeline(self):
        """
        Tests the "outer" rig3 pipeline, that is processing an RC config file,
        processing the sites and invoking the process of the source items,
        categories and page generation.

        This looks at making sure the proper methods are invoked as many times
        as expected rather than actually looking at the generated data.
        """

        # First parse the args
        test = self
        r = Rig3()
        t = self._testdata
        rc = os.path.join(t, "z_last_render_testdata.rc")
        args = [ "rig3", "-c", rc, "--force" ]
        r.ParseArgs(args)

        def PatchProcessSites(self):
            # ProcessSites() will now create the site and process it.
            # Let's do that manually here
            s = r._sites_settings

            test.assertListEquals(
                 [ "test_default", "test_magic" ],
                 s.Sites())

            # We'll test only the first site
            site_id = "test_default"
            sis = s.GetSiteSettings(site_id)
            site = CreateSite(r._log,
                              r._dry_run,
                              r._force,
                              sis)

            # the testdata.rc has 2 sources lines with 3 sources types
            # defined on each line (dir, file and blog)
            test.assertEquals(6, len(sis.source_list))

            # site.Process() should invoke _ProcessSourceItems()
            # (for each each source list) and then _CollectCategories()
            # once, and then finally GeneratePages()... lets patch them to
            # inject counters.
            site.old_ProcessSourceItems = site._ProcessSourceItems
            site.old_CollectCategories = site._CollectCategories
            site.old_GeneratePages = site.GeneratePages

            site.count_ProcessSourceItems = 0
            site.count_CollectCategories = 0
            site.count_GeneratePages = 0

            def Patch_ProcessSourceItems(self, source, site_items, dups):
                self.count_ProcessSourceItems += 1
                return self.old_ProcessSourceItems(source, site_items, dups)

            def Patch_CollectCategories(self, site_items):
                self.count_CollectCategories += 1
                return self.old_CollectCategories(site_items)

            def Patch_GeneratePages(self, categories, site_items):
                self.count_GeneratePages += 1
                return self.old_GeneratePages(categories, site_items)

            site._ProcessSourceItems = types.MethodType(Patch_ProcessSourceItems, site, SiteBase)
            site._CollectCategories = types.MethodType(Patch_CollectCategories, site, SiteBase)
            site.GeneratePages = types.MethodType(Patch_GeneratePages, site, SiteBase)
            site.Process()

            test.assertEquals(6, site.count_ProcessSourceItems)
            test.assertEquals(1, site.count_CollectCategories)
            test.assertEquals(1, site.count_GeneratePages)

            site.Dispose()

        # Rig3.Run() loads site settings then invokes ProcessSites().
        # we use monkey patching to invoke PatchProcessSites() from Run()
        # instead.
        r.ProcessSites = types.MethodType(PatchProcessSites, r, Rig3)
        r.Run()

        # Finally close the Rig3 instance
        r.Close()



#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
