# DAQview
# Copyright 2018-2023 Airborne Engineering Ltd

__author__ = "Airborne Engineering Ltd"

import os
import sys
import time
import signal
import logging
import argparse
import datetime
import textwrap
import traceback
import importlib_resources
import platformdirs
from PySide6 import QtWidgets, QtGui, QtDBus
from logging.config import dictConfig

# Prevent OpenBLAS starting threads to do work.
# If unset, when pyqtgraph makes certain numpy calls as part of updating chart
# data, numpy calls into OpenBLAS which spawns threads. Unfortunately this
# hits pathological design choices in OpenBLAS which cause the threads to
# spinlock on syscalling sched_yield, going to 100% CPU usage. Disabling
# threading in OpenBLAS causes it to perform the operations in-thread,
# which is plenty fast and prevents the problem. The environment variable
# must be set before numpy is first imported.
os.environ['OPENBLAS_NUM_THREADS'] = '1'

# Bypass flake8 for these imports to avoid warning about imports not
# at top of file (since environment variable setting above is required
# prior to import, as these imports pull in numpy).
from daqview.models.server import Server                # noqa
from daqview.models.preferences import Preferences      # noqa
from daqview.views.main_window import MainWindow        # noqa

logger = logging.getLogger(__name__)


def setup_logging():
    dt = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    logpath = platformdirs.user_log_path("daqview", "AEL", ensure_exists=True)
    logfile = logpath / f"daqview-{dt}.log"
    cfg = dict(
        version=1,
        disable_existing_loggers=False,
        formatters={
            'standard': {
                'format': '%(asctime)s %(name)-26s %(levelname)-8s %(message)s'
            }
        },
        handlers={
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': logging.INFO
            },
            'file': {
                'class': 'logging.handlers.WatchedFileHandler',
                'formatter': 'standard',
                'level': logging.INFO,
                'filename': logfile,
            },
        },
        root={
            'handlers': ['console', 'file'],
            'level': logging.INFO}
    )
    dictConfig(cfg)
    logger.info("Logging to '%s'", logfile)


def parse_args():
    parser = argparse.ArgumentParser(prog="daqview", description="DAQview")
    parser.add_argument(
        '--install', action='store_true',
        help="Install DAQview application files")
    parser.add_argument(
        '--server',
        help="Server to connect to at startup, in format host:port")
    parser.add_argument(
        '--zero-timestamps', action='store_true',
        help="Automatically zero timestamps on startup")
    parser.add_argument(
        '--layout',
        help="Layout file to open at startup")
    parser.add_argument(
        'dataset', nargs="*", help="Dataset files to open at startup")
    return parser.parse_args()


def exception_hook(exc_type, exc_value, tb_obj):
    error = "An unhandled error occurred. Error details:\n"
    error += "{}: {}\n".format(str(exc_type), str(exc_value))
    error += "".join(traceback.format_tb(tb_obj))
    logger.error("An unhandled error occurred: %s", error)
    # Add a short sleep to prevent error overload in a tight loop
    time.sleep(0.1)
    errbox = QtWidgets.QMessageBox()
    errbox.setText(error)
    errbox.exec_()


def install_application_files():
    if sys.platform.startswith('linux'):
        app_path = platformdirs.user_data_path('applications')
        if not os.path.isdir(app_path):
            logger.warning("No such directory '%s'", app_path)
            return
        logger.info("Installing application files for Linux...")
        app_path /= 'daqview.desktop'
        with open(app_path, 'w') as f:
            logger.info("Writing '%s'", app_path)
            f.write(textwrap.dedent("""\
                [Desktop Entry]
                Version=1.1
                Type=Application
                Terminal=false
                Exec=daqview %F
                Name=DAQview
                Comment=View live and historic DAQ data
                Keywords=hdf5;h5;hdf;daq;ael
                Icon=daqview
                MimeType=application/x-hdf
                Categories=Science
                DBusActivatable=true
                """))

        icon_path = platformdirs.user_data_path('icons', ensure_exists=True)
        icon_path = icon_path / 'hicolor' / 'scalable' / 'apps'
        if not os.path.isdir(icon_path):
            os.makedirs(icon_path)
        icon_path /= 'daqview.svg'
        with open(icon_path, 'wb') as f:
            logger.info("Writing '%s'", icon_path)
            ref = importlib_resources.files(__name__) / 'daqview.svg'
            with importlib_resources.as_file(ref) as path:
                f.write(open(path, 'rb').read())

        dbus_path = platformdirs.user_data_path('dbus-1', ensure_exists=True)
        dbus_path /= 'services'
        if not os.path.isdir(dbus_path):
            os.mkdir(dbus_path)
        dbus_path /= 'daqview.service'
        with open(dbus_path, 'w') as f:
            logger.info("Writing '%s'", dbus_path)
            f.write(textwrap.dedent("""\
                [D-BUS Service]
                Name=uk.co.ael.daqview
                Exec=daqview
                """))
    else:
        logger.error("Don't know how to install on platform '%s'", sys.platform)


def main():
    # Parse args early in case we need to just print usage and exit
    args = parse_args()

    setup_logging()
    logger.info("DAQview starting up")

    if args.install:
        install_application_files()
        return

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    prefs = Preferences()

    app = QtWidgets.QApplication(["DAQview"] + sys.argv[1:])
    app.prefs = prefs
    app.datasets = {}
    app.server = Server()
    app.args = args
    QtGui.QIcon.setThemeName("oxygen")

    ref = importlib_resources.files(__name__) / 'daqview.svg'
    with importlib_resources.as_file(ref) as path:
        app.setWindowIcon(QtGui.QIcon(str(path)))

    main_window = MainWindow()
    main_window.resize(1024, 768)
    policy = QtWidgets.QSizePolicy.Policy.Expanding
    main_window.setSizePolicy(policy, policy)
    main_window.show()

    bus = QtDBus.QDBusConnection.sessionBus()
    bus.registerService('uk.co.ael.daqview')
    bus.registerObject('/uk/co/ael/daqview', main_window)

    # Handle all subsequent uncaught exceptions
    sys.excepthook = exception_hook

    if app.args.server:
        app.server.connect_to_host(app.args.server)

    if app.args.zero_timestamps:
        app.server.live_data.zero_timestamps()

    if app.args.layout:
        main_window.open_layout(fname=app.args.layout)

    if app.args.dataset:
        main_window.open_datasets(fnames=app.args.dataset)

    sys.exit(app.exec_())
