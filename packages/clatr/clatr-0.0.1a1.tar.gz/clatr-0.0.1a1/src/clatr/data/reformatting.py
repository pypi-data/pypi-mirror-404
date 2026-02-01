import re

replacements = {
        'len': 'Length of ',
        'num': 'Number of ',
        'chars': 'Characters in ',
        'sents': 'Sentences in ',
        'paras': 'Paragraphs in ',
        'tokens': 'Tokens in ',
        'basic': 'Basic Text',
        'preprocessed': 'Preprocessed Text',
        'tokenized': 'Tokenized Text'
}

def reformatter(att):
    """
    Converts abbreviations to readable labels.
    """
    for key, value in replacements.items():
        att = re.sub(r'\_', ' ', att)
        att = re.sub(re.compile(key), value, att)
    return att
