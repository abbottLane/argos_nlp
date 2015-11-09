'''author@esilgard'''
#
# Copyright (c) 2013-2015 Fred Hutchinson Cancer Research Center
#
# Licensed under the Apache License, Version 2.0: http://www.apache.org/licenses/LICENSE-2.0
#

import re
import global_strings as gb
import numpy as np
from scipy.sparse import dok_matrix

class OneFieldPerReportML(object):
    '''
    extract the value of a field which has one value per report using a scikit learn ML model
    '''
    __version__ = 'OneFieldPerReportML1.0'

    def __init__(self):
        self.field_name = 'Default'
        self.keyword_patterns = {}
        self.return_d = {}
        self.confidence = 0.0
        self.table = 'Default'
        self.window = 0
        self.model = None
        self.feature_mapping = {}
        self.class_label_mapping = {}

    def get_version(self):
        ''' return the algorithm version '''
        return self.__version__

    def tokenize_and_vectorize(self, full_text):
        '''
        rudimentry tokenization and a hardcoded skip(2)gram model
        the window around the keyword is variable
        '''
        text = re.sub(r'[.,:;\"\'\(\)\*]', ' ', full_text.lower())
        token = text.split()
        vec = set([])
        word = False
        for v in range(len(token)):
            current = token[v]
            for kw, pattern in self.keyword_patterns.items():
                if re.search(pattern, current):
                    word = True
                    vec.add(kw)
                    ## place holder for character offset addition...
                    ## might be helpful to at least highlight the original keywords in the text?
                    pre = v-self.window
                    while v > pre >= 0:
                        #unigrams
                        vec.add(kw + 'pre_window=' + token[pre])
                        if  v-1 > pre:
                            #bigrams
                            vec.add(kw + 'pre_window=' + token[pre] + '_' + token[pre+1])
                            if v-2 > pre:
                                #one skipgram
                                vec.add(kw + 'pre_window=' + token[pre] + '_' + token[pre+2])
                                if v-3 > pre:
                                    #two skipgram
                                    vec.add(kw + 'pre_window=' + token[pre] + '_' + token[pre+3])
                        pre += 1
                    post = v+1
                    while post < min(len(text), v+self.window):
                        #unigrams
                        vec.add(kw + 'post_window=' + token[post])
                        if  post < len(text)-1:
                            #bigrams
                            vec.add(kw + 'post_window=' + token[post] + '_' + token[post+1])
                            if post < len(text)-2:
                                #one skipgram
                                vec.add(kw + 'post_window=' + token[post] + '_' + token[post+2])
                                if post < len(text)-3:
                                    #one skipgram
                                    vec.add(kw + 'post_window=' + token[post] + '_' + token[post+3])
                        post += 1
        if word == False:
            vec.add('NO_keyword_IN_TEXT')
        return vec

    def get(self, disease_group, dictionary):
        ''' return class label for the text string based on SVM classification '''
        full_text = dictionary[(-1, 'FullText', 0, None)]
        self.return_d={gb.NAME: self.field_name, gb.VALUE: None, gb.CONFIDENCE: '%.2f' % 0.0, \
                                gb.KEY: gb.ALL, gb.VERSION: self.get_version(), \
                                gb.STARTSTOPS: [], gb.TABLE: self.table}
        ## tokenize and turn into a sparse feature vector of binary features
        feat_vector = self.tokenize_and_vectorize(full_text)
        ## map string features to svm integers according to the feature mapping in the model
        feat_array = [self.feature_mapping.get(f) for f in feat_vector if f in self.feature_mapping]
        ## dictionary of keys type sparse array is easily confertable to sparse column matrix
        X = dok_matrix((1, self.features_in_model), dtype=np.float64)
        for f in feat_array:
            X[0, f] = 1
        ## convert dictionary of keys into a sparse column matrix (sparse features)
        X.tocsc()
        class_label = self.model.predict(X)[0]
        if class_label:
            self.return_d[gb.VALUE] = self.class_label_mapping[class_label]
            self.return_d[gb.CONFIDENCE] = ('%.2f' % self.confidence)
        return ([self.return_d], list)
