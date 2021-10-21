from flask import Flask, render_template, request, redirect, url_for
from queries import db, process_query
import json
from datetime import date

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.app = app
db.init_app(app)

title = 'Корпус фанфиков'
url = 'http://tokubetsu.pythonanywhere.com'
doc_dir = 'docs/'


last_check = date.today()
results = {}
temp_data = [{}, []]
poses = [
        ('NOUN', 'нарицательное существительное'),
        ('PROPN', 'имя собственное'),
        ('VERB', 'глагол'),
        ('AUX', 'вспомогательный глагол (чаще всего "быть")'),
        ('PRON', 'личное местоимение'),
        ('DET', 'указательное и относительное местоимение'),
        ('ADJ', 'прилагательное'),
        ('ADV', 'наречие'),
        ('NUM', 'числительное'),
        ('ADP', 'предлог'),
        ('CCONJ', 'сочинительный союз'),
        ('SCONJ', 'подчинительный союз'),
        ('PART', 'частица'),
        ('INTJ', 'междометие'),
        ('SYM', 'символ'),
        ('X', 'не определена часть речи')]


def recount_results(point=100):
    global results, last_check
    if date.today() != last_check:
        keys = sorted(results.keys(), key=lambda x: results[x][0], reverse=True)[0:point]
        results = {key: results[key] for key in keys}


def get_marked(sentence, mark, n=1):
    mark_sent = []
    marg = ['-', '—', '(', '«']
    key = 0
    for item in sentence:
        if item['PoS'] != 'PUNCT':
            mk = bool(sum([key - x in mark for x in range(n)]))
            mark_sent.append({'marked': mk, **item})
            key += 1
        else:
            if (item['text'] not in marg) and mark_sent:
                mark_sent[-1]['text'] += item['text']
            else:
                mark_sent.append({'marked': False, **item})
    return mark_sent


@app.route('/')
def index(site_title=title, baseurl=url):
    page = render_template('index.html', page_title=None,
                           site_title=site_title, baseurl=baseurl)
    return page


@app.route('/search')
def search(site_title=title, baseurl=url):
    global poses
    page = render_template('search.html', page_title='Поиск', site_title=site_title, baseurl=baseurl, poses=poses)
    return page


@app.route('/results/<query>')
def show_results(query, site_title=title, baseurl=url, pag=50):
    global temp_data

    if query in temp_data[0]:
        res = temp_data[1][temp_data[0][query]]
        page = render_template('results.html', page_title='Результаты запроса', site_title=site_title,
                               baseurl=baseurl, res=res[1], num=len(res) - 1, pages=(0, 1, 2), query=query)
    else:
        global results

        if query in results:
            results[query][0] += 1
            positions = results[query][1]
        else:
            positions = process_query(query)
            results[query] = [1, positions]

        if not positions:
            page = render_template('nothing.html', page_title='Ничего не найдено', site_title=site_title,
                                   baseurl=baseurl)
        else:
            n = len(query.split(' '))
            res = [1, []]
            prev_doc = -1
            prev_sent = -1
            marked = []
            for doc_id in sorted(positions):
                doc, sen, pos = doc_id
                if len(res[-1]) == pag:
                    res.append([])
                if doc != prev_doc:
                    with open(doc_dir + str(doc) + '.jsonl', 'r', encoding='utf-8') as f:
                        text = f.read().splitlines()
                    meta = json.loads(text[0])
                    prev_doc = doc
                if sen != prev_sent:
                    if marked:
                        res[-1].append([meta, *get_marked(sent, marked, n)])
                    sent = text[sen + 1]
                    sent = json.loads(sent)
                    prev_sent = sen
                    marked = [pos, ]
                else:
                    marked.append(pos)
            temp_data[0][query] = len(temp_data[1])
            temp_data[1].append(res)
            page = render_template('results.html', page_title='Результаты запроса', site_title=site_title,
                                   baseurl=baseurl, res=res[1], num=len(res) - 1,
                                   pages=(0, 1, 2), query=query)

        if len(results) > 100:
            recount_results()

    return page


@app.route('/pagination/<query>')
def show_results_page(query, site_title=title, baseurl=url):
    global temp_data
    query, page_n = query.split('+')
    res = temp_data[1][temp_data[0][query]]
    page_n = int(page_n)
    prev = page_n - 1
    post = page_n + 1
    page = render_template('results.html', page_title='Результаты запроса', site_title=site_title,
                           baseurl=baseurl, res=res[page_n], num=len(res) - 1,
                           pages=(prev, page_n, post), query=query)
    return page


@app.route('/results/', methods=['get'])
def empty_res(site_title=title, baseurl=url):
    page = render_template('nothing.html', page_title='Ничего не найдено', site_title=site_title,
                           baseurl=baseurl)
    return page


@app.route('/find', methods=['get'])
def find_process():
    if not request.args:
        return redirect(url_for('search'))

    global temp_data
    if len(temp_data) > 100:
        temp_data = [{}, []]

    query = request.args.get('query')

    return redirect(url_for('show_results', query=query))


@app.route('/info')
def info(site_title=title, baseurl=url):
    global poses
    page = render_template('info.html', page_title='Инструкция', site_title=site_title,
                           baseurl=baseurl, poses=poses)
    return page


if __name__ == '__main__':
    app.run()
