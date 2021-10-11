from flask_sqlalchemy import SQLAlchemy
import re
import spacy

nlp_spacy = spacy.load("ru_core_news_sm")
db = SQLAlchemy()


class Lemmas(db.Model):
    __tablename__ = "lemmas"

    id = db.Column('id', db.Integer, primary_key=True)
    lemma = db.Column('lemma', db.Text)


class Parses(db.Model):
    __tablename__ = "parses"

    id = db.Column('id', db.Integer, primary_key=True)
    id_word = db.Column('id_word', db.Integer)
    id_lemma = db.Column('id_lemma', db.Integer)
    id_pos = db.Column('id_pos', db.Integer)


class Poses(db.Model):
    __tablename__ = "poses"

    id = db.Column('id', db.Integer, primary_key=True)
    pos = db.Column('pos', db.Text)


class Positions(db.Model):
    __tablename__ = "positions"

    id_parse = db.Column('id_parse', db.Integer)
    id_doc = db.Column('id_doc', db.Integer, primary_key=True)
    id_sent = db.Column('id_sent', db.Integer, primary_key=True)
    id_position = db.Column('position', db.Integer, primary_key=True)


class Words(db.Model):
    __tablename__ = "words"

    id = db.Column('id', db.Integer, primary_key=True)
    word = db.Column('word', db.Text)


def find_parses(type_query: str, query: str) -> list:
    '''
    Функция, которая по запросу находит id разборов
    :param type_query: тип запроса: {pos, word, lemma, lemma+pos}
    :param query: строка запроса
    :return: список id разборами
    '''
    if type_query == 'pos':
        return [parse.id for parse in
                Parses.query.join(Poses, Poses.id == Parses.id_pos).filter(Poses.pos == query).all()]
    elif type_query == 'word':
        return [parse.id for parse in
                Parses.query.join(Words, Words.id == Parses.id_word).filter(Words.word == query).all()]
    elif type_query == 'lemma':
        return [parse.id for parse in
                Parses.query.join(Lemmas, Lemmas.id == Parses.id_lemma).filter(Lemmas.lemma == query).all()]
    elif type_query == 'lemma+pos':
        lemma, pos = query.split('+')
        return [parse.id for parse in Parses.query
                .join(Lemmas, Lemmas.id == Parses.id_lemma).join(Poses, Poses.id == Parses.id_pos)
                .filter(Lemmas.lemma == lemma).filter(Poses.pos == pos).all()]


def select_unigram(type_query: str, query: str) -> list:
    '''
    Функция, которая выдает вхождения запроса (униграммы)
    :param type_query: тип запроса: {pos, word, lemma, lemma+pos}
    :param query: строка запроса
    :return: список кортежей с местоположением каждого вхождения запроса: (id_doc, id_sent, position)
    '''
    parses = find_parses(type_query, query)
    result = []
    i = 0
    while i < len(parses):
        if i+999 < len(parses):
            result.extend([(position.id_doc, position.id_sent, position.id_position) for position in Positions.query
                          .join(Parses, Positions.id_parse == Parses.id).filter(Parses.id.in_(parses[i:i+999])).all()])
        else:
            result.extend([(position.id_doc, position.id_sent, position.id_position) for position in Positions.query
                          .join(Parses, Positions.id_parse == Parses.id).filter(
                Parses.id.in_(parses[i:])).all()])
        i += 999
    return result


def select(params: list) -> list:
    '''
    Функция, которая выдает вхождения запроса (униграммы/биграммы/триграммы)
    :param params: список кортежей с типом запроса и самой строкой запроса
    :return: список кортежей с местоположением каждого вхождения запроса: (id_doc, id_sent, position)
    '''
    result_1 = select_unigram(params[0][0], params[0][1])
    if len(params) == 1:
        return result_1
    elif len(params) == 2:
        result_2 = select_unigram(params[1][0], params[1][1])
        return [x for x in result_1 if (x[0], x[1], x[2] + 1) in result_2]
    else:
        result_2 = select_unigram(params[1][0], params[1][1])
        result_3 = select_unigram(params[2][0], params[2][1])
        return [x for x in result_1 if (x[0], x[1], x[2] + 1) in result_2 and (x[0], x[1], x[2] + 2) in result_3]


def process_item(item: str) -> tuple or False:
    '''
    Функция, которая обрабатывает запрос и выдает либо его тип и его самого в нужном формате,
    либо то, что такой запрос невалидный
    :param item: строка с запросом
    :return: кортеж с типом запроса и самим запросом или False
    '''
    poses = ['ADJ', 'ADP', 'ADV', 'AUX', 'INTJ', 'CCONJ', 'X', 'NOUN',
             'DET', 'PROPN', 'NUM', 'VERB', 'PART', 'PRON', 'SCONJ', 'SYM']
    if re.search(r'^"\w+"$', item):
        type_query = 'word'
        item = item.replace('"', '')
    elif item in poses:
        type_query = 'pos'
    elif re.search(r'^\w+\+[A-Z]+$', item):
        if re.search(r'^\w+\+([A-Z]+)$', item).group(1) in poses:
            type_query = 'lemma+pos'
        else:
            return False
    elif re.search(r'^\w+$', item):
        type_query = 'lemma'
        item = nlp_spacy(item)[0].lemma_
    else:
        return False
    return type_query, item


def process_query(search: str) -> list or False:
    '''
    Функция, которая по строке запроса выдает все его вхождения
    :param search: строка запроса
    :return: список кортежей с местоположением каждого вхождения запроса: (id_doc, id_sent, position)
    '''
    if not search:
        return False
    search = search.split()
    if len(search) > 3:
        return False
    params = []
    for item in search:
        type_item, item = process_item(item)
        if type_item:
            params.append((type_item, item))
        else:
            return False
    return select(params)
