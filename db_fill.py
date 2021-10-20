from models import *
import json
import os
import sqlite3


def read_json(filename):
	with open(filename, 'r', encoding='utf-8') as f:
		data = [json.loads(s) for s in f.read().splitlines()[1:]]
	return data


def get_sent_info(sent, words, lemmas, pos, parses, positions, doc_id, sent_id):
	n = 0
	for el in sent:
		if el['PoS'] != 'PUNCT':
			if el['word'] not in words:
				words[el['word']] = len(words)
			if el['lemma'] not in lemmas:
				lemmas[el['lemma']] = len(lemmas)
			if el['PoS'] not in pos:
				pos[el['PoS']] = len(pos)
			parse = (words[el['word']], lemmas[el['lemma']], pos[el['PoS']])
			if parse not in parses:
				parses[parse] = len(parses)
			positions.append((parses[parse], doc_id, sent_id, n))
			n += 1
	return words, lemmas, pos, parses, positions


def get_max_id(con, cur, words, lemmas, pos, parses):
	tb = [words, lemmas, pos, parses]
	table = ['words', 'lemmas', 'poses', 'parses']
	res = []
	for i, el in enumerate(table):
		if tb[i]:
			res.append(max(tb[i].values()) + 1)
		else:
			query = 'SELECT max(id) FROM ' + el
			cur.execute(query)
			res.append(cur.fetchone()[0] + 1)
	return res


def get_add_info(sent, words, lemmas, pos, parses, positions, doc_id, sent_id, con, cur):
	maxes = get_max_id(con, cur, words, lemmas, pos, parses)
	n = 0
	for el in sent:
		if el['PoS'] != 'PUNCT':

			query_w = f'SELECT id FROM words WHERE word = "{el["word"]}"'
			cur.execute(query_w)
			w = cur.fetchone()
			if not w:
				if el["word"] not in words:
					w = maxes[0]
					words[el['word']] = w
					maxes[0] += 1
				else:
					w = words[el["word"]]
			else:
				w = w[0]

			query_l = f'SELECT id FROM lemmas WHERE lemma = "{el["lemma"]}"'
			cur.execute(query_l)
			l = cur.fetchone()
			if not l:
				if el['lemma'] not in lemmas:
					l = maxes[1]
					lemmas[el['lemma']] = l
					maxes[1] += 1
				else:
					l = lemmas[el['lemma']]
			else:
				l = l[0]

			query_p = f'SELECT id FROM poses WHERE pos = "{el["PoS"]}"'
			cur.execute(query_p)
			p = cur.fetchone()
			if not p:
				if el['PoS'] not in pos:
					p = maxes[2]
					pos[el['PoS']] = p
					maxes[2] += 1
				else:
					p = pos[el['PoS']]
			else:
				p = p[0]

			query_par = f'SELECT id FROM parses WHERE id_word = {w} AND id_lemma = {l} AND id_pos = {p}'
			cur.execute(query_par)
			par = cur.fetchone()
			parse = (w, l, p)
			if not par:
				if parse not in parses:
					par = maxes[3]
					parses[parse] = par
					maxes[3] += 1
				else:
					par = parses[parse]
			else:
				par = par[0]

			positions.append((par, doc_id, sent_id, n))
			n += 1

	return words, lemmas, pos, parses, positions


def get_all_info(path, add=False, con=None, cur=None):
	res = ({}, {}, {}, {}, [])
	for _, __, files in os.walk(path):
		for filename in files:
			id_doc = int(filename.split('.')[0])
			data = read_json(path + '/' + filename)
			for i, el in enumerate(data):
				if add:
					res = get_add_info(el, *res, id_doc, i, con, cur)
				else:
					res = get_sent_info(el, *res, id_doc, i)
	return res


def create_connection(db_name):
	con = sqlite3.connect(db_name)
	cur = con.cursor()
	return con, cur


def add_to_table(con, cur, words, lemmas, pos, parses, positions):
	try:
		cur.executemany("INSERT INTO words VALUES (?, ?)", words)
		cur.executemany("INSERT INTO lemmas VALUES (?, ?)", lemmas)
		cur.executemany("INSERT INTO poses VALUES (?, ?)", pos)
		cur.executemany("INSERT INTO parses VALUES (?, ?, ?, ?)", parses)
		cur.executemany("INSERT INTO positions VALUES (?, ?, ?, ?)", positions)
	except sqlite3.IntegrityError:
		print('Duplicate documents')
		return
	con.commit()


def save_info(data, con, cur):
	res = []
	for j in range(len(data) - 2):
		res.append([(i[1], i[0]) for i in sorted(data[j].items(), key=lambda x: x[1])])
	res.append([(i[1], *i[0]) for i in sorted(data[3].items(), key=lambda x: x[1])])
	res.append(data[4])

	add_to_table(con, cur, *res)


def main(add=False, path='docs'):
	con, cur = create_connection('base.db')
	data = get_all_info(path, add, con, cur)
	save_info(data, con, cur)

	# print(get_max_id(con, cur, {}, {}, {}, {}))


if __name__ == '__main__':
	# main(add=True, path='new_doc')
	main()


