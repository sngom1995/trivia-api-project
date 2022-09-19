import json
import random

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
        # categories = [cate.format() for cate in categories]
        cat = dict()
        for c in categories:
            cat[c.id] = c.type
        return jsonify({"categories": cat, "success": True})

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
        if len(format_questions[start:end]) == 0:
            abort(404)
        cat = dict()
        for c in categories:
            cat[c.id] = c.type
        return jsonify({"questions": format_questions[start:end], "total_questions": len(format_questions),
                        "categories": cat, "current_category": current_categories, "success": True})

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
        # search_term = data.get('searchTerm', None)
        search_term = data.get('searchTerm', None)
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

    @app.route('/categories/<int:category_id>/questions')
    def get_question_from_category(category_id):
        questions = Question.query.join(Category, Question.category == Category.id).filter(
            Category.id == category_id).all()
        result = [question.format() for question in questions]
        q = Question.query.all()
        cat = Category.query.filter(Category.id == category_id).one_or_none()

        return jsonify({
            'success': True,
            'questions': result,
            'totalQuestions': len(q),
            'current_category': cat.type
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

    @app.route('/quizzes2', methods=['POST'])
    def next_question():
        data = request.get_json()
        if data['quiz_category'] == 0:
            question = Question.query.join(Category, Question.category == Category.id) \
                .filter(ColumnOperators.notin_(Question.id, data['previous_questions'])) \
                .order_by(func.random()) \
                .first()
        else:
            # data['quiz_category'] = json.dumps(data['quiz_category'])
            # data['previous_questions'] = json.dumps(data['previous_questions'])
            print(data['quiz_category'].get("id"))
            print(data['previous_questions'])
            question = Question.query.join(Category, Question.category == Category.id) \
                .filter(
                and_(Category.id == data['quiz_category'],
                     ColumnOperators.notin_(Question.id, data['previous_questions']))) \
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

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        """Play quiz by returning a new random question

          Tested by:
            Success:
              - test_play_quiz_with_category
              - test_play_quiz_without_category
            Error:
              - test_error_400_play_quiz
              - test_error_405_play_quiz
        """
        body = request.get_json()

        if not body:
            # If no JSON Body was given, raise error.
            abort(400, {'message': 'Please provide a JSON body with previous question Ids and optional category.'})

        # Get paramters from JSON Body.
        previous_questions = body.get('previous_questions', None)
        current_category = body.get('quiz_category', None)

        if not previous_questions:
            print(current_category)
            if current_category:
                # if no list with previous questions is given, but a category , just gut any question from this category.
                if current_category['id'] == 0:
                    questions_raw = Question.query.all()
                else:
                    questions_raw = (Question.query
                                     .filter(Question.category == str(current_category['id']))
                                     .all())
            else:
                # if no list with previous questions is given and also no category , just gut any question.
                if current_category['id'] == 0:
                    questions_raw = Question.query.all()

        else:
            if current_category:
                # if a list with previous questions is given and also a category, query for questions which are not contained in previous question and are in given category
                if current_category['id'] == 0:
                    questions_raw = (Question.query
                                     .filter(Question.id.notin_(previous_questions))
                                     .all())
                else:
                    questions_raw = (Question.query
                                     .filter(Question.category == str(current_category['id']))
                                     .filter(Question.id.notin_(previous_questions))
                                     .all())
            else:
                # # if a list with previous questions is given but no category, query for questions which are not contained in previous question.
                if current_category['id'] == 0:
                    questions_raw = (Question.query
                                     .filter(Question.id.notin_(previous_questions))
                                     .all())

        # Format questions & get a random question
        questions_formatted = [question.format() for question in questions_raw]
        print(questions_formatted)
        if len(questions_formatted) > 0:
            random_question = questions_formatted[random.randint(0, len(questions_formatted) - 1)]
        else:
            random_question = questions_formatted

        return jsonify({
            'success': True,
            'question': random_question
        })

    return app
