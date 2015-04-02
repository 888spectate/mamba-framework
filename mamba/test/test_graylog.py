
# Copyright (c) 2012 - Adam Drakeford <adamdrakeford@gmail.com>
# See LICENSE for more details

"""Tests for mamba.application.app
"""
from mock import Mock, patch
from twisted.trial import unittest

from mamba.core import GNU_LINUX
from mamba.application import app


class MockGraylogObserver(Mock):

    def start(self):
        pass


class MockUDPGelfProtocol(Mock):
    pass


class mock_udp(Mock):
    UDPGelfProtocol = MockUDPGelfProtocol


class GraylogIntegrationTest(unittest.TestCase):

    def setUp(self):
        if not app.txgraylog_installed:
            raise unittest.SkipTest(
                'txGraylog is not installed. '
                'Install with "pip install txGraylog"'
            )

        class DummyOptions:
            name = 'graylog_test'
            graylog = {
                "active": True,
                "host": "127.0.0.1",
                "port": 12201
            }

        self.patches = [
            patch('mamba.application.app.udp', mock_udp),
            patch(
                'mamba.application.app.GraylogObserver',
                MockGraylogObserver
            ),
            patch(
                'mamba.application.app.udp.UDPGelfProtocol',
                MockUDPGelfProtocol
            )
        ]
        [p.start() for p in self.patches]
        app.Mamba().initialized = False
        self.app = app.Mamba(DummyOptions())
        self._cleanup()

    def tearDown(self):
        [p.stop() for p in self.patches]

    def _cleanup(self):
        if GNU_LINUX:
            self.addCleanup(
                self.app.managers.get('controller').notifier.loseConnection
            )
            self.addCleanup(
                self.app.managers.get('model').notifier.loseConnection
            )

    def test_graylog_values(self):
        self.assertEqual(self.app.graylog, {
            "active": True,
            "host": "127.0.0.1",
            "port": 12201
        })
        self.assertTrue(app.txgraylog_installed)
        self._cleanup()

    def test_graylog_parameter_override(self):
        self.assertEqual(
            MockUDPGelfProtocol.parameter_override, {'tag': 'graylog_test'}
        )
        self._cleanup()

    def test_init_graylog_not_called_when_dev_enabled(self):
        self.app.development = True
        with patch.object(app.Mamba, '_init_graylog2') as mock:
            self.app._handle_logging()
            mock.assert_not_called()
        self._cleanup()

    def test_init_graylog_not_called_when_dev_disabled(self):
        self.app.development = False
        with patch.object(app.Mamba, '_init_graylog2') as mock:
            self.app._handle_logging()
            mock.assert_called()
        self._cleanup()

    def test_graylog_observer_called(self):
        self.app.development = False
        with patch.object(
                MockGraylogObserver, '__init__', return_value=None) as mock:
            self.app._handle_logging()
            mock.assert_called_with(MockUDPGelfProtocol, "127.0.0.1", 12201)
        self._cleanup()
