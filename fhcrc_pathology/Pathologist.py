#
# Copyright (c) 2014-2015 Fred Hutchinson Cancer Research Center
#
# Licensed under the Apache License, Version 2.0: http://www.apache.org/licenses/LICENSE-2.0
#

'''author@esilgard'''
__version__='Pathologist1.0'

from OneFieldPerReport import OneFieldPerReport
import global_strings as dict_keys

class Pathologist(OneFieldPerReport):
    __version__='Pathologist1.0'
    
    def __init__(self):
        self.field_name='Pathologist'
        self.regex=r'\n([A-Za-z\'\-,. ]+) MD(, PhD)?[ ]*\n[ ]*Pathologist[ ]*\n'
        self.confidence=1
        self.match_style='first'
        self.table=dict_keys.PATHOLOGY_TABLE
        self.value_type='match'
