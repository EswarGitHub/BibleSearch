from flask import Flask, render_template, flash, redirect, url_for, request
from wtforms import Form, StringField, validators
from csv import reader
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from math import log10, sqrt
from collections import OrderedDict



app = Flask(__name__)



def getMatrix(docs, terms):
	'''returns the tf-idf matrix'''
	keys = list(docs.keys())
	N = len(docs)
	matrix = []
	for k in range(N):
		i = keys[k]
		l = []
		for j in terms:
			n = len(terms[j])
			if i in terms[j]:
				l.append(log10(1+terms[j][i]) * log10(N/n))
			else:
				l.append(0)
		c = sqrt(sum(map(lambda x: x*x, l)))
		for i in range(len(l)):
			l[i] = l[i]/c
		matrix.append(l)
	return matrix




def readData():
	'''to read data from the dataset and load it into Data Structures'''
	f = open('bible_data_set.csv', 'r')

	k = reader(f)

	l = 0

	docs = {}

	all_terms_list = []
	all_real_terms_list = []
	for i in k:
		print(l)
		l += 1
		if l == 1:
			continue
		doc_name = i[0]
		terms_list = list(map(lambda x: PorterStemmer().stem(x), word_tokenize(i[4] + i[1])))
		real_terms_list = word_tokenize(i[4])
		all_terms_list += terms_list
		all_real_terms_list += real_terms_list
		docs[doc_name] = terms_list
		if l==10000:
			break

	f.close()


	k = 0
	terms = {}
	all_terms_list = list(set(all_terms_list))
	all_real_terms_list = set(all_real_terms_list)
	for i in all_terms_list:
		doc_list = []
		for j in docs:
			if i in docs[j]:
				doc_list.append((j, docs[j].count(i)))
		print(k)
		k += 1
		terms[i] = dict(doc_list)


	docs = OrderedDict(docs)
	

	matrix = getMatrix(docs, terms)
	return docs, terms, matrix, all_real_terms_list


docs, terms, matrix, real_terms = readData()
N = len(docs)


def editDistance(s1, s2, m,  n):

	'''returns the minimum number operations to convert string-s1 to string-s2'''
	
	dp = [[0 for x in range(n+1)] for x in range(m+1)] 

	for i in range(m+1):
		for j in range(n+1):
			if i==0:
				dp[i][j] = j
			elif j==0:
				dp[i][j] = i
			elif s1[i-1]==s2[j-1]:
				dp[i][j] = dp[i-1][j-1]
			else:
				dp[i][j] = 1 + min(dp[i][j-1], dp[i-1][j-1], dp[i-1][j])
	
	return dp[m][n]



def getMinWord(terms, word):
	'''returns a term in terms which requires least number of operations to convert to given word'''
	minimum = 99999999999
	minWord = word
	for i in terms:
		k = editDistance(i, word, len(i), len(word))
		if k < minimum:
			minWord = i
			minimum = k
	return minWord


def getSuffix(terms, word):
	'''returns a term in terms whose suffix is the given word'''
	for i in terms:
		if i.find(word)==0:
			return True, i
	return False, word



def getResults(query):
	'''Returns the top relevent results for the query'''

	search = ''

	for i in query.split(' '):
		if PorterStemmer().stem(i) in terms:
			search += i + ' '
		else:
			result, word = getSuffix(real_terms, i)
			if result == True:
				search += word + ' '
			else:
				search += getMinWord(real_terms, i) + ' '

	search = search.strip()
	queryTermsList = list(map(PorterStemmer().stem , word_tokenize(search)))

	q = []
	for i in terms:
		n = len(terms[i])
		q.append(log10(1+queryTermsList.count(i)) * log10(N+1/n))
	c = sqrt(sum(map(lambda x: x*x, q)))
	for i in range(len(q)):
		q[i] = q[i]/c
	def multiply(a, b):
		'''returns the sum of the product of the corresponding elements in both the lists'''
		su = 0
		for i in range(len(a)):
			su += a[i] * b[i]
		return su

	ranks = {}

	k = 0
	keys = list(docs.keys())
	for j in matrix:
		ranks[keys[k]] = multiply(j, q)
		k += 1
	results = sorted(ranks, key = lambda x: ranks[x], reverse = True)[:10]
	return results, search	


def getDocDetails(docname):
	'''returns the document with the (docname)'''
	f = open('bible_data_set.csv', 'r')

	k = reader(f)

	l = 0
	for i in k:
		print(l)
		l += 1
		if l == 1:
			continue
		doc_name = i[0]
		if docname == doc_name:
			f.close()
			return i[0], i[1], i[2], i[3], i[4]



class SearchForm(Form):
	'''Form class to support WTForms in Flask'''
	search = StringField('Search for...', [validators.InputRequired()])


@app.route('/searchResults/<string:query>', methods = ['GET', 'POST'])
def searchResults(query):
	'''returns the page with the top 10 relevant search results'''
	results, real_search = getResults(query)
	form = SearchForm(request.form)
	if request.method == 'POST' and form.validate():
		search = form.search.data
		return redirect(url_for('searchResults', query = search))
	if query != real_search:
		flash('Showing results for ' + real_search, 'success')
	return render_template('searchResults.html', results = results, form = form)



@app.route('/displayDoc/<string:docname>')
def displayDoc(docname):
	'''returns the document with given docname'''
	citation, book, chapter, verse, text = getDocDetails(docname)
	return render_template('document.html', citation = citation, book = book, chapter = chapter, verse = verse, text = text)



@app.route('/', methods = ['GET', 'POST'])
def index():
	'''returns the home page with search bar'''
	form = SearchForm(request.form)
	if request.method == 'POST' and form.validate():
		search = form.search.data
		return redirect(url_for('searchResults', query = search, form = form))
	return render_template("home.html", form = form)


if __name__ == '__main__':
	app.secret_key = '528491@JOKER'
	app.run()