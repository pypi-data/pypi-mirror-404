from dttlib import AnalysisNameId, ChannelName
from qtpy.QtWidgets import QDialogButtonBox
from qtpy.QtCore import Signal

from ndscope._qt import load_ui

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from ndscope.channel_select import ChannelConfigWidget


class Field:
    def __init__(self, name: str, symbol: str, bound: bool):
        """
        The symbol is the one-character symbol used in types
        if bound is true, the Field is bound to itself.
        """
        self.name = name
        self.symbol = symbol
        self.bind_value = self

    def __str__(self) -> str:
        return self.symbol

    def __eq__(self, other) -> bool:
        return other.bind_value is not None and self.bind_value == other.bind_value

    def unify(self, other):
        """If self is unbound, bind it to other
        unless other is unbound, then do nothing.

        If self is bound, raise an exception of
        unequal to other
        """
        if self.bind_value is None:
            self.bind_value = other.bind_value
        elif self != other:
            raise ValueError(
                "Attempted to bind an already bound field to an unequal field"
            )


time_field = Field("time", "t", True)
real_field = Field("real", "R", True)
complex_field = Field("complex", "C", True)
frequency_field = Field("frequency", "f", True)


def fieldvar(name: str) -> Field:
    """Create an unbound field variable"""
    return Field(name, f"<{name}>", False)


class ArrayType(object):
    def __init__(self, domain: Field, range: Field):
        self.domain = domain
        self.range = range

    def __str__(self) -> str:
        return f"{self.domain},{self.range}"


class Input(object):
    def __init__(self, name: Optional[str], array_type: ArrayType):
        self.name = name
        self.array_type = array_type


class Operator(object):
    def __init__(
        self,
        name: str,
        input_a: Input,
        input_b: Optional[Input],
        output_type: ArrayType,
        description: str,
    ):
        self.name = name
        self.input_a = input_a
        self.input_b = input_b
        self.output_type = output_type
        self.description = description
        self.num_inputs = (input_b is not None) and 2 or 1


# a common array type
X_R = ArrayType(fieldvar("X"), real_field)
X_C = ArrayType(fieldvar("X"), complex_field)

# the array time of almost all raw channels
t_R = ArrayType(time_field, real_field)

_built_in_operators = [
    Operator(
        "complex",
        Input("real", X_R),
        Input("imag.", X_R),
        X_C,
        """Convert a real signal and an imaginary signal into a complex signal.""",
    ),
    Operator(
        "phase",
        Input(None, X_C),
        None,
        X_R,
        """Calculate the phase of a complex signal.<br/>
             
The phase is always between -π and +π""",
    ),
]


class MathRegistry(dict):
    """
    A collection of created math traces stored by the short name
    """

    def __init__(self):
        self._reverse_table: Dict[AnalysisNameId, str] = {}

    def __setitem__(self, key: str, value: AnalysisNameId):
        if key in self:
            raise KeyError(f"'{key}' already present in MathRegistry")
        if value in self._reverse_table:
            raise KeyError("AnalysisNameId already present in MathRegistry")
        super().__setitem__(key, value)
        self._reverse_table[value] = key

    def reverse_lookup(self, key: AnalysisNameId) -> str:
        return self._reverse_table[key]

    def __delitem__(self, key: str) -> None:
        value = self[key]
        del self._reverse_table[value]
        return super().__delitem__(key)

    def reverse_del(self, value: AnalysisNameId):
        key = self._reverse_table[value]
        del self[key]


