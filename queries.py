from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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


def find_parses(type_query, query):
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
        return [parse.id for parse in Parses.query
                .join(Lemmas, Lemmas.id == Parses.id_lemma).join(Poses, Poses.id == Parses.id_pos)
                .filter(Lemmas.lemma == 'сидеть').filter(Poses.pos == 'VERB').all()]


def select_unigram(type_query, query):
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


def select_bigram(type_query_1, query_1, type_query_2, query_2):
    result_1 = select_unigram(type_query_1, query_1)
    result_2 = select_unigram(type_query_2, query_2)
    return [x for x in result_1 if (x[0], x[1], x[2] + 1) in result_2]


def select_trigram(type_query_1, query_1, type_query_2, query_2, type_query_3, query_3):
    result_1 = select_unigram(type_query_1, query_1)
    result_2 = select_unigram(type_query_2, query_2)
    result_3 = select_unigram(type_query_3, query_3)
    return [x for x in result_1 if (x[0], x[1], x[2] + 1) in result_2 and (x[0], x[1], x[2] + 2) in result_3]


print(select_trigram('pos', 'PROPN', 'pos', 'VERB', 'pos', 'NOUN')[:20])
