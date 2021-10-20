from flask_sqlalchemy import SQLAlchemy


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
