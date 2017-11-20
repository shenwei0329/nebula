# coding=utf-8

def safe_encoding(word, encoding='utf-8'):
    if not isinstance(word, unicode):
        return word
    return word.encode(encoding)
