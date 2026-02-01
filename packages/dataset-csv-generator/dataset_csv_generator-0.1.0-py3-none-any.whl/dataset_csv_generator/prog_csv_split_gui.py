#!/usr/bin/python

import sys
import os
import json
import signal
import subprocess
from pathlib import Path
import numpy as np
from sklearn.model_selection import train_test_split

import WorkingWithFiles as rnfunc

from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QDoubleSpinBox,
    QMessageBox,
    QGridLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QWidget,
    QMainWindow,
    QAction,
    QSizePolicy,
)

from PyQt5.QtGui  import QIcon, QDesktopServices
from PyQt5.QtCore import Qt, QUrl

import dataset_csv_generator.about as about
import dataset_csv_generator.modules.configure as configure 
from   dataset_csv_generator.modules.wabout  import show_about_window
from   dataset_csv_generator.desktop import create_desktop_file, create_desktop_directory, create_desktop_menu


# Path to config file
CONFIG_PATH = os.path.join( os.path.expanduser("~"),
                            ".config", 
                            about.__package__, 
                            "config."+about.__program_csv_split_gui__+".json" )

DEFAULT_CONTENT={   "toolbar_configure": "Configure",
                    "toolbar_configure_tooltip": "Open the configure Json file",
                    "toolbar_about": "About",
                    "toolbar_about_tooltip": "About the program",
                    "toolbar_coffee": "Coffee",
                    "toolbar_coffee_tooltip": "Buy me a coffee (TrucomanX)",
                    "window_input": "<b>Input:</b>",
                    "window_input_button": "Input csv file:",
                    "window_input_tooltip": "Select the input *.csv file path to split.",
                    "window_input_edit": "",
                    "window_percentage_label": "Test percentage %:",
                    "window_percentage_spin": 38.19,
                    "window_percentage_spin_tooltip": "Set the size percentage of the test dataset.",
                    "window_category_column_label": "Category column name:",
                    "window_category_column_lineedit": "label",
                    "window_category_column_lineedit_tooltip": "The column name of the column containing categorical data used to split the dataset in a stratified way. If left blank, the code assumes the last column is the categorical column. If the specified column name does not exist, the program returns an error.",
                    "window_output": "<b>Output:</b>",
                    "window_output_dir_button": "CSV file directory:",
                    "window_output_dir_lineedit": "./",
                    "window_output_dir_tooltip": "Select the *csv file to be split.",
                    "window_output_train_label": "CSV train filename:",
                    "window_output_train_lineedit": "train.csv",
                    "window_output_train_lineedit_tooltip": "The filename of the train *.csv file.",
                    "window_output_test_label": "CSV test filename:",
                    "window_output_test_lineedit": "test.csv",
                    "window_output_test_lineedit_tooltip": "The filename of the test *.csv file.",
                    "window_generate_button": "Generate",
                    "window_generate_button_tooltip": "Generate train and test *.csv files.",
                    "window_open_file": "Open File",
                    "window_select_directory": "Select Directory",
                    "window_width": 500,
                    "window_height": 400
                }

configure.verify_default_config(CONFIG_PATH,default_content=DEFAULT_CONTENT)

CONFIG=configure.load_config(CONFIG_PATH)

def count_labels(df_train, label_col="label"):
    if label_col not in df_train.columns:
        raise ValueError(f"Coluna '{label_col}' não encontrada no DataFrame")

    counts = df_train[label_col].value_counts().sort_values(ascending=False).to_dict()
    return counts
    
def train_test_split_stratify_index(y, test_size=0.38, random_state=42):
    y = np.asarray(y)

    if y.ndim != 1:
        raise ValueError("y must be a 1-dimensional array of labels")

    idx = np.arange(len(y))

    idx_train, idx_test, y_train, y_test = train_test_split(
        idx,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )

    return idx_train, idx_test, y_train, y_test


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(about.__program_csv_split_gui__)
        self.resize(CONFIG["window_width"], CONFIG["window_height"])
        #self.setGeometry(100, 100, 800, 240)

        ## Icon
        # Get base directory for icons
        base_dir_path = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(base_dir_path, 'icons', 'logo.png')
        self.setWindowIcon(QIcon(self.icon_path)) 
        
        self.toolbar = self.addToolBar("Main")
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.generate_toolbar()

        # Central widget (obrigatório no QMainWindow)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QGridLayout()
        central_widget.setLayout(layout)

        # ---------- Input ----------
        label_input = QLabel(CONFIG["window_input"])
        label_input.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(label_input, 0, 0)

        self.input_csv_btn = QPushButton(CONFIG["window_input_button"])
        self.input_csv_btn.setToolTip(CONFIG["window_input_tooltip"])
        self.input_csv_btn.clicked.connect(self.on_input_csv_btn_clicked)
        layout.addWidget(self.input_csv_btn, 1, 0)
        self.input_csv_linedit = QLineEdit(CONFIG["window_input_edit"])
        self.input_csv_linedit.setToolTip(CONFIG["window_input_tooltip"])
        layout.addWidget(self.input_csv_linedit, 1, 1)

        layout.addWidget(QLabel(CONFIG["window_percentage_label"]), 2, 0)
        self.test_factor_spin = QDoubleSpinBox()
        self.test_factor_spin.setDecimals(2)
        self.test_factor_spin.setRange(0.0, 100.0)
        self.test_factor_spin.setSingleStep(0.1)
        self.test_factor_spin.setValue(CONFIG["window_percentage_spin"])
        self.test_factor_spin.setToolTip(CONFIG["window_percentage_spin_tooltip"])
        layout.addWidget(self.test_factor_spin, 2, 1)


        layout.addWidget(QLabel(CONFIG["window_category_column_label"]), 3, 0)
        self.input_category_column_linedit = QLineEdit(CONFIG["window_category_column_lineedit"])
        self.input_category_column_linedit.setToolTip(CONFIG["window_category_column_lineedit_tooltip"])
        layout.addWidget(self.input_category_column_linedit, 3, 1)

        # Adicionar o espaçador
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout.addWidget(spacer, 4, 0)

        # ---------- Output ----------
        label_output = QLabel(CONFIG["window_output"])
        label_output.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(label_output, 5, 0)

        self.csv_out_dir_btn = QPushButton(CONFIG["window_output_dir_button"])
        self.csv_out_dir_btn.setToolTip(CONFIG["window_output_dir_tooltip"])
        layout.addWidget(self.csv_out_dir_btn, 6, 0)
        self.csv_out_dir_linedit = QLineEdit(CONFIG["window_output_dir_lineedit"])
        self.csv_out_dir_linedit.setToolTip(CONFIG["window_output_dir_tooltip"])
        layout.addWidget(self.csv_out_dir_linedit, 6, 1)

        layout.addWidget(QLabel(CONFIG["window_output_train_label"]), 7, 0)
        self.csv_train_filename_linedit = QLineEdit(CONFIG["window_output_train_lineedit"])
        self.csv_train_filename_linedit.setToolTip(CONFIG["window_output_train_lineedit_tooltip"])
        layout.addWidget(self.csv_train_filename_linedit, 7, 1)

        layout.addWidget(QLabel(CONFIG["window_output_test_label"]), 8, 0)
        self.csv_test_filename_linedit = QLineEdit(CONFIG["window_output_test_lineedit"])
        self.csv_test_filename_linedit.setToolTip(CONFIG["window_output_test_lineedit_tooltip"])
        layout.addWidget(self.csv_test_filename_linedit, 8, 1)

        # Adicionar o espaçador
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout.addWidget(spacer, 9, 0)

        self.generate_btn = QPushButton(CONFIG["window_generate_button"])
        self.generate_btn.setToolTip(CONFIG["window_generate_button_tooltip"])
        layout.addWidget(self.generate_btn, 10, 1)

        # ---------- Signals ----------

        self.csv_out_dir_btn.clicked.connect(self.on_csv_out_dir_btn_clicked)
        self.generate_btn.clicked.connect(self.on_generate_btn_clicked)


    def generate_toolbar(self):
        # Adicionar o espaçador
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        #
        self.configure_action = QAction(QIcon.fromTheme("document-properties"), CONFIG["toolbar_configure"], self)
        self.configure_action.setToolTip(CONFIG["toolbar_configure_tooltip"])
        self.configure_action.triggered.connect(self.open_configure_editor)
        
        #
        self.about_action = QAction(QIcon.fromTheme("help-about"), CONFIG["toolbar_about"], self)
        self.about_action.setToolTip(CONFIG["toolbar_about_tooltip"])
        self.about_action.triggered.connect(self.open_about)
        
        # Coffee
        self.coffee_action = QAction(QIcon.fromTheme("emblem-favorite"), CONFIG["toolbar_coffee"], self)
        self.coffee_action.setToolTip(CONFIG["toolbar_coffee_tooltip"])
        self.coffee_action.triggered.connect(self.on_coffee_action_click)

        self.toolbar.addWidget(spacer)
        self.toolbar.addAction(self.configure_action)
        self.toolbar.addAction(self.about_action)
        self.toolbar.addAction(self.coffee_action)

    def open_about(self):
        data={
            "version": about.__version__,
            "package": about.__package__,
            "program_name": about.__program_csv_split_gui__,
            "author": about.__author__,
            "email": about.__email__,
            "description": about.__description__,
            "url_source": about.__url_source__,
            "url_doc": about.__url_doc__,
            "url_funding": about.__url_funding__,
            "url_bugs": about.__url_bugs__
        }
        show_about_window(data,self.icon_path)

    # ---------- Callbacks ----------

    def open_configure_editor(self):
        if os.name == 'nt':  # Windows
            os.startfile(CONFIG_PATH)
        elif os.name == 'posix':  # Linux/macOS
            subprocess.run(['xdg-open', CONFIG_PATH])

    def on_coffee_action_click(self):
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/trucomanx"))

    def on_input_csv_btn_clicked(self):
        default_dir = str(Path.home())
        tmp_str = self.input_csv_linedit.text()

        if tmp_str:
            if os.path.isdir(tmp_str):
                default_dir = tmp_str
            elif os.path.isfile(tmp_str):
                default_dir = os.path.dirname(tmp_str)

        filters = "csv (*.csv)"
        filepath, _ = QFileDialog.getOpenFileName(
            self, CONFIG["window_open_file"], default_dir, filters
        )

        if filepath:
            self.input_csv_linedit.setText(filepath)

    def on_csv_out_dir_btn_clicked(self):
        default_dir = str(Path.home())
        tmp_str = self.input_csv_linedit.text()

        if tmp_str:
            if os.path.isdir(tmp_str):
                default_dir = tmp_str
            elif os.path.isfile(tmp_str):
                default_dir = os.path.dirname(tmp_str)

        filepath = QFileDialog.getExistingDirectory(
            self, CONFIG["window_select_directory"], default_dir
        )

        if filepath:
            self.csv_out_dir_linedit.setText(filepath)

    def on_generate_btn_clicked(self):
        import pandas as pd

        csv_out_dir = self.csv_out_dir_linedit.text()
        csv_train_filename = self.csv_train_filename_linedit.text()
        csv_test_filename = self.csv_test_filename_linedit.text()

        input_csv = self.input_csv_linedit.text()
        test_factor = self.test_factor_spin.value()
        random_state = 42

        csv_train_file = os.path.join(csv_out_dir, csv_train_filename)
        csv_test_file = os.path.join(csv_out_dir, csv_test_filename)

        df = pd.read_csv(input_csv)

        column_name = self.input_category_column_linedit.text().strip()
        
        if   len(column_name) == 0:
            column_name = df.columns[-1]
            y_np = df.iloc[:, -1].to_numpy()
        elif column_name in df.columns:
            y_np = df[column_name].to_numpy()
        else:
            alert = QMessageBox(self)
            alert.setText("Error choosing the category column with name: "+column_name)
            alert.exec()
            return

        d_set = list(set(y_np))
        d_lbl = list(range(len(d_set)))
        mydict = dict(zip(d_set, d_lbl))

        y = np.array([mydict[val] for val in y_np])

        y_train_id, y_test_id, _, _ = train_test_split_stratify_index(
            y,
            test_size=test_factor / 100.0,
            random_state=random_state
        )

        df_train = df.iloc[np.uint32(y_train_id).tolist(), :]
        df_test = df.iloc[np.uint32(y_test_id).tolist(), :]

        df_train.to_csv(csv_train_file, index=False)
        df_test.to_csv(csv_test_file, index=False)
        
        df_train_count = count_labels(df_train, label_col=column_name)
        df_test_count = count_labels(df_test, label_col=column_name)
        
        with open(csv_train_file + ".json", "w") as f:
            json.dump(df_train_count, f, indent=4)

        with open(csv_test_file + ".json", "w") as f:
            json.dump(df_test_count, f, indent=4)

        alert = QMessageBox(self)
        alert.setText("Work end")
        alert.exec()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    create_desktop_directory()    
    create_desktop_menu()
    create_desktop_file(os.path.join("~",".local","share","applications"), 
                        program_name=about.__program_csv_split_gui__)
    
    for n in range(len(sys.argv)):
        if sys.argv[n] == "--autostart":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".config","autostart"), 
                                overwrite=True, 
                                program_name=about.__program_csv_split_gui__)
            return
        if sys.argv[n] == "--applications":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".local","share","applications"), 
                                overwrite=True, 
                                program_name=about.__program_csv_split_gui__)
            return
    
    app = QApplication(sys.argv)
    app.setApplicationName(about.__package__) 
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

