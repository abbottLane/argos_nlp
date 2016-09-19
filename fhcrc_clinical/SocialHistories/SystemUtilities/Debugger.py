from fhcrc_clinical.SocialHistories.SystemUtilities import Configuration


def print_status_classification_results(sentences, classifications, event_type):
    with open(Configuration.DATA_DIR + "status_classification_"+event_type+ "_debug.txt", "wb") as file:
        for i in range(0, len(sentences)-1, 1):
            sent = sentences[i]
            predicted_class = classifications[i]
            text = sent.text
            file.write(predicted_class.encode("utf8") + ": \n\t" + text + "\n")

