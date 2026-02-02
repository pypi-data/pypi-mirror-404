import os
import copy
import json
import struct
import socket
import logging
import datetime
import collections.abc
import urllib.parse
from itertools import pairwise

import yaml
import numexpr
import numpy as np
import scipy.ndimage


logger = logging.getLogger(__name__)


TABLE_WR_REQUEST = 13
TABLE_WR_RESPONSE = 14
TABLE_RD_REQUEST = 15
TABLE_RD_RESPONSE = 16
TABLE_WR_V2_REQUEST = 62
TABLE_WR_V2_RESPONSE = 63
ERROR_RESPONSE = 23
ERROR_UNIMPLEMENTED = 1
DAQ_SEQ_TYPE_VALVE = 1
DAQ_SEQ_TYPE_AMV = 2
DAQ_SEQ_TYPE_AOUT = 3
DAQ_SEQ_TYPE_CAN = 4
DAQ_SEQ_TYPE_UART = 5
DAQ_SEQ_ID_RUN = 1
DAQ_SEQ_ID_STOP = 2
DAQ_AMV_PROFILE_MODE_DIST = 1
DAQ_AMV_PROFILE_MODE_OL = 2
DAQ_AMV_PROFILE_MODE_CL = 3
DAQ_SEQ_FLAG_BIT_USE_STOP_VALUE = 1 << 30
DAQ_SEQ_FLAG_BIT_ALLOW_OVERRIDE = 1 << 31

AMV_PROFILE_TYPES = {
    "profile_dist": DAQ_AMV_PROFILE_MODE_DIST,
    "profile_ol": DAQ_AMV_PROFILE_MODE_OL,
    "profile_cl": DAQ_AMV_PROFILE_MODE_CL,
}


class Config:
    """
    Load and process the entire configuration file.
    """

    def __init__(self, path):
        self.path = path
        try:
            with open(path) as f:
                cfg = yaml.safe_load(f)
        except (IOError, OSError) as e:
            logger.warning("Error opening config file: %s", e)
            self.daus = {}
            self.assigs = []
            self.roles = {}
            self.templates = []
            return

        self.cfg_daus = {d["dau"]: d for d in cfg.get("dau_assig", [])}
        self.cfg_assigs = cfg.get("assignments", [])
        self.cfg_roles = {a["role"]: a for a in self.cfg_assigs if "channel" in a}
        self.cfg_templates = cfg.get("templates", [])
        for tpl in self.cfg_templates:
            self._inherit_template(tpl)
        self.templates = [
            Template(t, self.cfg_daus, self.cfg_assigs, self.cfg_roles)
            for t in self.cfg_templates
        ]

    def __repr__(self):
        return f"<Config '{self.path}'>"

    def _inherit_template(self, tpl):
        assert "name" in tpl, "Template missing 'name'"
        for inherit in tpl.get("inherits", []):
            parent = [t for t in self.cfg_templates if t["name"] == inherit]
            assert len(parent) == 1, f"Can't find inheritance template {inherit}"
            parent = parent[0]
            assert "inherits" not in parent, "Can't inherit from a later template"
            logger.debug("Template %s inheriting from %s", tpl["name"], parent["name"])
            if "tzero_offset" not in tpl and "tzero_offset" in parent:
                tpl["tzero_offset"] = parent["tzero_offset"]
            assert (
                tpl["tzero_offset"] == parent["tzero_offset"]
            ), "Inherited template has different tzero_offset"
            for key in ("variables", "valves", "profiles", "daus"):
                if key not in tpl:
                    tpl[key] = []
            tpl_vars = {v["id"]: v for v in tpl["variables"]}
            for var in parent.get("variables", []):
                if var["id"] in tpl_vars:
                    logger.info("Not inheriting existing variable '%s'", var["id"])
                    continue
                tpl["variables"].append(var)
            for valve in parent.get("valves", []):
                tpl["valves"].append(valve)
            for profile in parent.get("profiles", []):
                tpl["profiles"].append(profile)
            for dau in parent.get("daus", []):
                tpl["daus"].append(dau)
        if "inherits" in tpl:
            del tpl["inherits"]


