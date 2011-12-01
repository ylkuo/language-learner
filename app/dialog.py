# -*- coding: utf-8 -*-

import os, re
from postagger_zh.postagger import POSTagger
from server import get_action_concept_category, get_location_concept_category, add_dialog

data_path = os.path.abspath(__file__).replace(\
		os.path.basename(__file__), '').replace(\
		os.path.abspath(__file__).split('/')[-2]+'/', 'data/')

class Dialog():
	def __init__(self):
		self.context_dialog = {}
		self.tagger = POSTagger()

	def add_dialog_template(self, dialog_template=data_path+'sentence_template.txt'):
		fp = open(dialog_template, 'r')
		for line in fp.read().split('==========\n'):
			if line.strip() == '':
				continue
			context = line.split('++++++++++\n')[0].strip()
			locations = context.split('|')[0].split('+')
			actions = context.split('|')[1].split('+')
			dialogs = line.split('++++++++++\n')[1].strip()
			for dialog in dialogs.split('----------\n'):
				dialog = dialog.strip()
				difficulty = self.calculate_dialog_difficulty(dialog)
				action_category, location_category =  self.find_associate_category(dialog)
				add_dialog(dialog, difficulty, action_category, location_category)
				

	def calculate_dialog_difficulty(self, dialog):
		sentences = dialog.split('\n')
		num_slots = 0
		num_segments = 0
		for sentence in sentences:
			chinese = sentence.split('\t')[0].strip()
			english = sentence.split('\t')[1].strip()
			num_slots += chinese.count('[')
			segments =  self.tagger.tag(\
					chinese.replace('[', '').replace(']', '').decode('utf-8'))
			num_segments += len(segments)
		return num_slots*(num_segments*len(sentences))

	def find_associate_category(self, dialog):
		sentences = dialog.split('\n')
		action_category = []
		location_category = []
		for sentence in sentences:
			chinese = sentence.split('\t')[0].strip()
			english = sentence.split('\t')[1].strip()
			matches = re.findall(r'\[\w+\]', \
					chinese.decode('utf-8'), flags=re.UNICODE)
			matches = list(set(matches))
			for match in matches:
				action_category.extend(get_action_concept_category(\
					match.replace('[', '').replace(']', '').encode('utf-8')))
				location_category.extend(get_location_concept_category(\
					match.replace('[', '').replace(']', '').encode('utf-8')))
		return (action_category, location_category)

if __name__ == '__main__':
	dialog = Dialog()
	dialog.add_dialog_template()
