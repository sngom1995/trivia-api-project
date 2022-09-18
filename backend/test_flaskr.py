import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """

    def test_get_categories(self):
        response = self.client().get('/categories')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['data']), 6)

    def test_get_questions(self):
        response = self.client().get('/questions')
        self.assertEqual(response.status_code, 200)

        response = self.client().get('/questions?page=100')
        self.assertEqual(response.status_code, 400)

    def test_delete_question(self):
        response = self.client().delete('/question/10')
        self.assertEqual(response.status_code, 200)

        response = self.client().delete('/question/1000')
        self.assertEqual(response.status_code, 400)

    def test_add_question(self):
        response = self.client().post('/question', \
                                 json={'question': 'Test', 'answer': 'test', 'category': 1, 'difficulty': 2})
        self.assertEqual(response.status_code, 200)

        response = self.client().post('/question', json={'question': ''})
        self.assertEqual(response.status_code, 400)

    def test_search_question(self):
        response = self.client().post('/questions', json={'search_term': 'title'})
        data = json.loads(response.data)
        self.assertEqual(data['total'], 2)

        response = self.client().post('/questions', json={'search_term': 'test term'})
        data = json.loads(response.data)
        self.assertEqual(data['total'], 0)

    def test_get_questions_from_category(self):
        response = self.client().get('/category/1/questions')
        data = json.loads(response.data)
        self.assertGreater(data['total'], 0)

        response = self.client().get('/category/100/questions')
        data = json.loads(response.data)
        self.assertEqual(data['data'], [])

    def test_next_question(self):
        response = self.client().post('/quiz/question', json={'category': 0, 'previous_questions': []})
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['data'])

        res = self.client().get('/quiz/question')
        self.assertEqual(res.status_code, 405)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()