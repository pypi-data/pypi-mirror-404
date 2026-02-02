from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTreeView, QGroupBox, QGridLayout,
                               QLineEdit, QErrorMessage, QMessageBox, QListView,
                               QApplication)


class Channel:
    def __init__(self, channel, row, group):
        self.channel = channel
        self.group = group
        self.row = row

    def get_name(self):
        return "{} ({})".format(self.channel['name'], self.channel['id'])


class Group:
    def __init__(self, name, row):
        self.name = name
        self.row = row
        self.channels = []

    def get_name(self):
        return self.name


class ChannelModel(QAbstractItemModel):
    """Present the tree of grouped channels as a QAbstractItemModel."""
    def __init__(self, dataset):
        super().__init__()
        self.dataset = dataset
        groups = dataset.channels_by_group()
        self.groups = []
        for idx, (group_id, channels) in enumerate(groups.items()):
            group = Group(dataset.get_group_name(group_id), idx)
            channels = [Channel(channel, i, group)
                        for (i, channel) in enumerate(channels)]
            group.channels = channels
            self.groups.append(group)

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            if row < len(self.groups):
                return self.createIndex(row, column, self.groups[row])
            else:
                return QModelIndex()
        else:
            parent = parent.internalPointer()
            if row < len(parent.channels):
                return self.createIndex(row, column, parent.channels[row])
            else:
                return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        child = index.internalPointer()
        if isinstance(child, Channel):
            group = child.group
            return self.createIndex(group.row, 0, group)
        else:
            return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self.groups)
        else:
            parent = parent.internalPointer()
            if isinstance(parent, Group):
                return len(parent.channels)
            else:
                return 0

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        item = index.internalPointer()
        col = index.column()
        if col == 0:
            return item.get_name()
        else:
            return None

    def flags(self, index):
        return Qt.ItemIsEnabled

    def headerData(self, action, orientation, role=Qt.DisplayRole):
        return None


class DerivedChannelModel(QAbstractItemModel):
    """Present the list of recent derived channels as a QAbstractItemModel."""
    def __init__(self, dataset, prefs):
        super().__init__()
        self.dataset = dataset
        self.prefs = prefs
        self.channels = []
        channels = self.prefs.get_recent_derived_channels()
        for channel in channels:
            try:
                dataset.evaluate(channel['expr'])
            except ValueError:
                pass
            else:
                self.channels.append(channel)

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            if row < len(self.channels):
                return self.createIndex(row, column, self.channels[row])
            else:
                return QModelIndex()
        else:
            return QModelIndex()

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self.channels)
        else:
            return 0

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        item = index.internalPointer()
        col = index.column()
        if col == 0:
            return "{} ({})".format(item['name'], item['id'])
        else:
            return None

    def flags(self, index):
        return Qt.ItemIsEnabled

    def headerData(self, action, orientation, role=Qt.DisplayRole):
        return None


class CreateDerivedChannelDialog(QDialog):
    """Dialog to configure and create a new derived channel."""
    def __init__(self, dataset, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Derived Channel")
        self.app = QApplication.instance()
        self.channel_model = ChannelModel(dataset)
        self.recent_model = DerivedChannelModel(dataset, self.app.prefs)
        self.dataset = dataset
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        lhs = QVBoxLayout()
        rhs = QVBoxLayout()
        layout.addLayout(lhs)
        layout.addLayout(rhs)

        ch_box = QGroupBox(self)
        ch_layout = QVBoxLayout(ch_box)
        ch_box.setLayout(ch_layout)
        lhs.addWidget(ch_box, stretch=3)
        ch_lbl = QLabel(
            "Available Channels\n(double click to add to expression)")
        ch_layout.addWidget(ch_lbl)
        ch_tree = QTreeView(self)
        ch_tree.setModel(self.channel_model)
        ch_tree.expandAll()
        ch_tree.resizeColumnToContents(0)
        ch_tree.resizeColumnToContents(1)
        ch_tree.doubleClicked.connect(self.item_clicked)
        ch_layout.addWidget(ch_tree)

        recent_box = QGroupBox(self)
        recent_layout = QVBoxLayout(recent_box)
        recent_box.setLayout(recent_layout)
        lhs.addWidget(recent_box, stretch=1)
        recent_lbl = QLabel(
            "Recent Derived Channels\n(double click to populate form)")
        recent_layout.addWidget(recent_lbl)
        recent_list = QListView(self)
        recent_list.setModel(self.recent_model)
        recent_list.doubleClicked.connect(self.recent_clicked)
        recent_layout.addWidget(recent_list)

        info_box = QGroupBox(self)
        info_box_layout = QVBoxLayout(info_box)
        info_lbl = QLabel("""\
You can create a new derived channel which is computed using other channels.

IDs should not contain spaces and are case-sensitive.
Colours may be any web colour name, or a hex colour such as #ff0000.
Limit values are used to display optional red/yellow lines on the chart.

The expression determines how the new channel is computed. Supported operators
are +, -, *, /, **, %, <<, >>, <, <=, ==, !=, >=, >, &, |, and ~. Supported
functions are (arc)sin(h), (arc)cos(h), (arc)tan(h), log, log10, exp, sqrt,
and abs. Other channel IDs are accepted as variables.

Click 'Validate' to check the expression.""")
        info_box_layout.addWidget(info_lbl)
        info_box.setLayout(info_box_layout)
        rhs.addWidget(info_box)

        rhs.addStretch()

        form_layout = QGridLayout()

        name_lbl = QLabel("Name:", self)
        form_layout.addWidget(name_lbl, 0, 0)
        self.name_le = QLineEdit(self)
        form_layout.addWidget(self.name_le, 0, 1)

        id_lbl = QLabel("ID:", self)
        form_layout.addWidget(id_lbl, 1, 0)
        self.id_le = QLineEdit(self)
        form_layout.addWidget(self.id_le, 1, 1)

        colour_lbl = QLabel("Colour (optional):", self)
        form_layout.addWidget(colour_lbl, 2, 0)
        self.colour_le = QLineEdit(self)
        form_layout.addWidget(self.colour_le, 2, 1)

        units_lbl = QLabel("Units (optional):", self)
        form_layout.addWidget(units_lbl, 3, 0)
        self.units_le = QLineEdit(self)
        form_layout.addWidget(self.units_le, 3, 1)

        ylwline_lbl = QLabel("Yelowline limit (optional):", self)
        form_layout.addWidget(ylwline_lbl, 4, 0)
        self.ylwline_le = QLineEdit(self)
        form_layout.addWidget(self.ylwline_le, 4, 1)

        redline_lbl = QLabel("Redline limit (optional):", self)
        form_layout.addWidget(redline_lbl, 5, 0)
        self.redline_le = QLineEdit(self)
        form_layout.addWidget(self.redline_le, 5, 1)

        expr_lbl = QLabel("Expression:", self)
        form_layout.addWidget(expr_lbl, 6, 0)
        self.expr_le = QLineEdit(self)
        form_layout.addWidget(self.expr_le, 6, 1)

        rhs.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel", self)
        validate_btn = QPushButton("Validate", self)
        add_btn = QPushButton("Add", self)
        cancel_btn.clicked.connect(self.reject)
        validate_btn.clicked.connect(self.validate_clicked)
        add_btn.clicked.connect(self.add_clicked)
        add_btn.setDefault(True)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(validate_btn)
        buttons_layout.addWidget(add_btn)
        rhs.addLayout(buttons_layout)

    def add_clicked(self):
        expr = self.expr_le.text()
        channel = {
            "id": self.id_le.text(),
            "name": self.name_le.text(),
            "colour": self.colour_le.text(),
            "units": self.units_le.text(),
        }
        try:
            redline = self.redline_le.text()
            if redline:
                channel['redline'] = float(redline)
            ylwline = self.ylwline_le.text()
            if ylwline:
                channel['yellowline'] = float(ylwline)

            self.dataset.add_derived_channel(channel, expr)
        except ValueError as e:
            error = QErrorMessage(self)
            error.setModal(True)
            error.showMessage("Error adding channel:\n" + str(e))
        else:
            self.accept()

    def validate_clicked(self):
        expr = self.expr_le.text()
        try:
            self.dataset.evaluate(expr)
        except ValueError as e:
            error = QErrorMessage(self)
            error.setModal(True)
            error.showMessage("Error validating expression:\n" + str(e))
        else:
            QMessageBox.information(
                None, "Validation succeeded", "Validation succeeded")

    def item_clicked(self, index):
        item = index.internalPointer()
        if isinstance(item, Channel):
            self.expr_le.insert(item.channel['id'] + " ")
            self.expr_le.setFocus()

    def recent_clicked(self, index):
        item = index.internalPointer()
        self.name_le.setText(item['name'])
        self.id_le.setText(item['id'])
        if 'colour' in item:
            self.colour_le.setText(item['colour'])
        if 'units' in item:
            self.units_le.setText(item['units'])
        if 'yellowline' in item:
            self.ylwline_le.setText(str(item['yellowline']))
        if 'redline' in item:
            self.redline_le.setText(str(item['redline']))
        self.expr_le.setText(item['expr'])
