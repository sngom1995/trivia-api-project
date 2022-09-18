from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from sqlalchemy import func, and_
from sqlalchemy.sql.operators import ColumnOperators

from models import setup_db, Category, Question

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    cors = CORS(app, resources={r"*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Headers', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        categories = [cate.format() for cate in categories]
        return jsonify(categories)

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.
    
    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route('/questions')
    def get_questions():
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * 10
        end = start + 10
        questions = Question.query.order_by(Question.category).all()
        format_questions = [question.format() for question in questions]
        current_categories = questions[0].category
        categories = Category.query.all()
        categories = [Category.query.get(cate.category).type for cate in questions]
        return jsonify({"questions": format_questions[start:end], "total_questions": len(format_questions),
                        "categories": categories, "current_category": current_categories})

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route('/questions/<int:question_id>', methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()
            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_books = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "books": current_books,
                    "total_books": len(Question.query.all()),
                }
            )
        except():
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.
    
    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route("/questions", methods=["POST"])
    def create_question():
        data = request.get_json()
        question = data.get('question', None)
        answer = data.get('answer', None)
        difficulty = data.get('difficulty', None)
        category = data.get('category', None)
        try:
            book = Question(question=question, answer=answer, difficulty=difficulty, category=category)
            book.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "created": book.id,
                    "questions": current_questions,
                    "total_questions": len(Question.query.all()),
                }
            )

        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.
    
    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        data = request.get_json()
        #search_term = data.get('searchTerm', None)
        search_term = data.get('search_term', None)
        try:
            print(search_term)
            selection = Question.query.order_by(Question.id).filter(
                Question.question.ilike("%{}%".format(search_term))
            )
            current_books = paginate_questions(request, selection)
            print(data)
            print(search_term)
            return jsonify(
                {
                    "success": True,
                    "questions": current_books,
                    "total_questions": len(selection.all()),
                }
            )
        except():
            abort(422)

    """
    @TODO:
    Create a GET endpoint to get questions based on category.
    
    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/category/<int:category_id>/questions')
    def get_question_from_category(category_id):
        questions = Question.query.join(Category, Question.category == Category.id).filter(
            Category.id == category_id).all()
        result = [question.format() for question in questions]

        return jsonify({
            'success': True,
            'data': result,
            'total': len(questions),
            'category': category_id
        })

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.
    
    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route('/quiz/question', methods=['POST'])
    def next_question():
        data = request.get_json()
        if data['category'] == 0:
            question = Question.query.join(Category, Question.category == Category.id) \
                .filter(ColumnOperators.notin_(Question.id, data['previous_questions'])) \
                .order_by(func.random()) \
                .first()
        else:
            question = Question.query.join(Category, Question.category == Category.id) \
                .filter(
                and_(Category.id == data['category'], ColumnOperators.notin_(Question.id, data['previous_questions']))) \
                .order_by(func.random()) \
                .first()

        if question is None:
            return abort(400)

        return jsonify({
            'success': True,
            'data': question.format()
        })

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(400)
    def page_not_found(e):
        return jsonify({
            'success': False,
            'data': 'Bad Request'
        }), 400

    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({
            'success': False,
            'data': 'Page not found'
        }), 404

    @app.errorhandler(405)
    def page_not_found(e):
        return jsonify({
            'success': False,
            'data': 'Method not allowed'
        }), 405

    @app.errorhandler(422)
    def page_not_found(e):
        return jsonify({
            'success': False,
            'data': 'Request cannot be processed'
        }), 422
    @app.route('/')
    def index():
        return jsonify({"message": "hello world"})

    return app