class Template:
    """
    One template loaded from the configuration file.

    The configuration file is a YAML file containing a mapping which may
    include a `templates` entry with a list of template configuration mappings.

    Each template entry contains:

    * `name`: String name for this template
    * `description`: Optional string description for this template
    * `tzero_offset`: Optional offset applied to sequence times, default 0.0
    * `inherit_only`: Optional boolean, if true the template cannot be used directly
    * `variables`: List of variable mappings, each containing:
        * `id`: String ID for variable used in expressions
        * `name`: String name for variable used for display
        * `description`: Optional string description for variable
        * `type`: Type of variable, default "float"
        * `units`: Optional string units for variable
        * `default`: Default value for variable
        * `decimals`: Number of decimal places to show, default 3
        * `step`: Adjustment step size, default 0.01
        * `minimum`: Minimum value, default 0.0
        * `maximum`: Maximum value, default 100.0
    * `profiles`: List of valve profiles, each containing:
        * `role`: role of this valve in the configuration file
        * `type`: one of `profile_dist`, `profile_ol`, `profile_cl`, or `profile_aout`
        * `scale_max`: the profile value corresponding to a full-scale output of 65535
        * `units`: optional string for value units
        * `dt_ms`: for legacy V1 tables, the timestep between generated points
        * `cutoff_freq`: for legacy V1 tables, the low-pass filter frequency
        * `initial_value`: optional starting value, default 0.0
        * `profile`: list of mappings defining the profile shape, each containing:
            * `type`: `corner`, `hold`, `ramp`, or `staircase`
            * `duration`, `time`, or `until`: time specifiers
            * `target`: value specifier
            * see block_corner/block_hold/block_ramp/block_staircase docs
    * `valves`: list of on/off valve sequences, each containing:
        * `role`: role of this valve in the configuration file
        * `run`: list of [start, stop] windows when this valve should be on
          during the main run sequence; omit `stop` on the final entry to
          leave the valve on after the sequence finishes.
        * `stop`: as per `run` but for the stop sequence
    * `daus`: for compatibiltiy with older config files, each entry gives
      an AMV profile with the keys from `profiles` and additionally
      a `dau` key with the DAU ID from the config file.
    """

    def __init__(self, cfg, cfg_daus, cfg_assigs, cfg_roles):
        self.name = cfg["name"]
        self.description = cfg.get("description", "")
        self.tzero_offset = cfg.get("tzero_offset", 0.0)
        self.inherit_only = cfg.get("inherit_only", False)
        self.variables = []
        self.cfg = cfg
        self.cfg_daus = cfg_daus
        self.cfg_assigs = cfg_assigs
        self.cfg_roles = cfg_roles
        for v in cfg.get("variables", []):
            self.variables.append(
                {
                    "id": v["id"],
                    "name": v["name"],
                    "description": v.get("description", ""),
                    "type": v.get("type", "float"),
                    "units": v.get("units", ""),
                    "default": v.get("default", 0.0),
                    "decimals": v.get("decimals", 3),
                    "step": v.get("step", 0.01),
                    "minimum": v.get("minimum", 0.0),
                    "maximum": v.get("maximum", 100.0),
                }
            )
        self.profiles = []
        profiles = list(cfg.get("profiles", []))
        # for compatibility with older configs that use a 'daus' list
        for dau in cfg.get("daus", []):
            # replace 'dau' with 'role', noting name will come from it too
            for assig in cfg_assigs:
                if assig.get("dau") == dau["dau"] and assig.get("channel") == 1:
                    dau["role"] = assig["role"]
                    break
            else:
                assert f"Couldn't find role matching DAU {dau['dau']}"
            assert dau["type"] in AMV_PROFILE_TYPES.keys()
            profiles.append(dau)
        for profile in profiles:
            self.profiles.append(
                {
                    "tzero_offset": self.tzero_offset,
                    "role": profile["role"],
                    "type": profile["type"],
                    "scale_max": float(profile["scale_max"]),
                    "units": profile.get("units", ""),
                    "dt_ms": profile.get("dt_ms", 1),
                    "cutoff_freq": profile.get("cutoff_freq", 500),
                    "initial_value": profile.get("initial_value", 0.0),
                    "profile": list(profile.get("profile", [])),
                    "stop_profile": list(profile.get("stop_profile", [])),
                }
            )
        self.valves = []
        for valve in cfg.get("valves", []):
            self.valves.append(
                {
                    "role": valve["role"],
                    "run": list(valve.get("run", [])),
                    "stop": list(valve.get("stop", [])),
                }
            )

    def __repr__(self):
        return f"<Template '{self.name}'>"

    def get_assig(self, role):
        return self.cfg_roles[role]

    def render(self, variables):
        """
        Given a concrete dictionary of variable values, render this template
        to complete sequences ready to display or load.
        """
        return RenderedTemplate(self, variables)


class RenderedTemplate:
    """
    Combine a template with a concrete set of variables to actually render
    specific values which can be plotted or loaded to a DAU.

    Contains a list of profiles and sequences which can be plotted, and a
    list of DAUs which can be loaded.
    """

    def __init__(self, template, variables):
        self.template = template
        self.variables = variables

        for v in template.variables:
            assert v["id"] in variables, f"Missing variable {v['id']}"
        self.daus = {d: Dau(template.cfg_daus[d]) for d in template.cfg_daus}

        max_durations = {}

        # Process all profiles in template and assign to relevant DAU
        self.profiles = []
        for profile in template.profiles:
            # fill in name and channel from role
            assig = template.get_assig(profile["role"])
            profile["name"] = assig["name"]
            profile["channel"] = assig["channel"]
            seq = ProfileSequence(profile, variables)
            for (k, d) in seq.durations().items():
                max_durations[k] = max(max_durations.get(k, 0.0), d)
            self.profiles.append(seq)
            self.daus[assig["dau"]].add_sequence(seq)

        # Process all valves, group by DAU, then generate sequences.
        self.sequences = []
        dau_valves = {}
        for valve in template.valves:
            assig = template.get_assig(valve["role"])
            valve["name"] = assig["name"]
            valve["channel"] = assig["channel"]
            if assig["dau"] not in dau_valves:
                dau_valves[assig["dau"]] = []
            dau_valves[assig["dau"]].append(valve)
        for dau in dau_valves:
            cfg = {
                "type": "sequence",
                "tzero_offset": template.tzero_offset,
                "sequence": dau_valves[dau],
            }
            seq = DigitalSequence(cfg, variables)
            for (k, d) in seq.durations().items():
                max_durations[k] = max(max_durations.get(k, 0.0), d)
            self.sequences.append(seq)
            self.daus[dau].add_sequence(seq)

        # Ensure all sequences have the same length.
        for profile in self.profiles:
            profile.extend(max_durations)
        for sequence in self.sequences:
            sequence.extend(max_durations)
        for dau in self.daus:
            self.daus[dau].max_durations = max_durations

    def generate_metadata(self):
        """
        Create the metadata dictionary and return it.
        """
        metadata = {
            "template": json.dumps(self.template.cfg),
            "template_variables": json.dumps(self.variables),
            "template_datetime": datetime.datetime.utcnow().isoformat() + "Z",
        }
        if "analysis_metadata" in self.template.cfg:
            analysis = copy.deepcopy(self.template.cfg["analysis_metadata"])
            seq = Sequence(self.variables)
            analysis = seq.template_value(analysis)
            metadata["analysis_metadata"] = json.dumps(analysis)
        return metadata

    def write_json_metadata(self, data_path):
        """
        Write out a JSON metadata file containing information on the template
        in use and its variables.

        If `analysis_metadata` is specified in the template, it is filled in
        using `variables` and also written out.
        """
        metadata = self.generate_metadata()
        json_path = os.path.join(data_path, "metadata.json")

        # If the JSON file already exists, open it and overwrite the fields
        # relevant to sequencing.
        if os.path.isfile(json_path):
            with open(json_path) as f:
                logger.info("Loading existing JSON file '%s'", json_path)
                existing_metadata = json.load(f)
                existing_metadata.update(metadata)
                metadata = existing_metadata

        logger.info("Writing JSON data to '%s'", json_path)
        with open(json_path, "w") as f:
            json.dump(metadata, f)


