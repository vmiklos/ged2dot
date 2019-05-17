#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

try:
    import sys
    import traceback

    import uno  # type: ignore  # Cannot find module named 'uno'
    import unohelper  # type: ignore  # Cannot find module named 'unohelper'
    from com.sun.star.beans import PropertyValue  # type: ignore  # Cannot find module named 'com.sun.star.beans'

    # Insert our own directory into sys.path. Normally that's already done, and
    # even if it's not, __file__ is defined, so it's trivial to do so. But
    # that's not the case here. Seems the only way to do this is to read a
    # configuration value, where %origin% gets replaced with the directory
    # we're interested in.
    ctx = uno.getComponentContext()
    configurationProvider = ctx.ServiceManager.createInstance('com.sun.star.configuration.ConfigurationProvider')
    value = PropertyValue()
    value.Name = 'nodepath'
    value.Value = 'hu.vmiklos.libreoffice.Draw.GedcomImportFilter.Settings/Tokens'
    configurationAccess = configurationProvider.createInstanceWithArguments('com.sun.star.configuration.ConfigurationAccess', (value,))
    origin = configurationAccess.Origin
    # Actually the returned value still contains 'vnd.sun.star.expand:$UNO_USER_PACKAGES_CACHE', let's expand that.
    expander = ctx.getValueByName('/singletons/com.sun.star.util.theMacroExpander')
    url = expander.expandMacros(origin).replace('vnd.sun.star.expand:', '')
    path = unohelper.fileUrlToSystemPath(url)
    sys.path.insert(0, path)

    import dialog
    import filter

    g_ImplementationHelper = unohelper.ImplementationHelper()
    g_ImplementationHelper.addImplementation(dialog.GedcomDialog, "hu.vmiklos.libreoffice.comp.Draw.GedcomImportDialog", ("com.sun.star.ui.dialogs.FilterOptionsDialog",))
    g_ImplementationHelper.addImplementation(filter.GedcomImport, "hu.vmiklos.libreoffice.comp.Draw.GedcomImportFilter", ("com.sun.star.document.ImportFilter",))
except Exception:
    traceback.print_exc(file=sys.stderr)

# vim:set shiftwidth=4 softtabstop=4 expandtab:
