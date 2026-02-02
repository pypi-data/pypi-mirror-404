from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableView, QAbstractItemView
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex


class FileMetadataModel(QAbstractTableModel):
    def __init__(self, metadata):
        super().__init__()
        self._data = list(metadata.items())

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self._data[index.row()][index.column()])
        else:
            return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return ["Attribute", "Value"][section]
        else:
            return section + 1


class FileMetadata(QDialog):
    def __init__(self, metadata):
        super().__init__()
        self.model = FileMetadataModel(metadata)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        table = QTableView(self)
        table.setModel(self.model)
        table.setAlternatingRowColors(True)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.resizeRowsToContents()
        table.resizeColumnsToContents()
        layout.addWidget(table)
        width = int(table.horizontalHeader().length() * 1.5)
        height = int(table.verticalHeader().length() * 1.5)
        self.resize(width, height)
