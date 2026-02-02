import os
import json
import logging
import configparser
import platformdirs

logger = logging.getLogger(__name__)

PREF_DIR = platformdirs.user_config_dir("daqview", "AEL")
PREF_FILE = "daqview.ini"

NUM_RECENT = 10


class Preferences:
    def __init__(self):
        self.path = os.path.join(PREF_DIR, PREF_FILE)
        if os.path.isfile(PREF_DIR):
            logger.info("Detected old config file at '%s', migrating...", PREF_DIR)
            old_config = open(PREF_DIR).read()
            os.unlink(PREF_DIR)
            os.mkdir(PREF_DIR)
            with open(self.path, "w") as f:
                f.write(old_config)
        self.config = configparser.ConfigParser()
        if os.path.isfile(self.path):
            logger.info("Reading preferences from %s", self.path)
            self.config.read(self.path)
        else:
            logger.info("No preferences file found: %s", self.path)
        if 'DAQview' not in self.config:
            self.config['DAQview'] = {}
        self.prefs = self.config['DAQview']

    def get_last_server(self):
        return self.prefs.get("last_server", "localhost:1736")

    def set_last_server(self, server):
        self.prefs["last_server"] = server
        self.save()

    def add_recent(self, name, item):
        logger.info("Adding '%s' to list of recent %s", item, name)
        recents = self.get_recents(name)
        if item in recents:
            # Move to end of recents list
            recents.append(recents.pop(recents.index(item)))
        else:
            recents.append(item)
        if len(recents) > NUM_RECENT:
            recents = recents[-NUM_RECENT:]
        self.prefs[f"recent_{name}"] = json.dumps(recents)
        self.save()

    def get_recents(self, name):
        recents = self.prefs.get(f"recent_{name}", "[]")
        return json.loads(recents)

    def add_recent_derived_channel(self, ch):
        self.add_recent("derived_channels", ch)

    def get_recent_derived_channels(self):
        return self.get_recents("derived_channels")

    def add_recent_layout(self, layout):
        self.add_recent("layouts", str(layout))

    def get_recent_layouts(self):
        return self.get_recents("layouts")

    def add_recent_dataset(self, dataset):
        self.add_recent("datasets", str(dataset))

    def get_recent_datasets(self):
        return self.get_recents("datasets")

    def set_recent_sequencing_cfg(self, cfg):
        logger.info("Saving sequencing configuration")
        self.prefs["sequencing"] = json.dumps(cfg)
        self.save()

    def get_recent_sequencing_cfg(self):
        return json.loads(self.prefs.get("sequencing", "{}"))

    def get_use_server_colours(self):
        return self.prefs.get("use_server_colours", False)

    def set_use_server_colours(self, use_server_colours):
        self.prefs["use_server_colours"] = use_server_colours
        self.save()

    def set_daqng_data_path(self, path):
        self.prefs["daqng_data_path"] = path
        self.save()

    def get_daqng_data_path(self):
        if "daqng_data_path" in self.prefs:
            return self.prefs["daqng_data_path"]
        else:
            daqng_pth = os.path.join(
                PREF_DIR, os.path.pardir, "daqng", "daqng_gui_setup.json")
            with open(daqng_pth) as f:
                daqng_cfg = json.load(f)
                return daqng_cfg.get("data_path")

    def save(self):
        if not os.path.isdir(PREF_DIR):
            try:
                os.mkdir(PREF_DIR)
            except FileNotFoundError:
                logger.warning("Could not create preferences folder %s", PREF_DIR)
                return
            except FileExistsError:
                logger.warning(
                    "Could not create preferences folder: %s already exists",
                    PREF_DIR
                )
                return
        try:
            with open(self.path, "w") as f:
                logger.info("Saving preferences to %s", self.path)
                self.config.write(f)
        except FileNotFoundError:
            logger.warning("Couldn't create preferences file %s", self.path)
