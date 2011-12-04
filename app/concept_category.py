# -*- coding: utf-8 -*-

import divisi2
import os

data_path = os.path.abspath(__file__).replace(\
		os.path.basename(__file__), '').replace(\
		os.path.abspath(__file__).split('/')[-2]+'/', 'data/')

class ConceptCategory():
	def __init__(self, matrix_path=data_path+'feature_matrix_zh.smat'):
		# AnalogySpace
		A = divisi2.load(matrix_path)
		self.A = A.normalize_all()
		self.concept_axes, axis_weights, self.feature_axes = self.A.svd(k=100)
		self.sim = divisi2.reconstruct_similarity(\
				self.concept_axes, axis_weights, post_normalize=False)
		self.predict = divisi2.reconstruct(\
				self.concept_axes, axis_weights, self.feature_axes)
		# Fast spreading activation
		assoc = divisi2.load(data_path+'assoc_matrix_zh.smat')
		self.assoc = assoc.normalize_all()
		U, S, _ = self.assoc.svd(k=100)
		self.spread = divisi2.reconstruct_activation(U, S)

	def get_category_from_sim(self, concept_list, n=20):
		if len(concept_list) == 0:
			return []
		category_vector = divisi2.SparseVector.from_counts(concept_list)
		return self.sim.left_category(category_vector).top_items(n=n)

	def get_category_from_predict(self, concept_list, n=20):
		if len(concept_list) == 0:
			return []
		category_vector = divisi2.SparseVector.from_counts(concept_list)
		category_features = \
				divisi2.aligned_matrix_multiply(category_vector, self.A)
		return self.predict.right_category(category_features).top_items(n=n)
		

if __name__ == '__main__':
	concept_category = ConceptCategory()
	for concept in \
			concept_category.get_category_from_sim(\
			#[u'公車', u'火車', u'船', u'飛機']):
			[u'魚']):
		print concept[0].encode('utf-8')
		print concept[1]
	'''
	for concept in \
			concept_category.get_category_from_predict(\
			[u'公車', u'火車', u'船', u'飛機']):
		print concept[0].encode('utf-8')
		print concept[1]
	for concept in \
			concept_category.spread.row_named(u'魚').top_items(n=20):
		print concept[0].encode('utf-8')
		print concept[1]	
	'''
