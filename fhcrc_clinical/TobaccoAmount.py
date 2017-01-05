from SubstanceInfoField import SubstanceField
from fhcrc_clinical.SocialHistories.DataLoading.DataLoadingGlobals import *


class TobaccoAmount(SubstanceField):
    __version__ = 'SubstanceInfo1.0'

    def __init__(self):
        SubstanceField.__init__(self)
        self.field_name = 'TobaccoAmount'
        self.table = SOC_HISTORIES
        self.substance = "Tobacco"
        self.field = "Alcohol"