class MathConfigDialog(*load_ui("math_config.ui")):
    update_status_signal = Signal()
    math_registry = MathRegistry()

    def __init__(
        self,
        parent,
        channel_config: "ChannelConfigWidget",
        input_a_name: str,
        input_b_name: str,
    ):
        """
        channel_config is the configuration dialog that will get the new math signal
        input_a and input_b are Channel or Short name
        """
        self.channel_config = channel_config

        super().__init__(parent)
        self.setupUi(self)

        self.input_a_edit.setText(input_a_name)
        self.input_b_edit.setText(input_b_name)

        self.dialog_button_box.accepted.connect(self.accept)
        self.dialog_button_box.rejected.connect(self.reject)
        self.swap_inputs_button.clicked.connect(self.swap_inputs_action.trigger)
        self.swap_inputs_action.triggered.connect(self.swap_inputs)
        self.operator_list.itemSelectionChanged.connect(self.item_activated)
        self._operator: Optional[Operator] = None
        self.operators: Dict[str, Operator] = {}
        self.get_operators()
        self.update_status_signal.connect(self.update_status)
        self.input_a_edit.textChanged.connect(self.update_status)
        self.input_b_edit.textChanged.connect(self.update_status)
        self.short_name_edit.textChanged.connect(self.update_status)
        self.update_status()

    def get_operators(self):
        global _built_in_operators
        for op in _built_in_operators:
            self.operators[op.name] = op
        self.operator_list.addItems(self.operators.keys())

    def swap_inputs(self):
        x = self.input_a_edit.text()
        y = self.input_b_edit.text()
        self.input_a_edit.setText(y)
        self.input_b_edit.setText(x)
        self.update_status_signal.emit()

    def check_status(self) -> Tuple[str, str]:
        """
        Return true if there's an error
        false if only a warning, and a status message.
        if empty string, no warning
        """

        if self._operator is None:
            return "ERROR", "No operator selected"

        # input checks
        if not self.input_a_edit.text():
            set_red(self.input_a_edit)
            return "ERROR", "There's nothing in the first input"
        clear_color(self.input_a_edit)

        if self._operator.input_b is not None and not self.input_b_edit.text():
            set_red(self.input_b_edit)
            return "ERROR", "There's nothing in the second input"
        clear_color(self.input_b_edit)

        # short name checks
        if self.short_name_edit.text() in self.math_registry:
            set_red(self.short_name_edit)
            return "ERROR", "Short name already in use"
        if self.short_name_edit.text() == "":
            set_red(self.short_name_edit)
            return "ERROR", "No short name provided"
        clear_color(self.short_name_edit)

        return "OK", "Status Ok"

    def update_status(self):
        error_level, msg = self.check_status()

        if error_level == "ERROR":
            set_red(self.status_line_edit)
            for button in self.dialog_button_box.buttons():
                if (
                    self.dialog_button_box.buttonRole(button)
                    == QDialogButtonBox.ButtonRole.AcceptRole
                ):
                    button.setDisabled(True)
        elif error_level == "WARNING":
            set_yellow(self.status_line_edit)
            for button in self.dialog_button_box.buttons():
                if (
                    self.dialog_button_box.buttonRole(button)
                    == QDialogButtonBox.ButtonRole.AcceptRole
                ):
                    button.setDisabled(False)
        else:
            self.status_line_edit.setStyleSheet("")
            for button in self.dialog_button_box.buttons():
                if (
                    self.dialog_button_box.buttonRole(button)
                    == QDialogButtonBox.ButtonRole.AcceptRole
                ):
                    button.setDisabled(False)
        self.status_line_edit.setText(msg)
        self.update_operator()

    def item_activated(self):
        items = self.operator_list.selectedItems()
        if len(items) == 0:
            self._operator = None
        else:
            item = items[0]
            self._operator = self.operators[item.text()]

        self.update_operator()
        self.update_status_signal.emit()

    def update_operator(self):
        if self._operator is not None:
            self.operator_description.setHtml(self._operator.description)
            if self._operator.input_a.name is not None:
                self.input_a_label.setText(self._operator.input_a.name)
            else:
                self.input_a_label.setText("Input A")
            if (
                self._operator.input_b is not None
                and self._operator.input_b.name is not None
            ):
                self.input_b_label.setText(self._operator.input_b.name)
            else:
                self.input_b_label.setText("Input B")
            self.operator_edit.setText(self._operator.name)
            self.num_inputs_edit.setText(str(self._operator.num_inputs))
            self.input_a_type_edit.setText(str(self._operator.input_a.array_type))
            if self._operator.input_b is None:
                self.input_b_type_edit.setText("")
                self.input_b_type_edit.setDisabled(True)
            else:
                self.input_b_type_edit.setDisabled(False)
                self.input_b_type_edit.setText(str(self._operator.input_b.array_type))
            self.out_type_edit.setText(str(self._operator.output_type))

            # long name
            rid = self.convert_operator_to_name_id()
            self.long_name_edit.setText(str(rid))
        else:
            self.operator_description.setHtml("")

    @classmethod
    def name_to_name_id(cls, name: str) -> AnalysisNameId:
        try:
            rid = cls.math_registry[name]
        except KeyError:
            chan = ChannelName(name)
            rid = AnalysisNameId.from_channel(chan)
        return rid

    def convert_operator_to_name_id(self) -> AnalysisNameId:
        # create a new analysis name and add it to the registry
        if self._operator is None:
            raise ValueError("Accepting an empty operator is not allowed")
        operator = self._operator.name

        input_names = [self.input_a_edit.text(), self.input_b_edit.text()]

        input_ids = []
        for i in range(self._operator.num_inputs):
            rid = self.name_to_name_id(input_names[i])
            input_ids.append(rid)

        return AnalysisNameId(operator, input_ids)

    def accept(self):
        short_name = self.short_name_edit.text()
        self.math_registry[short_name] = self.convert_operator_to_name_id()

        super().accept()


def set_red(widget):
    widget.setStyleSheet("QLineEdit { background-color: #FFB6C6; }")


def set_yellow(widget):
    widget.setStyleSheet("QLineEdit { background-color: #FFFFAA; }")


def clear_color(widget):
    widget.setStyleSheet("")
