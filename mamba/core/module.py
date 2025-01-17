# -*- test-case-name: mamba.core.test.test_module -*-
# Copyright (c) 2012 Oscar Campos <oscar.campos@member.fsf.org>
# See LICENSE for more details

"""
.. module:: module
    :platform: Linux
    :synopsys: Loadable python modules base class

.. moduleauthor:: Oscar Campos <oscar.campos@member.fsf.org>

"""

import gc
import re
import traceback
from collections import OrderedDict

from twisted.python import filepath, rebuild

from mamba.core import GNU_LINUX
from mamba.utils import log, config

if GNU_LINUX:
    from zope.interface import implements
    from twisted.internet import inotify
    from twisted.python._inotify import INotifyError

    from mamba.core.interfaces import INotifier

from mamba.plugin import ExtensionPoint
from mamba.utils import filevariables, output


class ModuleError(Exception):
    """ModuleError Exception"""
    pass


class ModuleManager(object):
    """
    Every module manager class inherits from me. I setup a
    :class:`twisted.internet.inotify.INotify` object in my
    :attr:`self._module_store` in order to perform auto reloads
    """
    if GNU_LINUX:
        implements(INotifier)

    def __init__(self):
        # Initialize the ExtensionLoader parent object
        super(ModuleManager, self).__init__()
        self.pattern = re.compile(r'[^_?]\.py$', re.IGNORECASE)

        self._modules = OrderedDict()
        self._extension = '.py'
        self.reload_enabled = config.Application().reload_enabled

        if GNU_LINUX:
            # Create and setup the Linux iNotify mechanism
            self.notifier = inotify.INotify()
            self._watching = False
            if self.reload_enabled:
                self.notifier.startReading()
                try:
                    self.notifier.watch(
                        filepath.FilePath(self._module_store),
                        callbacks=[self._notify]
                    )
                    self._watching = True
                except INotifyError:
                    self._watching = False

        # Start the loading process
        self.setup()

    def setup(self):
        """Setup the loder and load the Mamba plugins
        """

        self._load_from_package(self._module_store)

    def load(self, filename):
        """Loads a Mamba module

        :param filename: the module filname
        :type filename: str
        """

        if type(filename) is not str:
            filename = filename.path

        module_name = filepath.splitext(filepath.basename(filename))[0]
        module_path = self._modulize_path(filename).split('.py')[0]

        if module_name in self._modules:
            return

        objs = [module_name.capitalize()]
        temp_module = __import__(module_path, globals(), locals(), objs)
        # instance the object
        try:
            temp_object = getattr(temp_module, objs[0])()
        except AttributeError:
            for member in dir(temp_module):
                tmp_member = getattr(temp_module, member)

                if (type(tmp_member) is ExtensionPoint
                        or type(tmp_member).__name__ == 'MambaStorm'):
                    # make sure we are not instantiating incorrect objects
                    if tmp_member.__module__ == temp_module.__name__:
                        temp_object = tmp_member()
                        break

        temp_object.loaded = True

        self._modules.update({
            module_name: {
                'object': temp_object,
                'module': temp_module,
                'module_path': module_path
            }
        })

    def reload(self, module):
        """Reload a controller module

        :param module: the module to reload
        :type module: str
        """

        module_store = self.lookup(module)
        object = module_store.get('object')
        tmp_module = module_store.get('module')
        if object is None or object.loaded is False:
            raise ModuleError(
                'Tried to reload %s that is not yet loaded' % module)

        log.info(
            '{}: {} {}'.format(
                output.green('Reloading module'),
                object.__class__.__name__, object
            )
        )

        try:
            rebuild.rebuild(tmp_module, False)
        except Exception as error:
            log.info(
                '{}: {}\n{}'.format(
                    output.brown('Error reloading module'),
                    error,
                    traceback.format_exc()[:-1]
                )
            )
        finally:
            object_name = object.__class__.__name__
            del self._modules[module]['object']
            gc.collect()
            temp_object = getattr(tmp_module, object_name)()
            temp_object.loaded = True
            self._modules[module]['object'] = temp_object

    def lookup(self, module):
        """Find and return a controller from the pool

        :param module: the module to lookup
        :type module: str
        """

        return self._modules.get(module, dict())

    def length(self):
        """Returns the controller pool length
        """

        return len(self._modules)

    def is_valid_file(self, file_path):
        """Must be implemented by subclasses

        :param file_path: the filepath to check
        :type file_path: :class: `twisted.python.filepath.FilePath`
        """
        raise NotImplementedError("Not implemented yet!")

    def _notify(self, ignore, file_path, mask):
        """Notifies the changes on resources file_path
        """

        if not GNU_LINUX:
            return

        if mask == inotify.IN_MODIFY:
            if not self.is_valid_file(file_path):
                return

            module = filepath.splitext(file_path.basename())[0]
            if module in self._modules:
                self.reload(module)

        if mask == inotify.IN_CREATE:
            if file_path.exists():
                if self.is_valid_file(file_path):
                    self.load(file_path)

    def _valid_file(self, file_path, file_type):
        """Check if a file is a valid Mamba file
        """

        basename = filepath.basename(file_path)
        if filepath.splitext(basename)[1] == self._extension:
            filevars = filevariables.FileVariables(file_path)
            if filevars.get_value('mamba-file-type') == file_type:
                return True

        return False

    def _modulize_store(self):
        """Return a modularized version of the module store path
        """

        if self._package is not None:
            # this is a shared package
            retval = '{}{}'.format(
                self._package,
                self._module_store.rsplit(self._package, 1)[1]
            ).replace('/', '.')
        else:
            retval = self._module_store.replace('/', '.')

        return retval

    def _modulize_path(self, path):
        """Return a modularied version of the given path
        """

        path = filepath.joinpath(
            self._module_store, path.split(self._module_store + '/')[1])
        if self._package is not None:
            # seems like this is a package
            retval = '{}{}'.format(
                self._package,
                path.rsplit(self._package, 1)[1]
            ).replace('/', '.')
        else:
            retval = path.replace('/', '.')

        return retval

    def _load_from_package(self, package=''):
        """Load modules from the given package
        """

        try:
            for f in filepath.listdir(package):
                filename = filepath.joinpath(package, f)
                fp = filepath.FilePath(filename)
                if fp.isdir():
                    self._load_from_package(filename)
                    continue
                if self.pattern.search(filename) is not None:
                    if self.is_valid_file(filename):
                        self.load(filename)
        except OSError:
            pass


__all__ = ['ModuleError', 'ModuleManager']
