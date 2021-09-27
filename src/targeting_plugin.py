import utils
from n5_converter import OnTheFlyOverviewN5Converter
import os
from configparser import ConfigParser


class TargetingPlugin:
    N5_CONVERSION_MSG = "CONVERT OV TO N5"
    SECTION_NAME = "targeting"

    def __init__(self, main_controls):
        self._ui = main_controls
        self._acq = main_controls.acq
        self._ovm = main_controls.ovm
        self._config = None
        self._get_targeting_config()
        self._ui.checkBox_n5Conversion.setChecked(self._config.getboolean(self.SECTION_NAME, "convert_to_n5"))
        self.update_ov(self._config.getint(self.SECTION_NAME, "selected_ov"))
        self._n5_converter = None

    def update_ov(self, current_index=None):
        ov_combobox = self._ui.comboBox_ovId
        ovm = self._ui.ovm

        if current_index is None:
            current_index = ov_combobox.currentIndex()
        if current_index == -1:
            current_index = 0

        ov_combobox.blockSignals(True)
        ov_combobox.clear()
        ov_list_str = [str(r) for r in range(0, ovm.number_ov)]
        ov_combobox.addItems(ov_list_str)
        if current_index > len(ov_list_str) - 1:
            current_index = 0
        ov_combobox.setCurrentIndex(current_index)
        ov_combobox.blockSignals(False)

    def _get_targeting_config(self):
        targeting_config_path = os.path.join(self._acq.base_dir, "meta", "targeting.ini")
        if os.path.isfile(targeting_config_path):
            config = ConfigParser()
            with open(targeting_config_path, 'r') as file:
                config.read_file(file)
        else:
            # Make sensible defaults and save new targeting config
            config = ConfigParser()
            config.add_section(self.SECTION_NAME)
            config[self.SECTION_NAME]["selected_ov"] = "0"
            config[self.SECTION_NAME]["convert_to_n5"] = "False"
            self._save_targeting_config(config)

        self._config = config

    def _save_targeting_config(self, config):
        targeting_config_path = os.path.join(self._acq.base_dir, "meta", "targeting.ini")

        if not os.path.exists(targeting_config_path):
            success, exception_str = utils.create_subdirectories(self._acq.base_dir, ['meta'])
            if not success:
                # TODO - handle this error properly?
                return

        with open(targeting_config_path, 'w') as f:
            config.write(f)

    def selected_ov(self):
        return self._ui.comboBox_ovId.currentIndex()

    def is_convert_to_n5_active(self):
        return self._ui.checkBox_n5Conversion.isChecked()

    def restrict_gui(self, b):
        self._ui.comboBox_ovId.setEnabled(b)
        self._ui.checkBox_n5Conversion.setEnabled(b)

    def update_targeting_plugin_settings(self):

        # update targeting config
        self._config[self.SECTION_NAME]["selected_ov"] = str(self.selected_ov())
        self._config[self.SECTION_NAME]["convert_to_n5"] = str(self.is_convert_to_n5_active())
        self._save_targeting_config(self._config)

        # update n5 converter settings
        if self.is_convert_to_n5_active():
            if self._n5_converter is None:
                self._n5_converter = OnTheFlyOverviewN5Converter(self._acq, self._ovm,
                                                                 self.selected_ov())
            elif self._acq.base_dir != self._n5_converter.base_dir or \
                    self._acq.stack_name != self._n5_converter.stack_name or \
                    self.selected_ov() != self._n5_converter.ov_index:
                self._n5_converter = OnTheFlyOverviewN5Converter(self._acq, self._ovm,
                                                                 self.selected_ov())
            else:
                self._n5_converter.update_ov_settings()

    def handle_message(self, msg):
        ov_index = int(msg[len(self.N5_CONVERSION_MSG):])
        if self._n5_converter is not None:
            if ov_index == self._n5_converter.ov_index and self.is_convert_to_n5_active():
                self._write_ov_to_n5()

    def _write_ov_to_n5(self):
        relative_ov_path = utils.ov_relative_save_path(self._acq.stack_name, self._n5_converter.ov_index,
                                                       self._acq.slice_counter)
        path_to_tiff_slice = os.path.join(self._acq.base_dir, relative_ov_path)
        self._n5_converter.write_slice(path_to_tiff_slice)


