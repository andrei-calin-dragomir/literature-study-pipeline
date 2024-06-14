import unittest
import pandas as pd
import sys
sys.path.append('../')
import solve_cnf as scf

class SolveCNFTest(unittest.TestCase):
	def test_text_inside_parens_single_string(self):
		test_elements = pd.read_csv("test_data0.csv", delimiter=',')
		for i, x in test_elements.iterrows():
			self.assertEqual(
				x['element'], 
				scf.get_text_inside_parens(x['element_in_parentheses'])[0]
			)

	def test_text_inside_parens_multiple_strings(self):
		test_elements = pd.read_csv("test_data1.csv", delimiter=',')
		for i, x in test_elements.iterrows():
			self.assertEqual(
				x['element'], 
				scf.get_text_inside_parens(x['element_in_parentheses'])[0]
			)

	def test_text_inside_parens_multiple_parens(self):
		test_elements = pd.read_csv("test_data2.csv", delimiter=',')
		for i, x in test_elements.iterrows():
			self.assertEqual(
				x['element'].split(), 
				scf.get_text_inside_parens(x['element_in_parentheses'])
			)

	def test_solve_or(self):
		test_elements = pd.read_csv("test_data3.csv", delimiter=',')
		for i, x in test_elements.iterrows():
			self.assertTrue(
				scf.solve_or(x['test_string'], x['boolean_expression'])
			)

	def test_solve_and(self):
		test_elements = pd.read_csv("test_data4.csv", delimiter=',')
		for i, x in test_elements.iterrows():
			self.assertTrue(
				scf.solve_and(x['test_string'], x['boolean_expression'])
			)

	def test_solve_cnf(self):
		test_elements = pd.read_csv("test_data5.csv", delimiter=',')
		for i, x in test_elements.iterrows():
			self.assertTrue(
				scf.solve_cnf(x['title'], x['query'])
			)

if __name__ == "__main__":
	unittest.main()