# coding=utf-8
from itertools import chain
import nltk
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelBinarizer
import sklearn
import pycrfsuite

from fhcrc_clinical.SocialHistories.Extraction.AttributeExtraction.Execution_CRFSuite import test
from fhcrc_clinical.SocialHistories.Extraction.AttributeExtraction.Processing_CRFSuite import sent2features, \
    get_sentences_with_subsinfo_from_patients
from fhcrc_clinical.SocialHistories.SystemUtilities.Configuration import ATTRIB_EXTRACTION_DIR_HOME
from fhcrc_clinical.SocialHistories.SystemUtilities import Debug_Methods
from fhcrc_clinical.SocialHistories.SystemUtilities.Globals import entity_types


def train(patients, model_path=ATTRIB_EXTRACTION_DIR_HOME):
    print "training Subs_Amount tagger ..."
    sentence_objs = get_sentences_with_subsinfo_from_patients(patients)
    for type in entity_types:
        model_name = model_path + r"Models/" + "model-" + type + ".ser.gz"
        training_sents, training_labels = load_train_data(sentence_objs,type)
        #DEBUG
        Debug_Methods.write_training_data_as_file(training_sents, training_labels, sentence_objs)
        #END DEBUG
        x_train, y_train = get_features_and_labels(training_sents, training_labels)
        train_data(x_train, y_train, model_name+"wl")
        print("CRF model written to: " + model_name+"wl")
        #test("Blurb smokes 1-2 packs per day. He quit 3 days ago. He smoked for 34 years. Alcohol Use: infrequent (1 drink or less/day)", model_name)


def load_train_data(sentences, type):
    tokenized_sentences=list()
    tokenized_labels=list()
    for sent_obj in sentences:
        sentence_toks = list()
        label_toks = list()
        if len(sent_obj.gold_events) > 0: # if the sentence is predicted to have an event
            sentence = sent_obj.text
            # #DEBUG
            # if "1 drink or less/day" in sentence:
            #    pause=9
            gold_event_set = sent_obj.gold_events
            sent_offset = sent_obj.span_in_doc_start
            for match in nltk.re.finditer("\S+", sentence):
                start = match.start()
                end = match.end()
                pointer = sent_offset + start
                word = match.group(0)
                sentence_toks.append(word)
                answer = "0"
                debug_str = ""
                appended=False
                for entity in gold_event_set:
                    if answer != "0":
                        break
                    attr_dict = entity.attributes
                    for attr in attr_dict:
                        for span in attr_dict[attr].all_value_spans:
                            attr_start = int(span.start)
                            attr_end = int(span.stop)
                            if attr_dict[attr].type == type and \
                                                    attr_start <= pointer <= attr_end: # < attr_end
                                answer = type
                                label_toks.append(answer)
                                appended =True
                                break
                if not appended:
                    label_toks.append(answer)
        tokenized_sentences.append(sentence_toks)
        tokenized_labels.append(label_toks)
    return tokenized_sentences, tokenized_labels


def train_data(x_train, y_train, model_name):
    trainer = pycrfsuite.Trainer(verbose=False)
    for xseq, yseq in zip(x_train, y_train):
        trainer.append(xseq, yseq)

    trainer.set_params({
        'c1': 1.0,  # coefficient for L1 penalty
        'c2': 1e-3,  # coefficient for L2 penalty
        'max_iterations': 50,  # stop earlier

        # include transitions that are possible, but not observed
        'feature.possible_transitions': True
    })
    trainer.train(model_name) # produces model file with this name
    pass


def get_features_and_labels(sents, labels):
    # Tag for POS
    tagged_sents = list()
    for sent in sents:
        tagged_sent = nltk.pos_tag(sent)
        tagged_sents.append(tagged_sent)

    x = [sent2features(s) for s in tagged_sents]
    y = labels #[sent2labels(s) for s in labels]
    return x, y