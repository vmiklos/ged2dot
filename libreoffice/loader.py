#!/usr/bin/env python3
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

"""Registers the dialog and importer modules as an extension."""

import traceback
try:
    import sys

    import uno  # type: ignore  # pylint: disable=import-error
    import unohelper  # type: ignore  # pylint: disable=import-error
    from com.sun.star.beans import PropertyValue  # type: ignore  # pylint: disable=import-error

    # Insert our own directory into sys.path. Normally that's already done, and
    # even if it's not, __file__ is defined, so it's trivial to do so. But
    # that's not the case here. Seems the only way to do this is to read a
    # configuration value, where %origin% gets replaced with the directory
    # we're interested in.
    CTX = uno.getComponentContext()
    CONFIGURATION_PROVIDER = CTX.ServiceManager.createInstance('com.sun.star.configuration.ConfigurationProvider')
    VALUE = PropertyValue()
    VALUE.Name = 'nodepath'
    VALUE.Value = 'hu.vmiklos.libreoffice.Draw.GedcomImportFilter.Settings/Tokens'
    SERVICE_NAME = "com.sun.star.configuration.ConfigurationAccess"
    CONFIGURATION_ACCESS = CONFIGURATION_PROVIDER.createInstanceWithArguments(SERVICE_NAME, (VALUE,))
    ORIGIN = CONFIGURATION_ACCESS.Origin
    # Actually the returned value still contains 'vnd.sun.star.expand:$UNO_USER_PACKAGES_CACHE', let's expand that.
    EXPANDER = CTX.getValueByName('/singletons/com.sun.star.util.theMacroExpander')
    URL = EXPANDER.expandMacros(ORIGIN).replace('vnd.sun.star.expand:', '')
    PATH = unohelper.fileUrlToSystemPath(URL)
    sys.path.insert(0, PATH)

    import dialog
    import importer

    # pythonloader.py has this name hardcoded
    # pylint: disable=invalid-name
    g_ImplementationHelper = unohelper.ImplementationHelper()
    g_ImplementationHelper.addImplementation(dialog.GedcomDialog,
                                             "hu.vmiklos.libreoffice.comp.Draw.GedcomImportDialog",
                                             ("com.sun.star.ui.dialogs.FilterOptionsDialog",))
    g_ImplementationHelper.addImplementation(importer.GedcomImport,
                                             "hu.vmiklos.libreoffice.comp.Draw.GedcomImportFilter",
                                             ("com.sun.star.document.ImportFilter",))
# pylint: disable=broad-except
except Exception:
    traceback.print_exc(file=sys.stderr)

# vim:set shiftwidth=4 softtabstop=4 expandtab:
