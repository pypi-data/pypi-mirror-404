#!/usr/bin/env python3

import sys
import os
import json
import signal
import subprocess
import WorkingWithFiles as rnfunc

from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QGridLayout,
    QHBoxLayout,
    QCheckBox,
    QPushButton,
    QLabel,
    QLineEdit,
    QRadioButton,
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
                            "config."+about.__program_csv_gen_gui__+".json" )

DEFAULT_CONTENT={   "toolbar_configure": "Configure",
                    "toolbar_configure_tooltip": "Open the configure Json file",
                    "toolbar_about": "About",
                    "toolbar_about_tooltip": "About the program",
                    "toolbar_coffee": "Coffee",
                    "toolbar_coffee_tooltip": "Buy me a coffee (TrucomanX)",
                    "window_input": "<b>Input:</b>",
                    "window_base_directory": "Base directory:",
                    "window_base_directory_tooltip": "Select the base directory to scan files.",
                    "window_base_directory_default": "./",
                    "window_search_type_label": "Search type:",
                    "window_search_type": "Image search: ON / CSV search: OFF",
                    "window_search_type_tooltip": "Check to scan files in IMAGE format, or uncheck to scan only certain types of CSV files.",
                    "window_file_type_label": "file type:",
                    "window_file_type_image_default": ".png",
                    "window_file_type_csv_default": ".csv",
                    "window_file_type_tooltip": "Extensions of file types to be scanned: in images, these can be <b>.png</b>, <b>.jpg</b>, <b>.jpeg</b>, <b>.bmp</b>, etc. In CSV files, these can be <b>.csv</b>, <b>.CSV</b>, etc.",
                    "window_output": "<b>Output:</b>",
                    "window_output_csv_dir": "CSV file directory:",
                    "window_output_csv_dir_default": "./",
                    "window_output_csv_dir_tooltip": "The location of the directory where the *.csv file and the corresponding *.csv.json file will be stored.",
                    "window_output_csv_filename_label": "CSV filename:",
                    "window_output_csv_filename_default": "labels.csv",
                    "window_output_csv_filename_tooltip": "The output CSV filename, in this file a new <b>category column</b> is added where the label of each analyzed file will be stored. Go to the configuration file and edit 'window_output_csv_filename_category_column' to change the new <b>category column</b> name (Needed to reboot the program).",
                    "window_output_csv_filename_path_column": "filename",
                    "window_output_csv_filename_category_column": "label",
                    "window_output_category_label": "Category:",
                    "window_output_category_method_last": "Last folder name",
                    "window_output_category_method_first": "First folder name",
                    "window_output_category_method_last_tooltip": "The last subfolder name is considered the category of the file.",
                    "window_output_category_method_first_tooltip": "The first subfolder name is considered the category of the file.",
                    "window_generate": "Generate",
                    "window_generate_tooltip": "Generate the <b>*.csv</b> and <b>*.csv.json</b> files.",
                    "window_generate_result_message": "Found {count} files with the categories: {categories}",
                    "window_select_directory": "Select Directory",
                    "window_width": 500,
                    "window_height": 450
                }

configure.verify_default_config(CONFIG_PATH,default_content=DEFAULT_CONTENT)

CONFIG=configure.load_config(CONFIG_PATH)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(about.__program_csv_gen_gui__)
        #self.setGeometry(100, 100, 800, 240)
        self.resize(CONFIG["window_width"], CONFIG["window_height"])

        ## Icon
        # Get base directory for icons
        base_dir_path = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(base_dir_path, 'icons', 'logo.png')
        self.setWindowIcon(QIcon(self.icon_path)) 
        
        self.toolbar = self.addToolBar("Main")
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.generate_toolbar()
        

        # Central widget (QMainWindow exige isso)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QGridLayout()
        central_widget.setLayout(layout)

        ## Row pretty label
        label_input = QLabel(CONFIG["window_input"])
        label_input.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(label_input, 0, 0)

        ## Row images directory
        self.base_dir_btn = QPushButton(CONFIG["window_base_directory"])
        self.base_dir_btn.setToolTip(CONFIG["window_base_directory_tooltip"])
        layout.addWidget(self.base_dir_btn, 1, 0)
        self.base_dir_linedit = QLineEdit(CONFIG["window_base_directory_default"])
        self.base_dir_linedit.setToolTip(CONFIG["window_base_directory_tooltip"])
        layout.addWidget(self.base_dir_linedit, 1, 1)

        ## Row search type
        layout.addWidget(QLabel(CONFIG["window_search_type_label"]), 2, 0)
        self.search_type_btn = QCheckBox(CONFIG["window_search_type"])
        self.search_type_btn.setToolTip(CONFIG["window_search_type_tooltip"])
        self.search_type_btn.setChecked(True)
        self.search_type_btn.stateChanged.connect(self.on_search_type_changed)
        layout.addWidget(self.search_type_btn, 2, 1)

        ## Row file type
        layout.addWidget(QLabel(CONFIG["window_file_type_label"]), 3, 0)
        self.file_type_linedit = QLineEdit(CONFIG["window_file_type_image_default"])
        self.file_type_linedit.setToolTip(CONFIG["window_file_type_tooltip"])
        layout.addWidget(self.file_type_linedit, 3, 1)

        # Adicionar o espaçador
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout.addWidget(spacer, 4, 0)

        ## Row pretty label
        label_output = QLabel(CONFIG["window_output"])
        label_output.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(label_output, 5, 0)

        ## Row CSV directory
        self.csv_dir_btn = QPushButton(CONFIG["window_output_csv_dir"])
        self.csv_dir_btn.setToolTip(CONFIG["window_output_csv_dir_tooltip"])
        layout.addWidget(self.csv_dir_btn, 6, 0)
        self.csv_dir_linedit = QLineEdit(CONFIG["window_output_csv_dir_default"])
        self.csv_dir_linedit.setToolTip(CONFIG["window_output_csv_dir_tooltip"])
        layout.addWidget(self.csv_dir_linedit, 6, 1)

        ## Row CSV filename
        layout.addWidget(QLabel(CONFIG["window_output_csv_filename_label"]), 7, 0)
        self.csv_filename_linedit = QLineEdit(CONFIG["window_output_csv_filename_default"])
        self.csv_filename_linedit.setToolTip(CONFIG["window_output_csv_filename_tooltip"])
        layout.addWidget(self.csv_filename_linedit, 7, 1)

        ## Row category
        layout.addWidget(QLabel(CONFIG["window_output_category_label"]), 8, 0)
        hlayout = QHBoxLayout()
        self.rb_last = QRadioButton(CONFIG["window_output_category_method_last"])
        self.rb_first = QRadioButton(CONFIG["window_output_category_method_first"])
        self.rb_last.setToolTip(CONFIG["window_output_category_method_last_tooltip"])
        self.rb_first.setToolTip(CONFIG["window_output_category_method_first_tooltip"])
        self.rb_first.setChecked(True)
        hlayout.addWidget(self.rb_last)
        hlayout.addWidget(self.rb_first)
        layout.addLayout(hlayout, 8, 1)

        ## 
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout.addWidget(spacer, 9, 0)

        ## Row generate button
        self.generate_btn = QPushButton(CONFIG["window_generate"])
        self.generate_btn.setToolTip(CONFIG["window_generate_tooltip"])
        layout.addWidget(self.generate_btn, 10, 1)

        # Signals
        self.base_dir_btn.clicked.connect(self.on_base_dir_btn_clicked)
        self.csv_dir_btn.clicked.connect(self.on_csv_dir_btn_clicked)
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

    def on_search_type_changed(self, state):
        checked = self.search_type_btn.isChecked()
        if checked:
            self.file_type_linedit.setText(CONFIG["window_file_type_image_default"])
        else:
            self.file_type_linedit.setText(CONFIG["window_file_type_csv_default"])

    def open_configure_editor(self):
        if os.name == 'nt':  # Windows
            os.startfile(CONFIG_PATH)
        elif os.name == 'posix':  # Linux/macOS
            subprocess.run(['xdg-open', CONFIG_PATH])

    def open_about(self):
        data={
            "version": about.__version__,
            "package": about.__package__,
            "program_name": about.__program_csv_gen_gui__,
            "author": about.__author__,
            "email": about.__email__,
            "description": about.__description__,
            "url_source": about.__url_source__,
            "url_doc": about.__url_doc__,
            "url_funding": about.__url_funding__,
            "url_bugs": about.__url_bugs__
        }
        show_about_window(data,self.icon_path)

    def on_coffee_action_click(self):
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/trucomanx"))
    
    def on_base_dir_btn_clicked(self):
        filepath = QFileDialog.getExistingDirectory(self, CONFIG["window_select_directory"])
        if filepath:
            self.base_dir_linedit.setText(filepath)

    def on_csv_dir_btn_clicked(self):
        filepath = QFileDialog.getExistingDirectory(self, CONFIG["window_select_directory"])
        if filepath:
            self.csv_dir_linedit.setText(filepath)

    def on_generate_btn_clicked(self):
        base_dir = self.base_dir_linedit.text()
        file_type = self.file_type_linedit.text()
        csv_dir = self.csv_dir_linedit.text()
        csv_filename = self.csv_filename_linedit.text()
        search_image = self.search_type_btn.isChecked()
        rb_first_down = self.rb_first.isChecked()

        format_list = [file_type]
        csv_file = os.path.join(csv_dir, csv_filename)

        if search_image:
            res, Count = rnfunc.generate_csv_file_from_dir_structure(
                base_dir,
                format_list,
                csv_file,
                header = [CONFIG["window_output_csv_filename_path_column"], CONFIG["window_output_csv_filename_category_column"]],
                label_first=rb_first_down
            )
        else:
            res, Count = rnfunc.generate_csv_file_from_csv_dir_structure(
                base_dir,
                format_list,
                csv_file,
                input_has_header=True,
                output_header_list='default',
                new_column=CONFIG["window_output_csv_filename_category_column"],
                label_first=rb_first_down,
                processing_func=None
            )

        # Save JSON summary
        with open(csv_file + ".json", "w") as f:
            json.dump(Count, f, indent=4)

        msg = CONFIG["window_generate_result_message"].format(
            count=len(res),
            categories=Count
        )
        alert = QMessageBox(self)
        alert.setText(msg)
        alert.exec()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    create_desktop_directory()    
    create_desktop_menu()
    create_desktop_file(os.path.join("~",".local","share","applications"), 
                        program_name=about.__program_csv_gen_gui__)
    
    for n in range(len(sys.argv)):
        if sys.argv[n] == "--autostart":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".config","autostart"), 
                                overwrite=True, 
                                program_name=about.__program_csv_gen_gui__)
            return
        if sys.argv[n] == "--applications":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".local","share","applications"), 
                                overwrite=True, 
                                program_name=about.__program_csv_gen_gui__)
            return
    
    app = QApplication(sys.argv)
    app.setApplicationName(about.__package__) 
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

