
# Copyright (c) 2012 - Oscar Campos <oscar.campos@member.fsf.org>
# See LICENSE for more details

"""
Tests for mamba.core.module
"""

from mock import patch

from twisted.trial import unittest

from mamba.core import GNU_LINUX
from mamba.core.interfaces import INotifier
from mamba.core.module import ModuleManager


class ModuleManagerTest(unittest.TestCase):
    """
    This is a pure base class so it's hardly tested in its inheritors
    """

    MODULE_PATH_PREFIX = 'mamba.core.module'


    @classmethod
    def _get_full_mock_path(cls, *args):
        return '.'.join([cls.MODULE_PATH_PREFIX] + list(args))

    def setUp(self):
        if not GNU_LINUX:
            raise unittest.SkipTest('File monitoring only available on Linux')

        self.inotify_patch = patch(self._get_full_mock_path('inotify'))
        self.setup_patch = patch(self._get_full_mock_path('ModuleManager', 'setup'))
        self.notifier_patch = patch(
            self._get_full_mock_path('ModuleManager', 'notifier'),
            create=True,
        )
        self.module_store_patch = patch(
            self._get_full_mock_path('ModuleManager', '_module_store'),
            create=True,
        )
        self.config_patch = patch(self._get_full_mock_path('config', 'Application'))

        self.inotify_patch.start()
        self.setup_patch.start()
        self.notifier_patch.start()
        self.module_store_patch.start()
        self.config_mock = self.config_patch.start()

    def tearDown(self):
        self.inotify_patch.stop()
        self.setup_patch.stop()
        self.notifier_patch.stop()
        self.module_store_patch.stop()
        self.config_patch.stop()

    def test_module_manager_implements_inotifier(self):
        self.assertTrue(INotifier.implementedBy(ModuleManager))

    def test_module_manager_reload_enabled(self):
        self.config_mock.return_value.reload_enabled = True

        mm = ModuleManager()
        self.assertTrue(mm.reload_enabled)
        self.assertTrue(mm._watching)
        mm.notifier.startReading.assert_called_once()
        mm.notifier.watch.assert_called_once()

    def test_module_manager_reload_disabled(self):
        self.config_mock.return_value.reload_enabled = False

        mm = ModuleManager()
        self.assertFalse(mm.reload_enabled)
        self.assertFalse(mm._watching)
        mm.notifier.startReading.assert_not_called()
        mm.notifier.watch.assert_not_called()
