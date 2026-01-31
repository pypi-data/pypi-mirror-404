# coding=utf-8
from dragonfly.properties import ModelProperties
from .properties.model import ModelIesveProperties


# set a hidden iesve attribute on each core geometry Property class to None
# define methods to produce iesve property instances on each Property instance
ModelProperties._iesve = None


def model_iesve_properties(self):
    if self._iesve is None:
        self._iesve = ModelIesveProperties(self.host)
    return self._iesve


# add iesve property methods to the Properties classes
ModelProperties.iesve = property(model_iesve_properties)
