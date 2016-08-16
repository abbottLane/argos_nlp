import csv

import re
from nltk.tokenize import *

from DataLoading import ServerQuery
from DataModeling.DataModels import Document, Event, Patient, Sentence
from SystemUtilities import Configuration
from SystemUtilities.Globals import *
from Extraction.KeywordSearch import KeywordSearch
from os import listdir
from os.path import isfile, join
import sys



def main(environment):
    reload(sys)
    sys.setdefaultencoding('utf8')

    print "Loading training data annotations from labkey server ..."
    annotation_metadata = ServerQuery.get_annotations_from_server()  # testing: stub data only

    if environment == Configuration.RUNTIME_ENV.TRAIN:
        split_set = load_split_info(environment)
        labkey_training_patients = load_labkey_patients(annotation_metadata, split_set)
        return labkey_training_patients

    elif environment == Configuration.RUNTIME_ENV.EXECUTE:
        split_set = load_split_info(Configuration.RUNTIME_ENV.TRAIN) # TODO: split should not be explicitly stated like this. It only is ATM b/c Labkey has no annotated testing data
        labkey_testing_patients = load_labkey_patients(annotation_metadata, split_set)
        return labkey_testing_patients

def load_split_info(environment):
    lines = list()
    if environment == Configuration.RUNTIME_ENV.EXECUTE:
        with open(Configuration.data_dir + "notes_dev_def.txt", "rb") as file:
            lines = file.read().splitlines()
    elif environment == Configuration.RUNTIME_ENV.TRAIN:
        with open(Configuration.data_dir + "notes_train_def.txt", "rb") as file:
            lines = file.read().splitlines()
    return set(lines)


def load_labkey_patients(test_anns, split_set):
    # Load full data note repo from which TRAIN or TEST will pic and return a subset of docs
    noteID_text_dict = load_data_repo(Configuration.NOTE_OUTPUT_DIR)

    labkey_patients = build_patients_from_labkey(test_anns, noteID_text_dict, split_set)
    return labkey_patients


def get_doc_sentences(doc):
    # Split sentences
    split_sentences, sent_spans = split_doc_text(doc.text)

    # Create sentence objects and stuff into doc
    sentence_object_list = list()
    for sent, span in zip(split_sentences, sent_spans):
        sent_obj = Sentence(doc.id, sent, span[0], span[1])
        sentence_object_list.append(sent_obj)

    # Assign doc's keywords to appropriate sentences
    assign_keywords_to_sents(sentence_object_list, doc)
    return sentence_object_list


def split_doc_text(text):
    text= re.sub("\r", "",text) # Carriage Returns are EVIL !!!!!
    sentences = PunktSentenceTokenizer().sentences_from_text(text.encode("utf8"))
    spans = list(PunktSentenceTokenizer().span_tokenize(text.encode("utf8")))
    return sentences, spans


def assign_goldLabels_to_sents(sents, doc):
    doc_gold_events = doc.gold_events
    for gold_event in doc_gold_events:
        if len(gold_event.status_spans) > 0:  # ie if it has a span and is not just a 'dummy' event
            for span in gold_event.status_spans:
                event_span_begin = span.start
                event_span_end = span.stop
                for sent in sents:
                    if event_span_begin > sent.span_in_doc_end:
                        # do nothing
                        tmp = 0
                    elif sent.span_in_doc_start > event_span_end:
                        break  # skip to the next event
                    else:
                        sent.gold_events.append(gold_event)
                        break  # skip to the next event
    pass


def assign_keywords_to_sents(sents, doc):
    """ Used for features in ML as well as assigning attributes to events """
    for event in doc.gold_events:
        substance = event.substance_type
        doc_hits = doc.keyword_hits[substance]
        keyword_index = 0
        sent_index = 0

        # Iterate through both sentences and keywords
        while not (keyword_index == len(doc_hits) or sent_index == len(sents)):
            sent_start = sents[sent_index].span_in_doc_start
            sent_end = sents[sent_index].span_in_doc_end
            keyword_start = doc_hits[keyword_index].span_start
            keyword_end = doc_hits[keyword_index].span_end

            # If current keyword is past current sentence, go to next sentence
            if keyword_start > sent_end:
                sent_index += 1
            # If sentence is past keyword, go to next keyword
            elif sent_start > keyword_end:
                keyword_index += 1
            # Else, they overlap and keyword should be assigned to sentence
            else:
                sents[sent_index].keyword_hits[substance].append(doc_hits[keyword_index])
                keyword_index += 1


def populate_event(doc, gold_label, substance, regex):
    event = Event(substance)

    event.status = gold_label.rstrip()
    if event.status != "":
        doc.gold_events.append(event)

    load_doc_keywords(doc, substance, regex)


def load_doc_keywords(doc, substance, regex):
    hits = KeywordSearch.find_doc_hits(doc, regex)
    doc.keyword_hits[substance].extend(hits)


def load_patient_labels(patient_gold_labels_path):
    pid_label = dict()
    if patient_gold_labels_path is not None:
        with open(patient_gold_labels_path, "rb") as file:
            lines = file.readlines()
        for line in lines:
            id_label = line.split()
            pid_label[id_label[0]] = id_label[1]
    return pid_label


def load_data_repo(NOTE_OUTPUT_DIR):
    id_text_dict = dict()
    all_notes = [f for f in listdir(NOTE_OUTPUT_DIR) if isfile(join(NOTE_OUTPUT_DIR, f))]
    for note in all_notes:
        with open(NOTE_OUTPUT_DIR + "\\" + note, "rb") as f:
            id_text_dict[note] = f.read()
    return id_text_dict


def get_labkey_documents(annId_patient_dict, docID_text_dict, split_set):
    annotater_ids = sorted(annId_patient_dict.keys())
    labkey_documents = list()
    for annotater_id in annotater_ids:
        patient_dict = annId_patient_dict[annotater_id]
        pat_ids = sorted(patient_dict.keys())
        for pat_id in pat_ids:
            docId_events = patient_dict[pat_id]  # {patientId : {eventType : EventObject}}
            for docId, event_dict in docId_events.iteritems():
                if docId in split_set:
                    doc_obj = Document(docId, docID_text_dict[docId])
                    # populate the docObj's event list
                    for type, event in event_dict.iteritems():
                        doc_obj.gold_events.append(event)
                    # split and assign document sentences from raw text
                    doc_obj.sent_list = get_doc_sentences(doc_obj)
                    labkey_documents.append(doc_obj)
                    # Match spans to sentence level
                    assign_goldLabels_to_sents(doc_obj.sent_list, doc_obj)

    return labkey_documents


def get_labkey_patients(labkey_documents):
    patients_dict = dict()
    patients_list = list()
    for doc in labkey_documents:
        patId = doc.id.split("_")[0]
        if patId not in patients_dict:
            patients_dict[patId] = list()
            patients_dict[patId].append(doc)
        else:
            patients_dict[patId].append(doc)

    for pid, doclist in patients_dict.iteritems():
        patient = Patient(pid)
        patient.doc_list = doclist
        patients_list.append(patient)
    return patients_list


def build_patients_from_labkey(annId_patient_dict, docID_text_dict, split_set):
    labkey_documents = get_labkey_documents(annId_patient_dict, docID_text_dict, split_set)
    labkey_patients = get_labkey_patients(labkey_documents)
    return labkey_patients


if __name__ == '__main__':
    main(Configuration.RUNTIME_ENV.TRAIN)
