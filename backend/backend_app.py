import json
import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
CORS(app)

SWAGGER_URL = "/api/docs"
API_URL = "/static/masterblog.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': 'Masterblog API'}
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_FILE = os.path.join(BASE_DIR, 'posts.json')


def load_posts():
    try:
        with open(POSTS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_posts(posts):
    with open(POSTS_FILE, 'w') as f:
        json.dump(posts, f, indent=4)


@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    posts = load_posts()
    title_query = request.args.get('title', '').lower()
    content_query = request.args.get('content', '').lower()
    author_query = request.args.get('author', '').lower()
    date_query = request.args.get('date', '').lower()

    results = [post for post in posts if
               (title_query and title_query in post['title'].lower()) or
               (content_query and content_query in post['content'].lower()) or
               (author_query and author_query in post['author'].lower()) or
               (date_query and date_query in post['date'].lower())]

    return jsonify(results), 200


@app.route('/api/posts', methods=['GET'])
def get_posts():
    posts = load_posts()
    sort = request.args.get('sort')
    direction = request.args.get('direction')

    valid_sort_fields = ['title', 'content', 'author', 'date']
    valid_directions = ['asc', 'desc']

    if sort and sort not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort field '{sort}'. Use 'title', 'content', 'author' or 'date'."}), 400

    if direction and direction not in valid_directions:
        return jsonify({"error": f"Invalid direction '{direction}'. Use 'asc' or 'desc'."}), 400

    if sort:
        reverse = direction == 'desc'
        if sort == 'date':
            posts = sorted(posts, key=lambda post: datetime.strptime(post['date'], '%Y-%m-%d'), reverse=reverse)
        else:
            posts = sorted(posts, key=lambda post: post[sort].lower(), reverse=reverse)

    return jsonify(posts), 200


@app.route('/api/posts', methods=['POST'])
def add_post():
    posts = load_posts()
    data = request.get_json()

    missing_fields = []
    if not data.get('title'):
        missing_fields.append('title')
    if not data.get('content'):
        missing_fields.append('content')

    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    new_id = max(post['id'] for post in posts) + 1 if posts else 1
    new_post = {
        'id': new_id,
        'title': data.get('title'),
        'content': data.get('content'),
        'author': data.get('author', 'Anonymous'),
        'date': data.get('date', datetime.today().strftime('%Y-%m-%d'))
    }
    posts.append(new_post)
    save_posts(posts)
    return jsonify(new_post), 201


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    posts = load_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    if post is None:
        return jsonify({"error": f"Post with id {post_id} was not found."}), 404
    posts.remove(post)
    save_posts(posts)
    return jsonify({"message": f"Post with id {post_id} has been deleted successfully."}), 200


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    posts = load_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    if post is None:
        return jsonify({"error": f"Post with id {post_id} was not found."}), 404

    data = request.get_json()
    post['title'] = data.get('title', post['title'])
    post['content'] = data.get('content', post['content'])
    post['author'] = data.get('author', post['author'])
    post['date'] = data.get('date', post['date'])
    save_posts(posts)
    return jsonify(post), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
