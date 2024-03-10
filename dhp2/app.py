from flask import Flask, render_template, request, redirect, url_for, session
from newspaper import Article
import psycopg2
import json
import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk import pos_tag
from collections import Counter
nltk.download('universal_tagset')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')


app = Flask(__name__)
app.secret_key = '2030'
# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="anamika1905",
    user="anamika1905_user",
    password="QemaFXCOGzKvJUVelWF9OSvpZEZXPYMR",
    host="dpg-cnmmi72cn0vc738eu6sg-a",
    port="5432"
)
cur = conn.cursor()
# Create table if not exists
#postgres://anamika1905_user:QemaFXCOGzKvJUVelWF9OSvpZEZXPYMR@dpg-cnmmi72cn0vc738eu6sg-a.oregon-postgres.render.com/anamika1905
cur.execute('''
    CREATE TABLE IF NOT EXISTS news (
        id SERIAL PRIMARY KEY,
        url TEXT,
        news_text TEXT,
        analysis_summary JSON
    )
''')
conn.commit()

def extract_news_text(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.text

def clean_text(text):
    # Remove HTML tags
    cleaned_text = re.sub(r'<.*?>', '', text)
    # Remove special characters except for full stops
    cleaned_text = re.sub(r'[^a-zA-Z\s\.]', '', cleaned_text)
    # Add space after full stops
    cleaned_text = re.sub(r'\.(?! )', '. ', cleaned_text)
    # Convert to lowercase
    cleaned_text = cleaned_text.lower()
    return cleaned_text

def analyze_text(text):
    sentences = sent_tokenize(text)
    words = word_tokenize(text)

    # Part-of-speech tagging with Universal Tagset
    pos_tags = pos_tag(words, tagset='universal')
    
    # Count occurrence of each word
    word_counts = Counter(words)

    # Extract keywords (nouns and proper nouns)
    keywords = [word.lower() for word, pos in pos_tags if pos.startswith('N')]

    analysis_summary = {
        'num_sentences': len(sentences),
        'num_words': len(words),
        'word_counts': dict(word_counts),
        'pos_tags': dict(Counter(tag for word, tag in pos_tags)),
        'keywords': dict(Counter(keywords))
    }

    return analysis_summary

# Define route for the index page
@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            error = "Please enter a URL."
        else:
            try:
                news_text = extract_news_text(url)
                cleaned_text = clean_text(news_text)
                analysis_summary = analyze_text(cleaned_text)

                # Store data in PostgreSQL
                cur.execute("INSERT INTO news (url, news_text, analysis_summary) VALUES (%s, %s, %s)",
                            (url, news_text, json.dumps(analysis_summary)))
                conn.commit()

                return render_template('result.html', cleaned_news_text=cleaned_text, analysis_summary=analysis_summary)
            except Exception as e:
                error = f"An error occurred: {str(e)}"
    return render_template('index.html', error=error)

# Define route for the admin history page
@app.route('/admin/history')
def admin_history():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    cur.execute("SELECT * FROM news")
    rows = cur.fetchall()
    return render_template('history.html', rows=rows)

# Define route for the admin login page
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == 'Anamika' and request.form['password'] == '2030':
            session['admin'] = True
            return redirect(url_for('admin_history'))
        else:
            return render_template('login.html', error=True)
    return render_template('login.html', error=False)

# Define route for the admin logout page
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