class Dau:
    """
    A DAU with communication details and one or more sequences to load.
    """

    def __init__(self, cfg, table_size=8192, write_unimpl_ok=False):
        self.dau_id = cfg["dau"]
        self.name = cfg["name"]
        self.addr = cfg["addr"]
        url = urllib.parse.urlparse(self.addr)
        assert url.scheme == "udp", f"Unsupported URL scheme {url.scheme}"
        self.hostname = url.hostname
        self.port = url.port
        self.table_size = table_size
        self.sequences = []
        self.max_durations = {}
        self.write_unimpl_ok = write_unimpl_ok

    def add_sequence(self, seq):
        self.sequences.append(seq)

    def load(self):
        """
        Load all configured sequences to this DAU.
        """
        if not self.sequences:
            # Load a blank sequence to ensure boxes that aren't being used in
            # this template don't hold on to some old sequence from a previous
            # template. The blank sequence will cause valve controllers to
            # be "running" for the full duration but no valves change state.
            nop = NopSequence()
            nop.extend(self.max_durations)
            self.add_sequence(nop)
            self.write_unimpl_ok = True
        if self.check_v2_supported():
            data = b"".join([s.to_table(version=2) for s in self.sequences])
            header = struct.pack("<IIIII", 0, 0, 0, 0, 5 * 4 + len(data))
            self.write_table(header + data, 2)
        else:
            assert len(self.sequences) == 1, "V1 DAUs only support one sequence"
            data = self.sequences[0].to_table(version=1)
            self.write_table(data, 1)

    def check_v2_supported(self):
        """
        Check if v2 tables are supported, returning true or false.

        Executing this check will reset any stored sequences on the DAU.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(True)
        sock.settimeout(0.2)
        cmd = struct.pack("<HHH", TABLE_WR_V2_REQUEST, 2, 0)
        sock.sendto(cmd, (self.hostname, self.port))
        rx = sock.recv(128)
        hdr_type, hdr_len = struct.unpack("<HH", rx[:4])
        if hdr_type == TABLE_WR_V2_RESPONSE:
            logger.debug("DAU %s supports V2", self.name)
            return True
        else:
            logger.debug("DAU %s supports V1", self.name)
            return False

    def read_table(self, n):
        """
        Read table data from an AEL3xxx DAU.

        If specified, n is the number of bytes to read.
        """
        if n > self.table_size:
            logger.warning("Attempting to read more bytes than table size")
        logger.info("Reading %d bytes from DAU %s", n, self.name)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(True)
        sock.settimeout(0.2)
        offset = 0
        max_chunk_size = 256
        data = []
        while len(data) < n:
            bytes_left = n - len(data)
            chunk_size = min(bytes_left, max_chunk_size)
            cmd = struct.pack("<HHHH", TABLE_RD_REQUEST, 4, offset, chunk_size)
            sock.sendto(cmd, (self.hostname, self.port))
            rx = sock.recv(1024)
            logger.debug("Received %d bytes from DAU %s", len(rx), self.name)
            hdr_type, hdr_len = struct.unpack("<HH", rx[:4])
            if hdr_type != TABLE_RD_RESPONSE:
                raise RuntimeError(f"Unexpected packet {hdr_type} from DAU")
            data += struct.unpack(f"<{hdr_len}B", rx[4 : 4 + hdr_len])
            offset += hdr_len
        return bytes(data)

    def write_table(self, data, version, verify=True):
        """
        Write table data bytes to an AEL3xxx DAU using either version 1 or 2.

        Validates the returned CRC16 and raises an exception if doesn't match.
        """
        if version == 1:
            req = TABLE_WR_REQUEST
            resp = TABLE_WR_RESPONSE
        elif version == 2:
            req = TABLE_WR_V2_REQUEST
            resp = TABLE_WR_V2_RESPONSE
        else:
            raise ValueError("Table write version must be 1 or 2")
        if len(data) > self.table_size:
            logger.warning("Attempting to write more bytes than table size")
        logger.info("Writing %d bytes to DAU %s", len(data), self.dau_id)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(True)
        sock.settimeout(0.2)
        offset = 0
        max_chunk_size = 256
        while offset < len(data):
            bytes_left = len(data) - offset
            chunk_size = min(bytes_left, max_chunk_size)
            tx_data = data[offset : offset + chunk_size]
            tx_crc = self._crc16(tx_data)
            cmd = struct.pack(
                f"<HHH{chunk_size}B", req, 2 + chunk_size, offset, *tx_data
            )
            logger.debug("Sending %d bytes to DAU %s", chunk_size, self.name)
            sock.sendto(cmd, (self.hostname, self.port))
            rx = sock.recv(1024)
            hdr_type, hdr_len = struct.unpack("<HH", rx[:4])
            if hdr_type == ERROR_RESPONSE and rx[4] == ERROR_UNIMPLEMENTED:
                if self.write_unimpl_ok:
                    return
                raise RuntimeError("Table write unimplemented in DAU")
            elif hdr_type != resp:
                raise RuntimeError(f"Unexpected packet {hdr_type} from DAU")
            rx_crc = struct.unpack("<H", rx[4 : 4 + hdr_len])[0]
            assert tx_crc == rx_crc, "Invalid CRC received when writing table"
            offset += chunk_size
        if verify:
            rxdata = self.read_table(len(data))
            assert rxdata == data, "Readback verification unsuccessful"

    def _crc16(self, data):
        """
        Compute the DAU CRC16 over the provided data bytes.
        """
        table = [
            0x0000,
            0xCC01,
            0xD801,
            0x1400,
            0xF001,
            0x3C00,
            0x2800,
            0xE401,
            0xA001,
            0x6C00,
            0x7800,
            0xB401,
            0x5000,
            0x9C01,
            0x8801,
            0x4400,
        ]
        crc = 0xFFFF
        for byte in data:
            crc = ((crc >> 4) & 0x0FFF) ^ table[(crc ^ byte) & 0xF]
            crc = ((crc >> 4) & 0x0FFF) ^ table[(crc ^ (byte >> 4)) & 0xF]
        return crc ^ 0xFFFF


class Sequence:
    """
    A Sequence is a time series that will be loaded to a DAU.

    There are three types of Sequence:
        * ProfileSequence contains a single channel which is in principle
          real-valued, for example a massflow profile, an analogue output,
          or a variable valve position. Used for AMVs and AOUTs.
        * DigitalSequence contains up to 32 channels which are binary-valued,
          i.e. only ever on or off. Used for valve controllers.
        * NopSequence contains no data and ensures that any DAU it is written
          to will take no action when sequences are started.

    DAUs that support V2 tables may have more than one sequence loaded, for
    example a few analogue output channels and valves, while DAUs that support
    V1 tables may only have a single sequence (or a start and a stop
    DigitalSequence).

    `variables` is a dictionary of ID-to-value mappings for template variables.
    """

    def __init__(self, variables):
        self.variables = variables

    def to_display(self):
        """
        Returns a dict mapping sequence IDs (1=run, 2=stop) to lists of
        (time, value, role, name) tuples for all traces that should be
        displayed for this Sequence.
        """
        raise NotImplementedError

    def to_table(self, version=1):
        """
        Return the serialised bytes to load this sequence into a table
        of the specified version.

        For V1 tables this returns either an entire profile table (AMV) or
        entire sequence table (valves) including both run and stop sequences.

        For V2 tables this returns zero or more serialised sequences which
        will eventually be concatenated into a single table. The table header
        must be added separately.
        """
        assert version in (1, 2), "Version must be 1 or 2"
        if version == 1:
            return self._to_table_v1()
        elif version == 2:
            return self._to_table_v2()

    def durations(self):
        """
        Return a map of {seq_id: duration} with total durations in seconds.
        Note duration is overall length of sequence, but with a negative
        tzero_offset this is likely larger than the final time.
        """
        raise NotImplementedError

    def extend(self, durations):
        """
        Extend this sequence to maintain its final state so that the overall
        duration matches that specified in `durations` for each sequence ID.
        """
        raise NotImplementedError

    def _to_table_v1(self):
        raise NotImplementedError

    def _to_table_v2(self):
        raise NotImplementedError

    def template_str(self, s):
        """
        If `s` is a string wrapped by '{}', evaluate the contents using
        `variables` and return the result. Otherwise, returns `s` unchanged.
        """
        local = self.variables
        if isinstance(s, str) and s.startswith("{") and s.endswith("}"):
            return numexpr.evaluate(s[1:-1], local_dict=local, global_dict={})
        else:
            return s

    def template_value(self, v):
        """
        Recursively template `v`, replacing any strings wrapped in '{}' by
        their templated values.

        Mutates lists and dictionaries in-place; copy first if you need to
        preserve the original.
        """
        if isinstance(v, collections.abc.MutableSequence):
            for i in range(len(v)):
                v[i] = self.template_value(v[i])
        elif isinstance(v, collections.abc.MutableMapping):
            for k in v:
                v[k] = self.template_value(v[k])
        else:
            v = self.template_str(v)
            if isinstance(v, np.ndarray):
                v = float(v)
        return v

    def get_value(self, block, key, default=None):
        """
        Look up `key` in `block`, replacing with `default` if not found,
        expanding any strings wrapped in "{}".
        """
        v = block.get(key, default)
        return self.template_str(v)

    def get_float(self, block, key, default=None):
        """
        Look up `key` in `block`, replacing with `default` if not found,
        expanding any strings wrapped in "{}", and return as a float.
        """
        return float(self.get_value(block, key, default))

    def get_int(self, block, key, default=None):
        """
        Look up `key` in `block`, replacing with `default` if not found,
        expanding any strings wrapped in "{}", and return as an int.
        """
        return int(self.get_value(block, key, default))

    def get_bool(self, block, key, default=None):
        """
        Look up `key` in `block`, replacing with `default` if not found,
        expanding any strings wrapped in "{}", and return as a bool.
        """
        return bool(self.get_value(block, key, default))


class ProfileSequence(Sequence):
    """
    A Sequence that contains a single real-valued time series.

    Keys used from `cfg`:

    * `type`: One of 'profile_dist', 'profile_ol', 'profile_cl',
              'profile_aout', 'profile_can', or 'profile_uart'.
    * `name`: Profile name
    * `role`: Output role ID
    * `units`: Units for display
    * `channel`: Output channel (1 for AMVs)
    * `scale_max`: Value in input units to correspond to 65535 at output
    * `dt_ms': Output timestep in milliseconds, (default 100, not used in V2 tables)
    * `cutoff_freq`: Filter cutoff frequency in Hz, (default 3.0, not used in V2 tables)
    * `tzero_offset`: Sequence time at first sequence point (default 0)
    * `initial_value`: Value at first sequence point (default 0)
    * `profile`: List of dicts of blocks which define the profile shape:
        * `type`: 'corner'/'hold'/'ramp'/'staircase'
        * See block documentation for remaining keys
    """

    def __init__(self, cfg, variables):
        super().__init__(variables)
        valid_types = list(AMV_PROFILE_TYPES.keys()) + [
            "profile_aout",
            "profile_can",
            "profile_uart",
        ]
        assert cfg["type"] in valid_types
        self.name = cfg["name"]
        self.role = cfg["role"]
        self.units = cfg["units"]
        self.profile_type = cfg["type"]
        self.channel = cfg.get("channel")
        if self.profile_type == "profile_aout" and not (1 <= self.channel <= 4):
            raise ValueError("For profile_aout, channel must be 1-4")
        if self.profile_type in AMV_PROFILE_TYPES.keys() and self.channel != 1:
            raise ValueError("For AMV profiles, channel must be 1")
        self.dt_ms = cfg["dt_ms"]
        self.scale_max = cfg["scale_max"]
        self.cutoff = cfg["cutoff_freq"]
        self.tzero_offset = cfg["tzero_offset"]
        self.initial_value = cfg["initial_value"]

        # Generate corners for run profile, starting at tzero_offset and
        # initial_value from profile.
        self.corners = [(self.tzero_offset, self.initial_value, 0)]
        self._blocks_to_corners(cfg["profile"], self.corners)

        # If specified, generate corners for stop profile, which must
        # start with an explicit corner (value is maintained from moment
        # of stop until first corner is reached, allowing ramp-down).
        self.stop_corners = []
        if cfg["stop_profile"]:
            self.stop_corners = [(0.0, 0.0, DAQ_SEQ_FLAG_BIT_USE_STOP_VALUE)]
            self._blocks_to_corners(cfg["stop_profile"], self.stop_corners)

    def _block_corner(self, corners, block):
        """
        Insert a single new corner at time block['duration'] from previous
        time, to new value at block['target'].

        Block keys:
        * 'duration': Delta time from previous corner, in seconds.
                      Specify either 'duration' or 'time'.
                      Default: 0.0
                      Templated: Yes, float
        * 'time':     Absolute time of corner, in seconds.
                      Specify either 'duration' or 'time'.
                      Default: Uses 'duration' if unspecified.
                      Templated: Yes, float
        * 'target':   New value to move to.
                      Default: previous value
                      Templated: Yes, float
        * 'allow_override': Mark this corner as allowing override via network
                            command until the next corner.
                            Default: False
                            Templated: Yes, bool
        * 'use_stop_value': Mark this corner to use the value in place when the
                            stop sequence began instead of the specified value.
                            Default: False
                            Templated: Yes, bool
        """
        prev_t, prev_v, _ = corners[-1]
        if "time" in block:
            assert "duration" not in block, "Cannot specify both 'time' and 'duration'"
            time = self.get_float(block, "time")
            assert time >= prev_t, "'time' must be after previous corner time"
            duration = time - prev_t
        else:
            duration = self.get_float(block, "duration", 0.0)
        target = self.get_float(block, "target", prev_v)
        flags = 0
        if self.get_bool(block, "allow_override", False):
            flags |= DAQ_SEQ_FLAG_BIT_ALLOW_OVERRIDE
        if self.get_bool(block, "use_stop_value", False):
            flags |= DAQ_SEQ_FLAG_BIT_USE_STOP_VALUE
        corners.append((prev_t + duration, target, flags))

    def _block_hold(self, corners, block):
        """
        Hold previous value for an additional block['duration'] seconds.

        Block keys:
        * 'duration': Duration of hold, in seconds.
                      Specify either 'duration' or 'until'.
                      Default: 0.0
                      Templated: Yes, float
        * 'until':    Hold until an absolute time in seconds.
                      Specify either 'duration' or 'until'.
                      Default: Uses 'duration' if unspecified.
                      Templated: Yes, float
        * 'allow_override': Mark this corner as allowing override via network
                            command until the next corner.
                            Default: False
                            Templated: Yes, bool
        * 'use_stop_value': Mark this corner to use the value in place when the
                            stop sequence began instead of the specified value.
                            Default: False
                            Templated: Yes, bool
        """
        prev_t, prev_v, prev_flags = corners[-1]
        if "until" in block:
            assert "duration" not in block, "Cannot specify both 'until' and 'duration'"
            until = self.get_float(block, "until")
            assert until >= prev_t, "'until' must be after previous corner time"
            duration = until - prev_t
        else:
            duration = self.get_float(block, "duration", 0.0)
        flags = prev_flags & DAQ_SEQ_FLAG_BIT_USE_STOP_VALUE
        if self.get_bool(block, "allow_override", False):
            corners[-1] = (prev_t, prev_v, prev_flags | DAQ_SEQ_FLAG_BIT_ALLOW_OVERRIDE)
        if self.get_bool(block, "use_stop_value", False):
            flags |= DAQ_SEQ_FLAG_BIT_USE_STOP_VALUE
        corners.append((prev_t + duration, prev_v, flags))

    def _block_ramp(self, corners, block):
        """
        Ramp from previous value to block['target'], either over
        block['duration'] seconds, at a rate of block['rate'] per second, or
        until absolute time block['until'].

        Block keys:
        * 'duration': Duration of ramp, in seconds.
                      Specify either 'duration', 'rate', or 'until'.
                      Default: 0.0
                      Templated: Yes, float
        * 'rate':     Ramp rate in value-units per second.
                      Specify either 'duration', 'rate', or 'until'.
                      Default: Uses 'duration' if unspecified.
                      Templated: Yes, float
        * 'until':    Time at which ramp finishes, in absolute seconds.
                      Specify either 'duration', 'rate', or 'until'.
                      Default: Uses 'duration' if unspecified.
                      Templated: Yes, float
        * 'target':   Target value to ramp to.
                      Default: previous value
                      Templated: Yes, float
        """
        prev_t, prev_v, _ = corners[-1]
        target = self.get_float(block, "target", prev_v)
        if "until" in block:
            until = self.get_float(block, "until")
            duration = until - prev_t
        elif "rate" in block:
            rate = self.get_float(block, "rate")
            duration = abs(prev_v - target) / rate
        else:
            duration = self.get_float(block, "duration", 0.0)
        corners.append((prev_t + duration, target, 0))

    def _block_staircase(self, corners, block):
        """
        Generates a staircase profile. Step values are either given in
        block['steps'], or computed from block['nsteps'] and block['target'].

        Each step is dwelled on for block['step_duration'] seconds, ramping between
        steps either over block['ramp_duration'] seconds or at a rate of
        block['ramp_rate'].

        Block keys:
        * 'steps':         List of values to hold at.
                           Specify either 'steps' OR ('nsteps' and 'target').
                           Default: Uses 'nsteps' if unspecified.
                           Templated: Yes, see below.
        * 'nsteps':        Number of steps to generate, instead of using 'steps'.
                           Specify either 'steps' OR ('nsteps' and 'target').
                           Default: 1
                           Templated: Yes, integer
        * 'target':        Final value to hold at, instead of using 'steps'.
                           Specify either 'steps' OR ('nsteps' and 'target').
                           Default: previous value
                           Templated: Yes, float
        * 'step_duration': Duration to hold each step.
                           Default: 0.0
                           Templated: Yes, float
        * 'ramp_rate':     Ramp rate between steps in value-units per second
                           Specify either 'ramp_rate' OR 'ramp_duration'.
                           Default: uses 'ramp_duration' if unspecified.
                           Templated: Yes, float
        * 'ramp_duration': Duration to ramp between each step.
                           Specify either 'ramp_rate' OR 'ramp_duration'.
                           Default: 0.0
                           Templated: Yes, float

        Note on templating 'steps':
        If 'steps' is a single variable name enclosed by "{" and "}", it is
        replaced entirely by the template value, which must be either a list of
        floats or a string representing a list of floats in YAML format.
        If 'steps' is a list or a string representing a list, each entry in the
        list is optionally templated as a float.
        """
        prev_t, prev_v, _ = corners[-1]
        if "steps" in block:
            # If steps is specified, it may be a simple list of floats,
            # or a list of strings representing templated floats,
            # or a string representing a variable containing a list.
            s = block["steps"]
            if isinstance(s, str) and s.startswith("{") and s.endswith("}"):
                # In this case s is like '{variable}',
                # and variable is either a list already or a string for a list.
                s_var = s[1:-1]
                if s_var not in self.variables:
                    raise KeyError(f"{s_var} not found in variables")
                steps = self.variables[s_var]
                if isinstance(steps, str):
                    steps = list(yaml.safe_load(steps))
                else:
                    steps = list(steps)
            else:
                steps = []
                # Otherwise s is a list of either floats or strings to template
                for step in list(s):
                    steps.append(self.get_float({"step": step}, "step"))

        else:
            # If steps is not specified, use 'nsteps' and 'target' instead,
            # both of which can take default values.
            nsteps = self.get_int(block, "nsteps", 1)
            target = self.get_float(block, "target", prev_v)
            if nsteps <= 1:
                step_size = target - prev_v
            else:
                step_size = (target - prev_v) / (nsteps - 1)
            steps = [prev_v + step_size * i for i in range(nsteps)]

        step_duration = self.get_float(block, "step_duration", 0.0)
        ramp = {}
        if "ramp_rate" in block:
            ramp["rate"] = self.get_float(block, "ramp_rate")
        else:
            ramp["duration"] = self.get_float(block, "ramp_duration", 0.0)

        def ramp_to(target):
            b = {"target": target}
            b.update(ramp)
            self._block_ramp(b)

        if steps[0] != prev_v:
            ramp_to(steps[0])
        for step in steps[1:]:
            self._block_hold({"duration": step_duration})
            ramp_to(step)
        self._block_hold({"duration": step_duration})

    def _block_to_corners(self, corners, block):
        """
        Process block based on block['type'].

        If 'type' is unspecified it defaults to 'corner'.
        """
        block_type = block.get("type", "corner")
        if block_type == "corner":
            self._block_corner(corners, block)
        elif block_type == "hold":
            self._block_hold(corners, block)
        elif block_type == "ramp":
            self._block_ramp(corners, block)
        elif block_type == "staircase":
            self._block_staircase(corners, block)
        else:
            raise ValueError(f"Unknown block type {block_type}")

    def _blocks_to_corners(self, blocks, corners):
        """
        Process entire list of blocks.

        Starting corner is ``initial``.

        Returns final list of corners, as (t, v) pairs.
        Time in seconds without tzero_offset applied (i.e., may be negative).
        Values in physical quantities (not scaled output units).
        """
        for block in blocks:
            self._block_to_corners(corners, block)

    def _interpolate_corners(self, corners, scale=True):
        """
        Creates a regularly sampled profile based on an array of (t, val, flags)
        corners. The output type is np.uint16, scaled such that `scale_max` in
        the input corresponds to 65535 in the output.

        Returns filtered and resampled profile timesteps and data array.
        """

        scale_max = self.scale_max
        dt_ms = self.dt_ms
        corners = np.asarray(corners)

        # Check arguments
        assert np.all(
            np.diff(corners[:, 0]) >= 0
        ), "Profile times must be monotonically non-decreasing"
        assert not np.any(corners[:, 1] > scale_max), "Profile exceeds scale_max"
        assert isinstance(dt_ms, int), "dt_ms must be an integer"
        assert 1 <= dt_ms <= 1000, "dt_ms must be between 1 and 1000"

        # Replace USE_STOP_VALUE with maximum run value for display purposes
        # (Note that stop sequences aren't allowed for table v1 so won't go
        #  through _interpolate_corners for generating tables).
        use_stop_idxs = corners[:, 2].astype(int) & DAQ_SEQ_FLAG_BIT_USE_STOP_VALUE != 0
        replacement_stop_val = max(c[1] for c in self.corners)
        corners[use_stop_idxs, 1] = replacement_stop_val

        # Resample to internal dt of 1ms
        dt_filter = 1e-3
        t = np.arange(corners[0, 0], corners[-1, 0] + dt_filter, dt_filter)
        p = np.interp(t, corners[:, 0], corners[:, 1])

        # Filter
        f = (1.0 / dt_filter) / (2.0 * np.pi * self.cutoff)
        p_filt = scipy.ndimage.gaussian_filter1d(p, f)

        # Resample to output dt
        t_out = np.arange(corners[0, 0], corners[-1, 0] + dt_ms * 1e-3, dt_ms * 1e-3)
        p_out = np.interp(t_out, t, p_filt)

        # Rescale
        if scale:
            p_out *= 65535.0 / scale_max
            # Check output
            assert np.all(p_out >= 0.0), "Generated profile not non-negative"
            assert np.all(p_out <= 65535.0), "Generated profile exceeds 65535"
            p_out = p_out.astype("<u2")

        return t_out, p_out

    def _generate_display(self, corners):
        t, v = self._interpolate_corners(corners, scale=False)
        displays = [(t, v, self.role, self.name, self.units)]
        flag_t = []
        allow_override = []
        use_stop_value = []
        for (c, next_c) in pairwise(corners):
            flag_t.append(c[0])
            flag_t.append(next_c[0])
            for _ in range(2):
                allow_override.append((c[2] & DAQ_SEQ_FLAG_BIT_ALLOW_OVERRIDE) != 0)
                use_stop_value.append((c[2] & DAQ_SEQ_FLAG_BIT_USE_STOP_VALUE) != 0)
        if any(allow_override):
            role = f"{self.role}-allow-override"
            name = f"{self.name}: Allow override"
            displays.append((flag_t, allow_override, role, name, "Flag"))
        if any(use_stop_value):
            role = f"{self.role}-use-stop-valuee"
            name = f"{self.name}: Use stop value"
            displays.append((flag_t, use_stop_value, role, name, "Flag"))
        return displays

    def to_display(self):
        display = {DAQ_SEQ_ID_RUN: self._generate_display(self.corners)}
        if self.stop_corners:
            display[DAQ_SEQ_ID_STOP] = self._generate_display(self.stop_corners)
        return display

    def durations(self):
        durations = {DAQ_SEQ_ID_RUN: self.corners[-1][0] - self.tzero_offset}
        if self.stop_corners:
            durations[DAQ_SEQ_ID_STOP] = self.stop_corners[-1][0]
        return durations

    def extend(self, durations):
        if DAQ_SEQ_ID_RUN in durations and self.corners:
            final_t = durations[DAQ_SEQ_ID_RUN] + self.tzero_offset
            last_corner = self.corners[-1]
            if final_t > last_corner[0]:
                self.corners.append((final_t, last_corner[1], last_corner[2]))
        if DAQ_SEQ_ID_STOP in durations and self.stop_corners:
            final_t = durations[DAQ_SEQ_ID_STOP]
            if final_t > self.stop_corners[-1][0]:
                self.stop_corners.append((final_t, last_corner[1], last_corner[2]))

    def _to_table_v1(self):
        if self.profile_type not in AMV_PROFILE_TYPES:
            pt = self.profile_type
            raise ValueError(f"Unsupported profile type {pt} for V1 table")
        if self.stop_corners:
            raise ValueError("Stop profile not supported in V1 table")
        (_, v) = self._interpolate_corners(self.corners)
        profile = np.zeros(len(v) + 3, dtype="<u2")
        profile[0] = self.dt_ms
        profile[1] = len(v)
        profile[2] = AMV_PROFILE_TYPES[self.profile_type]
        profile[3:] = v
        return profile.tobytes()

    def _to_table_v2(self):
        if self.profile_type in AMV_PROFILE_TYPES:
            header_type = DAQ_SEQ_TYPE_AMV
            meta = [AMV_PROFILE_TYPES[self.profile_type], 0, 0, 0]
        elif self.profile_type == "profile_aout":
            header_type = DAQ_SEQ_TYPE_AOUT
            meta = [self.channel - 1, 0, 0, 0]
        elif self.profile_type == "profile_can":
            header_type = DAQ_SEQ_TYPE_CAN
            meta = [0, 0, 0, 0]
        elif self.profile_type == "profile_uart":
            header_type = DAQ_SEQ_TYPE_UART
            meta = [0, 0, 0, 0]

        corners = np.asarray(self.corners)
        assert np.all(
            np.diff(corners[:, 0]) >= 0
        ), "Profile times must be monotonically non-decreasing"
        assert not np.any(corners[:, 1] > self.scale_max), "Profile exceeds scale_max"
        corners[:, 0] -= self.tzero_offset
        assert np.all(corners[:, 0] >= 0), "Times must  be non-negative"
        corners[:, 0] *= 1e3
        corners[:, 1] *= 65535.0 / self.scale_max
        corners = corners.astype("<u4")
        corners[:, 1] |= corners[:, 2]
        data = corners[:, :2].tobytes()

        seq_id = DAQ_SEQ_ID_RUN
        header = struct.pack("<HBBIIII", len(self.corners), header_type, seq_id, *meta)

        table = header + data

        if self.stop_corners:
            stop_corners = np.asarray(self.stop_corners)
            assert np.all(
                np.diff(stop_corners[:, 0]) >= 0
            ), "Profile times must be monotonically non-decreasing"
            assert not np.any(
                stop_corners[:, 1] > self.scale_max
            ), "Profile exceeds scale_max"
            stop_corners[:, 0] -= self.tzero_offset
            assert np.all(stop_corners[:, 0] >= 0), "Times must  be non-negative"
            stop_corners[:, 0] *= 1e3
            stop_corners[:, 1] *= 65535.0 / self.scale_max
            stop_corners = stop_corners.astype("<u4")
            stop_corners[:, 1] |= stop_corners[:, 2]
            stop_data = stop_corners.tobytes()
            seq_id = DAQ_SEQ_ID_STOP
            stop_header = struct.pack(
                "<HBBIIII", len(self.stop_corners), header_type, seq_id, *meta
            )
            table += stop_header + stop_data

        return table


class DigitalSequence(Sequence):
    """
    A Sequence that contains up to 32 binary-valued time series.

    Keys used from `cfg`:
    * `type`: must be 'sequence'
    * `tzero_offset`: Sequence time at first sequence point (default 0)
    * `sequence`: List of dicts of channels:
        * `channel`: Channel number on valve controller box
        * `name`: Optional channel name to display
        * `run`: List of [on_time, off_time] windows for run sequence
        * `stop`: List of [on_time, off_time] windows for stop sequence
        * If either list is empty, the channel is included in the relevant
          mask but never turned on.
        * Both run and stop are optional.
          If neither are specified, the channel is excluded from both
          run and stop masks.
          If only a run sequence is specified, the channel is included
          in both run and stop masks, and turned off in the stop sequence.
          If only a stop sequence is specified, the channel is excluded
          from the run mask, but included in the stop mask.
    """

    def __init__(self, cfg, variables):
        super().__init__(variables)
        self.tzero_offset = cfg["tzero_offset"]
        assert cfg.get("type") == "sequence"
        seq = cfg["sequence"]
        for channel in seq:
            assert "channel" in channel, "Channel definition missing 'channel'"
            assert channel["channel"] > 0, "Channel must be > 0"
            if "name" not in channel:
                channel["name"] = f"Channel {channel['channel']}"
        self.channel_names = {ch["channel"]: ch["name"] for ch in seq}
        self.channel_roles = {ch["channel"]: ch["role"] for ch in seq}
        # Steps are lists of [time, value] where time is in milliseconds since
        # sequence start (tzero_offset already applied) and value is a 32-bit
        # mask for all 32 possible valve channels.
        self.run_mask, self.run_steps = self._sequence_to_steps(seq, "run")
        self.stop_mask, self.stop_steps = self._sequence_to_steps(seq, "stop")
        self.stop_mask |= self.run_mask

    def _sequence_to_steps(self, sequence, run_or_stop="run"):
        """
        Convert a list of channels with on-windows to a sequence of valve commands.

        `tzero_offset` is subtracted from all times in the provided windows, so the
        returned steps always start at time 0.
        """
        assert run_or_stop in ("run", "stop")
        tzero_offset = self.tzero_offset if run_or_stop == "run" else 0.0
        mask = 0
        step_times = {0: {"on": [], "off": []}}
        for channel in sequence:
            if run_or_stop in channel:
                ch = int(channel["channel"])
                assert 1 <= ch <= 32, f"Channel {ch} is outside range 1-32"
                mask |= 1 << (ch - 1)
                windows = channel[run_or_stop]
                for start_stop in windows:
                    # Process start time first, which must always be present.
                    # Template, convert to seconds, remove offset, convert to
                    # 1ms step times, and add to overall sequence.
                    start = start_stop[0]
                    start = float(self.template_str(start)) - tzero_offset
                    start = int(start * 1000)
                    if start not in step_times:
                        step_times[start] = {"on": [], "off": []}
                    step_times[start]["on"].append(ch)
                    # If present, process stop times, otherwise valve will stay
                    # on until the next window or indefinitely.
                    if len(start_stop) == 2:
                        stop = start_stop[1]
                        stop = float(self.template_str(stop)) - tzero_offset
                        stop = int(stop * 1000)
                        if stop not in step_times:
                            step_times[stop] = {"on": [], "off": []}
                        step_times[stop]["off"].append(ch)
        steps = []
        state = 0
        for t in sorted(step_times.keys()):
            for ch in step_times[t]["on"]:
                state |= 1 << (ch - 1)
            for ch in step_times[t]["off"]:
                state &= ~(1 << (ch - 1))
            steps.append((t, state))
        return mask, steps

    def durations(self):
        return {
            DAQ_SEQ_ID_RUN: self.run_steps[-1][0] / 1000.0,
            DAQ_SEQ_ID_STOP: self.stop_steps[-1][0] / 1000.0,
        }

    def extend(self, durations):
        if DAQ_SEQ_ID_RUN in durations and self.run_steps:
            duration = int(durations[DAQ_SEQ_ID_RUN] * 1000)
            if duration > self.run_steps[-1][0]:
                self.run_steps.append((duration, self.run_steps[-1][1]))
        if DAQ_SEQ_ID_STOP in durations and self.stop_steps:
            duration = int(durations[DAQ_SEQ_ID_STOP] * 1000)
            if duration > self.stop_steps[-1][0]:
                self.stop_steps.append((duration, self.stop_steps[-1][1]))

    def _render_for_display(self, run_or_stop, edge_dt=0.0005, max_dt=0.1):
        """
        Convert a mask and list of (time, state) steps to a time series
        per channel, suitable for plotting.

        Returns a list of (time, value, channel), with transitions in value
        output over `edge_dt` seconds to ensure sharp edges when points are
        interpolated, and repeat points inserted every `max_dt` to ensure
        minimum output density. `channel_number` is 1-indexed.

        Only channels set in `mask` are output.
        """
        if run_or_stop == "run":
            mask, steps = self.run_mask, self.run_steps
            tzero_offset = self.tzero_offset
        elif run_or_stop == "stop":
            mask, steps = self.stop_mask, self.stop_steps
            tzero_offset = 0.0
        else:
            raise ValueError("run_or_stop must be 'run' or 'stop'")

        # Store time series and corresponding values for each channel
        time = [0.0]
        channels = {i: [0.0] for i in range(len(f"{mask:b}"))}

        for (t, state) in steps:
            # Convert t from steps of 1ms to seconds
            t *= 0.001
            # Insert repeat points every max_dt steps
            while t - time[-1] > max_dt:
                time.append(time[-1] + max_dt)
                for d in channels.values():
                    d.append(d[-1])
            # Insert current value at current time
            time.append(t)
            for d in channels.values():
                d.append(d[-1])
            # Insert new values at edge_dt time later
            time.append(t + edge_dt)
            for ch in channels:
                bit = (state & (1 << ch)) >> ch
                channels[ch].append(float(bit))

        # Apply tzero offset for display
        time = np.asarray(time) + tzero_offset

        return [
            (time, d, self.channel_roles[ch + 1], self.channel_names[ch + 1])
            for (ch, d) in channels.items()
            if mask & (1 << ch)
        ]

    def to_display(self):
        """
        Generate the required dict of start/stop sequences.
        """
        return {
            DAQ_SEQ_ID_RUN: self._render_for_display("run"),
            DAQ_SEQ_ID_STOP: self._render_for_display("stop"),
        }

    def to_table(self, version):
        run_data = np.asarray(self.run_steps).astype("<u4").tobytes()
        stop_data = np.asarray(self.stop_steps).astype("<u4").tobytes()

        if version == 1:
            header = struct.pack(
                "<IIII",
                self.run_mask,
                len(self.run_steps),
                self.stop_mask,
                len(self.stop_steps),
            )
            return header + run_data + stop_data
        elif version == 2:
            run_header = struct.pack(
                "<HBBIIII",
                len(self.run_steps),
                DAQ_SEQ_TYPE_VALVE,
                DAQ_SEQ_ID_RUN,
                self.run_mask,
                0,
                0,
                0,
            )
            stop_header = struct.pack(
                "<HBBIIII",
                len(self.stop_steps),
                DAQ_SEQ_TYPE_VALVE,
                DAQ_SEQ_ID_STOP,
                self.stop_mask,
                0,
                0,
                0,
            )
            return run_header + run_data + stop_header + stop_data


class NopSequence(DigitalSequence):
    """
    Generates profile data to cause a programmed box to take no action,
    but ensure valve boxes are "running" for the full duration of a sequence.

    This can be safely written to all DAUs in a configuration not otherwise
    given a profile, to ensure they do not still contain old profile data.
    """

    def __init__(self):
        self.variables = {}
        self.run_mask = self.stop_mask = 0
        # Put enough steps that if this table ends up generated as V1 and then
        # incorrectly interpreted as an AMV profile, it will be in a mode that
        # doesn't exist (in addition to having nsteps=0).
        self.run_steps = [(0, 0), (0, 0), (0, 0)]
        self.stop_steps = [(0, 0), (0, 0), (0, 0)]


if __name__ == "__main__":
    import sys
    from pprint import pprint

    c = Config(sys.argv[1])
    for tpl in c.templates:
        print("----------------------------------------------")
        print(tpl)
        print("Variables:")
        pprint(tpl.variables)
        print("Valves:")
        pprint(tpl.valves)
        print("Profiles:")
        pprint(tpl.profiles)
        print()
