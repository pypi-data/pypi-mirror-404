"""
This algorithm was designed, programmed, and developed by Sapiens Technology®️ to enable the construction, training, tuning, and inference of language models using the main architectural frameworks of Sapiens Technology®️.
The code includes a main class with the base architecture and several other internal sub-architectures that can be configured through the model's parameters.

Any changes to this code, reverse engineering, disclosure, or public commentary involving the technical aspects of the technology contained herein are strictly prohibited, and the authors will be duly prosecuted by our legal team.

WE DO NOT authorize the commercial use of this code without prior permission from Sapiens Technology®️.
"""
# --------------------------> A SAPIENS TECHNOLOGY®️ PRODUCTION) <--------------------------
class SapiensModel:
	def __init__(self, show_errors=True, display_error_point=False):
		try:
			self.__show_errors = bool(show_errors) if type(show_errors) in (bool, int, float) else True
			self.__display_error_point = bool(display_error_point) if type(display_error_point) in (bool, int, float) else False
			try:
				from warnings import filterwarnings
				from logging import getLogger, ERROR, disable, CRITICAL
				from os import environ
				from dotenv import load_dotenv
				filterwarnings('ignore')
				filterwarnings('ignore', category=UserWarning, module='torch.distributed')
				getLogger('torch.distributed.elastic.multiprocessing.redirects').setLevel(ERROR)
				environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
				load_dotenv()
				disable(CRITICAL)
			except: pass
			from traceback import print_exc
			self.__print_exc = print_exc
			from semantic_comparison_network import SemanticComparisonNetwork
			from scnetwork import SCNet
			from scn import SCN
			from hur import HurModel
			from hur_multimodal import HurMultiModal
			from sapiens_cpu import CPUModel
			from mgt import MGT
			self.__semantic_comparison_network = SemanticComparisonNetwork
			self.__scnetwork = SCNet
			self.__scn = SCN
			self.__hur = HurModel
			self.__hur_multimodal = HurMultiModal
			self.__sapiens_cpu = CPUModel
			self.__mgt = MGT
			self.__sapiens_model = None
			self.__sub_architecture = 'cpu'
			self.__model_path = ''
			self.__copy_folder_to_temp = ''
			self.string = ''
			self.precision = 1.0
			self.tokenizer = 'gpt-4'
			self.method = 'semantic'
			self.interaction = True
			self.activation_function = 'linear'
			self.bias = 0.0
			self.learning_rate = 1.0
			self.stochastic_factor = False
			self.fx = False
			self.context_window = float('inf')
			self.end_tag = '<|end|>'
			self.validate = 0.0
			self.hurnet_initializer = True
			self.hurnet_layer = False
			self.hurnet_fit = False
			self.stream_dataset = False
			self.quantization = None
			self.experts = 1
			self.language = None
			self.information_gain = None
			self.minimum_score = 0.5
			self.hot = False
			self.max_tokens = None
			self.min_fit_probability = 0.7
			self.min_probability = 0.01
			self.generalization = True
			self.temperature = 0.1
			self.top_k = 0
			self.top_p = 1.0
			self.system = ''
			self.messages = []
			self.sapiens_model_path = ''
			self.embedding_dim = None
			self.block_size = None
			self.batch_size = None
			self.number_heads = None
			self.number_layers = None
			self.dropout = None
			self.eval_interval = None
			self.epochs = None
			self.use_bit_net_quantization = None
			self.device = None
			self.user_id = 0
			self.parallel_prediction = False
			self.minimum_probability_for_candidates = 0.9
			self.show_errors = True
			self.display_error_point = False
			self.progress = True
			self.scn_architecture = 'level_1'
			self.system_tag = 'System:'
			self.user_tag = 'User:'
			self.assistant_tag = 'Assistant:'
			self.tokens_number = 0
			self.parameters_number = 0
			self.perplexity = 100.0
			self.weight_decay = None
			self.hurnet_embedding_length = 25
			self.hurnet_division_method = 0
			self.include_vocabulary_in_model = True
			self.use_scheduler = False
			self.scheduled = None
			self.hurnet_dtype = None
			self.show_error = False
			self.show_error_details = False
			self.delay = 0.01
			self.real_time_generator = False
			self.online_consultation = True
			self.summary_automation = True
			self.translation_automation = True
			self.mathematical_automation = True
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.__init__: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
	def __resolve_directory_path(self, directory_path=''):
		try:
			from pathlib import Path
			path_object = Path(str(directory_path))
			if path_object.is_dir(): return str(path_object)
			if path_object.is_file(): return str(path_object.parent)
			current_path = path_object
			while not current_path.exists():
				if current_path.parent == current_path: break
				current_path = current_path.parent
			return str(current_path)
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.__resolve_directory_path: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return directory_path
	def __get_input_output(self, json_dictionary={}):
		try:
			return_dictionary = {'input': '', 'output': '', 'file_path': ''}
			if not json_dictionary or type(json_dictionary) != dict: return return_dictionary
			input_output, _input, _output, _file_path = json_dictionary, '', '', ''
			if input_output and type(input_output) == dict:
				json_keys = list(input_output.keys())
				if 'input' in json_keys: _input = str(input_output.get('input', '')).strip()
				elif 'Input' in json_keys: _input = str(input_output.get('Input', '')).strip()
				elif 'INPUT' in json_keys: _input = str(input_output.get('INPUT', '')).strip()
				elif 'question' in json_keys: _input = str(input_output.get('question', '')).strip()
				elif 'Question' in json_keys: _input = str(input_output.get('Question', '')).strip()
				elif 'QUESTION' in json_keys: _input = str(input_output.get('QUESTION', '')).strip()
				elif 'prompt' in json_keys: _input = str(input_output.get('prompt', '')).strip()
				elif 'Prompt' in json_keys: _input = str(input_output.get('Prompt', '')).strip()
				elif 'PROMPT' in json_keys: _input = str(input_output.get('PROMPT', '')).strip()
				if 'output' in json_keys: _output = str(input_output.get('output', '')).strip()
				elif 'Output' in json_keys: _output = str(input_output.get('Output', '')).strip()
				elif 'OUTPUT' in json_keys: _output = str(input_output.get('OUTPUT', '')).strip()
				elif 'answer' in json_keys: _output = str(input_output.get('answer', '')).strip()
				elif 'Answer' in json_keys: _output = str(input_output.get('Answer', '')).strip()
				elif 'ANSWER' in json_keys: _output = str(input_output.get('ANSWER', '')).strip()
				elif 'response' in json_keys: _output = str(input_output.get('response', '')).strip()
				elif 'Response' in json_keys: _output = str(input_output.get('Response', '')).strip()
				elif 'RESPONSE' in json_keys: _output = str(input_output.get('RESPONSE', '')).strip()
				if 'file_path' in json_keys: _file_path = str(input_output.get('file_path', '')).strip()
				elif 'File_path' in json_keys: _file_path = str(input_output.get('File_path', '')).strip()
				elif 'FILE_PATH' in json_keys: _file_path = str(input_output.get('FILE_PATH', '')).strip()
				if not _input: _input = str(input_output[json_keys[0]]).strip()
				if not _output: _output = str(input_output[json_keys[1]]).strip()
				return_dictionary['input'], return_dictionary['output'] = _input, _output
				if _file_path: return_dictionary['file_path'] = _file_path
			return return_dictionary
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.__get_input_output: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return {'input': '', 'output': '', 'file_path': ''}
	def __set_hurnet_parameters(self):
		try:
			if self.__sapiens_model:
				if self.embedding_dim is not None: self.__sapiens_model.EMBEDDING_DIM = self.embedding_dim
				if self.block_size is not None: self.__sapiens_model.BLOCK_SIZE = self.block_size
				if self.batch_size is not None: self.__sapiens_model.BATCH_SIZE = self.batch_size
				if self.number_heads is not None: self.__sapiens_model.NUMBER_HEADS = self.number_heads
				if self.number_layers is not None: self.__sapiens_model.NUMBER_LAYERS = self.number_layers
				if self.dropout is not None: self.__sapiens_model.DROPOUT = self.dropout
				if self.learning_rate is not None: self.__sapiens_model.LEARNING_RATE = self.learning_rate
				if self.eval_interval is not None: self.__sapiens_model.EVAL_INTERVAL = self.eval_interval
				if self.epochs is not None: self.__sapiens_model.EPOCHS = self.epochs
				if self.use_bit_net_quantization is not None: self.__sapiens_model.USE_BIT_NET_QUANTIZATION = self.use_bit_net_quantization
				if self.device is not None: self.__sapiens_model.DEVICE = self.device
				if self.end_tag is not None: self.__sapiens_model.END_TAG = self.end_tag
				if self.system_tag is not None: self.__sapiens_model.SYSTEM_TAG = self.system_tag
				if self.user_tag is not None: self.__sapiens_model.USER_TAG = self.user_tag
				if self.assistant_tag is not None: self.__sapiens_model.ASSISTANT_TAG = self.assistant_tag
				if self.tokens_number is not None: self.__sapiens_model.TOKENS_NUMBER = self.tokens_number
				if self.parameters_number is not None: self.__sapiens_model.PARAMETERS_NUMBER = self.parameters_number
				if self.perplexity is not None: self.__sapiens_model.PERPLEXITY = self.perplexity
				if self.weight_decay is not None: self.__sapiens_model.WEIGHT_DECAY = self.weight_decay
				if self.user_id is not None: self.__sapiens_model.USER_ID = self.user_id
				if self.hurnet_embedding_length is not None: self.__sapiens_model.HURNET_EMBEDDING_LENGTH = self.hurnet_embedding_length
				if self.hurnet_division_method is not None: self.__sapiens_model.HURNET_DIVISION_METHOD = self.hurnet_division_method
				if self.include_vocabulary_in_model is not None: self.__sapiens_model.INCLUDE_VOCABULARY_IN_MODEL = self.include_vocabulary_in_model
				if self.use_scheduler is not None: self.__sapiens_model.USE_SCHEDULER = self.use_scheduler
				if self.hurnet_dtype is not None: self.__sapiens_model.HURNET_DTYPE = self.hurnet_dtype
				if self.show_error is not None: self.__sapiens_model.SHOW_ERROR = self.show_error
				if self.show_error_details is not None: self.__sapiens_model.SHOW_ERROR_DETAILS = self.show_error_details
				if self.scheduled is not None: self.__sapiens_model.SCHEDULED = self.scheduled
			return True
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.__set_hurnet_parameters: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return False
	def __save_sapiens_json(self, directory_path=''):
		try:
			directory_path = str(directory_path).strip()
			directory_path = self.__resolve_directory_path(directory_path=directory_path)
			from json import dump
			from os.path import join, isdir
			from os import makedirs
			if not isdir(directory_path): makedirs(directory_path)
			context_window = float('inf') if self.__sub_architecture == 'hur' and self.context_window is None else self.context_window
			data = {
				'architecture': 'sapiens_architecture',
				'sub_architecture': self.__sub_architecture,
				'string': self.string,
				'precision': self.precision,
				'tokenizer': self.tokenizer,
				'method': self.method,
				'interaction': self.interaction,
				'activation_function': self.activation_function,
				'bias': self.bias,
				'learning_rate': self.learning_rate,
				'stochastic_factor': self.stochastic_factor,
				'fx': self.fx,
				'context_window': context_window,
				'end_tag': self.end_tag,
				'validate': self.validate,
				'hurnet_initializer': self.hurnet_initializer,
				'hurnet_layer': self.hurnet_layer,
				'hurnet_fit': self.hurnet_fit,
				'stream_dataset': self.stream_dataset,
				'quantization': self.quantization,
				'experts': self.experts,
				'language': self.language,
				'information_gain': self.information_gain,
				'minimum_score': self.minimum_score,
				'hot': self.hot,
				'max_tokens': self.max_tokens,
				'min_fit_probability': self.min_fit_probability,
				'min_probability': self.min_probability,
				'generalization': self.generalization,
				'temperature': self.temperature,
				'top_k': self.top_k,
				'top_p': self.top_p,
				'system': self.system,
				'messages': self.messages,
				'sapiens_model_path': self.sapiens_model_path,
				'embedding_dim': self.embedding_dim,
				'block_size': self.block_size,
				'batch_size': self.batch_size,
				'number_heads': self.number_heads,
				'number_layers': self.number_layers,
				'dropout': self.dropout,
				'eval_interval': self.eval_interval,
				'epochs': self.epochs,
				'use_bit_net_quantization': self.use_bit_net_quantization,
				'device': str(self.device) if self.device is not None else self.device,
				'user_id': self.user_id,
				'parallel_prediction': self.parallel_prediction,
				'minimum_probability_for_candidates': self.minimum_probability_for_candidates,
				'show_errors': self.show_errors,
				'display_error_point': self.display_error_point,
				'progress': self.progress,
				'scn_architecture': self.scn_architecture,
				'system_tag': self.system_tag,
				'user_tag': self.user_tag,
				'assistant_tag': self.assistant_tag,
				'tokens_number': self.tokens_number,
				'parameters_number': self.parameters_number,
				'perplexity': self.perplexity,
				'weight_decay': self.weight_decay,
				'hurnet_embedding_length': self.hurnet_embedding_length,
				'hurnet_division_method': self.hurnet_division_method,
				'include_vocabulary_in_model': self.include_vocabulary_in_model,
				'use_scheduler': self.use_scheduler,
				'scheduled': str(self.scheduled) if self.scheduled is not None else self.scheduled,
				'hurnet_dtype': str(self.hurnet_dtype) if self.hurnet_dtype is not None else self.hurnet_dtype,
				'show_error': self.show_error,
				'show_error_details': self.show_error_details,
				'delay': self.delay,
				'real_time_generator': self.real_time_generator,
				'online_consultation': self.online_consultation,
				'summary_automation': self.summary_automation,
				'translation_automation': self.translation_automation,
				'mathematical_automation': self.mathematical_automation
			}
			file_path = join(directory_path, 'sapiens.json')
			with open(file_path, 'w', encoding='utf-8') as file: dump(data, file, ensure_ascii=False, indent=4)
			return True
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.__save_sapiens_json: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return False
	def __load_sapiens_json(self, directory_path=''):
		try:
			directory_path = str(directory_path).strip()
			directory_path = self.__resolve_directory_path(directory_path=directory_path)
			from json import load
			from os.path import join, isfile
			file_path = join(directory_path, 'sapiens.json')
			if not isfile(file_path): return False
			with open(file_path, 'r', encoding='utf-8') as file: data = load(file)
			self.__sub_architecture = str(data.get('sub_architecture', 'cpu')).lower().strip()
			try: self.string = str(data.get('string', '')).strip()
			except: self.string = ''
			try: self.precision = float(data.get('precision', 1.0))
			except: self.precision = 1.0
			try: self.tokenizer = str(data.get('tokenizer', 'gpt-4')).lower().strip()
			except: self.tokenizer = 'gpt-4'
			try: self.method = str(data.get('method', 'semantic')).lower().strip()
			except: self.method = 'semantic'
			try: self.interaction = bool(data.get('interaction', True))
			except: self.interaction = True
			try: self.activation_function = str(data.get('activation_function', 'linear')).lower().strip()
			except: self.activation_function = 'linear'
			try: self.bias = float(data.get('bias', 0.0))
			except: self.bias = 0.0
			try: self.learning_rate = float(data.get('learning_rate', 1.0))
			except: self.learning_rate = 1.0
			try: self.stochastic_factor = bool(data.get('stochastic_factor', False))
			except: self.stochastic_factor = False
			try: self.fx = bool(data.get('fx', False))
			except: self.fx = False
			try:
				self.context_window = data.get('context_window', float('inf'))
				if self.__sub_architecture == 'hur' and self.context_window == float('inf'): self.context_window = None
			except: self.context_window = None if self.__sub_architecture == 'hur' else float('inf')
			try: self.end_tag = str(data.get('end_tag', '<|end|>'))
			except: self.end_tag = '<|end|>'
			try: self.validate = float(data.get('validate', 0.0))
			except: self.validate = 0.0
			try: self.hurnet_initializer = bool(data.get('hurnet_initializer', True))
			except: self.hurnet_initializer = True
			try: self.hurnet_layer = bool(data.get('hurnet_layer', False))
			except: self.hurnet_layer = False
			try: self.hurnet_fit = bool(data.get('hurnet_fit', False))
			except: self.hurnet_fit = False
			try: self.stream_dataset = bool(data.get('stream_dataset', False))
			except: self.stream_dataset = False
			try: self.quantization = data.get('quantization', None)
			except: self.quantization = None
			try: self.experts = int(data.get('experts', 1))
			except: self.experts = 1
			try: self.language = data.get('language', None)
			except: self.language = None
			try: self.information_gain = data.get('information_gain', None)
			except: self.information_gain = None
			try: self.minimum_score = float(data.get('minimum_score', 0.5))
			except: self.minimum_score = 0.5
			try: self.hot = bool(data.get('hot', False))
			except: self.hot = False
			try: self.max_tokens = data.get('max_tokens', None)
			except: self.max_tokens = None
			try: self.min_fit_probability = float(data.get('min_fit_probability', 0.7))
			except: self.min_fit_probability = 0.7
			try: self.min_probability = float(data.get('min_probability', 0.01))
			except: self.min_probability = 0.01
			try: self.generalization = bool(data.get('generalization', True))
			except: self.generalization = True
			try: self.temperature = float(data.get('temperature', 0.1))
			except: self.temperature = 0.1
			try: self.top_k = int(data.get('top_k', 0))
			except: self.top_k = 0
			try: self.top_p = float(data.get('top_p', 1.0))
			except: self.top_p = 1.0
			try: self.system = str(data.get('system', '')).strip()
			except: self.system = ''
			try: self.messages = list(data.get('messages', []))
			except: self.messages = []
			try: self.sapiens_model_path = str(data.get('sapiens_model_path', '')).strip()
			except: self.sapiens_model_path = ''
			try: self.embedding_dim = data.get('embedding_dim', None)
			except: self.embedding_dim = None
			try: self.block_size = data.get('block_size', None)
			except: self.block_size = None
			try: self.batch_size = data.get('batch_size', None)
			except: self.batch_size = None
			try: self.number_heads = data.get('number_heads', None)
			except: self.number_heads = None
			try: self.number_layers = data.get('number_layers', None)
			except: self.number_layers = None
			try: self.dropout = data.get('dropout', None)
			except: self.dropout = None
			try: self.eval_interval = data.get('eval_interval', None)
			except: self.eval_interval = None
			try: self.epochs = data.get('epochs', None)
			except: self.epochs = None
			try: self.use_bit_net_quantization = data.get('use_bit_net_quantization', None)
			except: self.use_bit_net_quantization = None
			try: self.device = data.get('device', None)
			except: self.device = None
			try: self.user_id = data.get('user_id', 0)
			except: self.user_id = 0
			try: self.parallel_prediction = bool(data.get('parallel_prediction', False))
			except: self.parallel_prediction = False
			try: self.minimum_probability_for_candidates = float(data.get('minimum_probability_for_candidates', 0.9))
			except: self.minimum_probability_for_candidates = 0.9
			try: self.show_errors = bool(data.get('show_errors', True))
			except: self.show_errors = True
			try: self.display_error_point = bool(data.get('display_error_point', False))
			except: self.display_error_point = False
			try: self.progress = bool(data.get('progress', True))
			except: self.progress = True
			try: self.scn_architecture = str(data.get('scn_architecture', 'level_1')).lower().strip()
			except: self.scn_architecture = 'level_1'
			try: self.system_tag = str(data.get('system_tag', 'System:'))
			except: self.system_tag = 'System:'
			try: self.user_tag = str(data.get('user_tag', 'User:'))
			except: self.user_tag = 'User:'
			try: self.assistant_tag = str(data.get('assistant_tag', 'Assistant:'))
			except: self.assistant_tag = 'Assistant:'
			try: self.tokens_number = int(data.get('tokens_number', 0))
			except: self.tokens_number = 0
			try: self.parameters_number = int(data.get('parameters_number', 0))
			except: self.parameters_number = 0
			try: self.perplexity = float(data.get('perplexity', 100.0))
			except: self.perplexity = 100.0
			try: self.weight_decay = data.get('weight_decay', None)
			except: self.weight_decay = None
			try: self.hurnet_embedding_length = int(data.get('hurnet_embedding_length', 25))
			except: self.hurnet_embedding_length = 25
			try: self.hurnet_division_method = int(data.get('hurnet_division_method', 0))
			except: self.hurnet_division_method = 0
			try: self.include_vocabulary_in_model = bool(data.get('include_vocabulary_in_model', True))
			except: self.include_vocabulary_in_model = True
			try: self.use_scheduler = bool(data.get('use_scheduler', False))
			except: self.use_scheduler = False
			try:
				self.scheduled = data.get('scheduled', None)
				if type(self.scheduled) == str:
					def _string_to_class(class_string=''):
					    from importlib import import_module
					    cleaned = class_string.replace("<class '", '').replace("'>", '')
					    torch_module = import_module('torch')
					    return eval(cleaned, {'torch': torch_module})
					self.scheduled = _string_to_class(self.scheduled)
			except: self.scheduled = None
			try:
				self.hurnet_dtype = data.get('hurnet_dtype', None)
				if type(self.hurnet_dtype) == str:
					def _string_to_torch_dtype(dtype_string=''):
						from importlib import import_module
						torch_module = import_module('torch')
						return eval(dtype_string, {'torch': torch_module})
					self.hurnet_dtype = _string_to_torch_dtype(self.hurnet_dtype)
			except: self.hurnet_dtype = None
			try: self.show_error = bool(data.get('show_error', False))
			except: self.show_error = False
			try: self.show_error_details = bool(data.get('show_error_details', False))
			except: self.show_error_details = False
			try: self.delay = float(data.get('delay', 0.01))
			except: self.delay = 0.01
			try: self.real_time_generator = bool(data.get('real_time_generator', False))
			except: self.real_time_generator = False
			try: self.online_consultation = bool(data.get('online_consultation', True))
			except: self.online_consultation = True
			try: self.summary_automation = bool(data.get('summary_automation', True))
			except: self.summary_automation = True
			try: self.translation_automation = bool(data.get('translation_automation', True))
			except: self.translation_automation = True
			try: self.mathematical_automation = bool(data.get('mathematical_automation', True))
			except: self.mathematical_automation = True
			return True
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.__load_sapiens_json: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return False
	def __get_online_answer(self, prompt=''):
		try:
			obtained_response = ''
			prompt = str(prompt).strip()
			def ___eligible_question(question=''):
				eligible_question_result = [False, '']
				question = str(question).lower().strip()
				words_length = len(question.split())
				if words_length > 10: return eligible_question_result
				elif not question.endswith(chr(63)): return eligible_question_result
				forbidden_strings = ('your name', 'sapiens chat', 'sapiens technology')
				for forbidden_string in forbidden_strings:
					if forbidden_string in question: return eligible_question_result
				terms_strings = ('who is', '¿quién es', '¿quien es', 'quem é', 'quem e', 'who was', '¿quién fue', '¿quien fue', 'quem foi',
				'¿quién era', '¿quien era', 'quem era', 'who were', '¿quiénes fueron', '¿quienes fueron', 'quem foram', '¿quiénes eran',
				'¿quienes eran', 'quem eram', 'what is', "what's", 'whats', 'what`s', 'what’s', '¿qué es', '¿que es', 'o que é', 'oque é', 'o que e',
				'oque e', 'o quê é', 'oquê é', 'o quê e', 'oquê e', 'what was', 'what were', '¿qué fueron', '¿que fueron', '¿qué fue',
				'¿que fue', 'o quê foi', 'oquê foi', 'o quê foram', 'oquê foram', 'o que foi', 'oque foi', 'o que foram', 'oque foram',
				'¿qué eran', '¿que eran', '¿qué era', '¿que era', 'o quê eram', 'o que eram', 'oquê eram', 'oque eram', 'o quê era',
				'o que era', 'oquê era', 'oque era', 'cuál es', 'cual es', 'qual é', 'qual e', 'what are', "what're", 'whatre', 'what`re',
				'what’re', 'cuáles son', 'cuales son', 'quais são', 'quais sao', 'who are', 'quiénes son', 'quienes son', 'quem são', 'quem sao')
				connections_strings = ('a', 'an', 'the', 'some', 'un', 'una', 'el', 'la', 'unos', 'unas',
				'los', 'las', 'um', 'uma', 'o', 'á', 'à', 'uns', 'umas', 'os', 'as', 'ás', 'às')
				for term_string in terms_strings:
					term_string = str(term_string).lower().strip()
					if question.startswith(term_string+chr(32)):
						new_question = question.split(term_string)[-1].strip()
						for connection_string in connections_strings:
							if new_question.startswith(connection_string+chr(32)):
								other_question = new_question.split(term_string)[-1].strip()
								if other_question.endswith(chr(63)):
									title, eligible_question = other_question[:-1].strip(), True
									eligible_question_result[0] = eligible_question
									eligible_question_result[1] = title
									break
						if not eligible_question_result[0] and new_question.endswith(chr(63)):
							title, eligible_question = new_question[:-1].strip(), True
							eligible_question_result[0] = eligible_question
							eligible_question_result[1] = title
				return eligible_question_result
			def ___formats_content(content=''):
				page_content_lines = content.split('\n')
				for index, page_content_line in enumerate(page_content_lines):
					page_content_line = page_content_line.strip()
					if page_content_line:
						if page_content_line.startswith('=') and '= ' in page_content_line:
							page_content_line = page_content_line.rstrip('=')
							if '====== ' in page_content_line: page_content_line = page_content_line.replace('====== ', '###### ').strip()
							if '===== ' in page_content_line: page_content_line = page_content_line.replace('===== ', '##### ').strip()
							if '==== ' in page_content_line: page_content_line = page_content_line.replace('==== ', '#### ').strip()
							if '=== ' in page_content_line: page_content_line = page_content_line.replace('=== ', '### ').strip()
							if '== ' in page_content_line: page_content_line = page_content_line.replace('== ', '## ').strip()
							if '= ' in page_content_line: page_content_line = page_content_line.replace('= ', '# ').strip()
							page_content_lines[index] = page_content_line
				content = str('\n'.join(page_content_lines)).strip()
				return content
			eligible_question_result = ___eligible_question(question=prompt)
			eligible_result = eligible_question_result[0]
			eligible_tile = eligible_question_result[-1]
			if eligible_result:
				from sapiens_dataset import SapiensDataset
				from utilities_nlp import UtilitiesNLP as SapiensUtilities
				sapiens_dataset = SapiensDataset(show_errors=False, display_error_point=False)
				sapiens_utilities = SapiensUtilities(show_errors=False, display_error_point=False)
				language = sapiens_utilities.getLanguage(prompt)
				obtained_response = sapiens_dataset.wikipediaArticleSummary(eligible_tile, language if language else None)
			if obtained_response: obtained_response = ___formats_content(content=obtained_response)
			return obtained_response.strip()
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.__get_online_answer: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return ''
	def __mathematical_solution(self, prompt=''):
		try:
			mathematical_solution = ''
			prompt = str(prompt).strip()
			from utilities_nlp import UtilitiesNLP as SapiensUtilities
			sapiens_utilities = SapiensUtilities(show_errors=self.__show_errors, display_error_point=self.__display_error_point)
			count_tokens = sapiens_utilities.countTokens(string=prompt, pattern='gpt')
			if count_tokens > 150: return mathematical_solution
			from re import search, sub, finditer
			def _check_operation(text=''):
				temp_text = text.replace('x', '*').replace('X', '*').replace('ˆ', '**').replace('^', '**')
				temp_text = temp_text.replace('⁰', '** 0').replace('¹', '** 1').replace('²', '** 2').replace('³', '** 3').replace('⁴', '** 4')
				temp_text = temp_text.replace('⁵', '** 5').replace('⁶', '** 6').replace('⁷', '** 7').replace('⁸', '** 8').replace('⁹', '** 9')
				temp_text = temp_text.replace('raised to the power of', '**').replace('elevado a la', '**').replace('elevado à', '**').replace('elevado a', '**')
				number = r'[-+]?\d+(?:[.,]\d+)?'
				operators = [r'\*\*\=', r'\+\=', r'-\=', r'/\=', r'//\=', r'%\=', r'\*\=', r'\*\*(?!\=)', r'//(?!\=)', r'<=', r'>=', r'!=', r'\+(?!\=)', r'-(?!\=)', r'/(?!\=)', r'%(?!\=)', r'\*(?!\=)', r'<(?!\=)', r'>(?!\=)']
				for operator in operators:
					pattern = rf'{number}\s*{operator}\s*{number}'
					if search(pattern, temp_text): return True
				return False
			def _process_and_calculate(text=''):
				processed_text = sub(r'(\d),(\d)', r'\1.\2', text)
				processed_text = processed_text.replace('x', '*').replace('X', '*').replace('ˆ', '**').replace('^', '**')
				processed_text = processed_text.replace('⁰', '** 0').replace('¹', '** 1').replace('²', '** 2').replace('³', '** 3').replace('⁴', '** 4')
				processed_text = processed_text.replace('⁵', '** 5').replace('⁶', '** 6').replace('⁷', '** 7').replace('⁸', '** 8').replace('⁹', '** 9')
				processed_text = processed_text.replace('raised to the power of', '**').replace('elevado a la', '**').replace('elevado à', '**').replace('elevado a', '**')
				expression_pattern = r'[(\[]*[-+]?\d+(?:\.\d+)?[)\]]*(?:\s*(?:\*\*\=?|//\=?|[+\-*/%<>=!]+\=?)\s*[(\[]*[-+]?\d+(?:\.\d+)?[)\]]*)+|[(\[][-+]?\d+(?:\.\d+)?(?:\s*(?:\*\*\=?|//\=?|[+\-*/%<>=!]+\=?)\s*[-+]?\d+(?:\.\d+)?)+[)\]](?:\s*(?:\*\*\=?|//\=?|[+\-*/%<>=!]+\=?)\s*[(\[]*[-+]?\d+(?:\.\d+)?[)\]]*)*'
				matches = list(finditer(expression_pattern, processed_text))
				if not matches: return ''
				best_match = max(matches, key=lambda m: len(m.group()))
				expression = best_match.group().strip()
				open_paren = expression.count('(')
				close_paren = expression.count(')')
				open_bracket = expression.count('[')
				close_bracket = expression.count(']')
				start_pos = best_match.start()
				end_pos = best_match.end()
				while open_paren > close_paren and end_pos < len(processed_text):
					if processed_text[end_pos] == ')':
						close_paren += 1
						end_pos += 1
						expression = processed_text[start_pos:end_pos].strip()
					else: end_pos += 1
				while open_bracket > close_bracket and end_pos < len(processed_text):
					if processed_text[end_pos] == ']':
						close_bracket += 1
						end_pos += 1
						expression = processed_text[start_pos:end_pos].strip()
					else: end_pos += 1
				while close_paren > open_paren and start_pos > 0:
					start_pos -= 1
					if processed_text[start_pos] == '(':
						open_paren += 1
						expression = processed_text[start_pos:end_pos].strip()
				while close_bracket > open_bracket and start_pos > 0:
					start_pos -= 1
					if processed_text[start_pos] == '[':
						open_bracket += 1
						expression = processed_text[start_pos:end_pos].strip()
				try:
					result = eval(expression)
					return f'{expression} = {result}'
				except: return ''
			def _calculate_expression(text=''):
				if _check_operation(text=text): return _process_and_calculate(text=text.replace('[', '(').replace(']', ')') if '[' in text and ']' in text else text)
				else: return ''
			lines, calculate, calculated_expressions = prompt.split('\n'), False, []
			for line in lines:
				calculate_expression = _calculate_expression(text=str(line).strip())
				if calculate_expression:
					calculated_expressions.append(calculate_expression)
					calculate = True
			if calculate and calculated_expressions: mathematical_solution = '\n'.join(calculated_expressions)
			return mathematical_solution.strip()
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.__mathematical_solution: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return False
	def training(self, dataset_path='', sub_architecture='cpu', progress=True):
		try:
			sub_architecture, training_function = str(sub_architecture).lower().strip(), False
			if sub_architecture == 'cpu':
				self.__sapiens_model = self.__sapiens_cpu(show_errors=self.show_errors, display_error_point=self.display_error_point)
				if self.end_tag is not None: self.__sapiens_model.END_TAG = self.end_tag
				if self.experts is not None: self.__sapiens_model.N_EXPERTS = self.experts
				is_json = dataset_path.lower().strip().endswith('.json')
				if is_json:
					string_content, fit_structure, data = '', [], []
					from utilities_nlp import UtilitiesNLP as SapiensUtilities
					sapiens_utilities = SapiensUtilities(show_errors=self.__show_errors, display_error_point=self.__display_error_point)
					with open(dataset_path, 'r', encoding='utf-8') as file_object: string_content = str(file_object.read()).strip()
					if string_content: fit_structure = sapiens_utilities.stringToDictionaryOrJSON(string=string_content)
					if type(fit_structure) == dict:
						json_keys = list(fit_structure.keys())
						if 'data' in json_keys: data = list(fit_structure.get('data', []))
						else:
							data_key = str(json_keys[0]).strip()
							data = list(fit_structure.get(data_key, []))
						if data:
							from tqdm import tqdm
							total_length, data_string = len(data), ''
							with tqdm(total=total_length, unit='item', disable=not progress) as progress_bar:
								for input_output in data:
									input_output = self.__get_input_output(json_dictionary=input_output)
									_input, _output = input_output.get('input', ''), input_output.get('output', '')
									if _input and _output: data_string += f'{_input}\n{_output}\n\n{self.end_tag}\n\n'
									if progress:
										progress_bar.set_description('Reading data')
										progress_bar.update(1)
							data_string = data_string.strip()
							if data_string:
								temporary_files_directory = sapiens_utilities.getTemporaryFilesDirectory()
								hash_code = sapiens_utilities.getHashCode()
								file_name = f'{temporary_files_directory}{hash_code}.txt'
								with open(file_name, 'w', encoding='utf-8') as file_object: file_object.write(data_string)
								training_function = self.__sapiens_model.train(dataset_path=file_name, progress=progress)
								sapiens_utilities.deleteFile(file_name)
							else: return False
						else: return False
					elif type(fit_structure) in (tuple, list): data = fit_structure
				else: training_function = self.__sapiens_model.train(dataset_path=dataset_path, progress=progress)
			elif sub_architecture == 'scn':
				if self.scn_architecture == 'level_1':
					self.__sapiens_model = self.__semantic_comparison_network()
					if self.tokenizer.startswith('gpt'): self.tokenizer = 'gpt'
					training_function = self.__sapiens_model.train(dataset_path=dataset_path, string=self.string, precision=self.precision, tokenizer=self.tokenizer, method=self.method, interaction=self.interaction, activation_function=self.activation_function, bias=self.bias, learning_rate=self.learning_rate, stochastic_factor=self.stochastic_factor, fx=self.fx, progress=progress)
				elif self.scn_architecture == 'level_3':
					self.__sapiens_model = self.__scn(device=self.device, user_id=self.user_id, parallel_prediction=self.parallel_prediction, minimum_probability_for_candidates=self.minimum_probability_for_candidates, show_errors=self.show_errors)
					training_function = self.__sapiens_model.train(dataset_path=dataset_path, string=self.string, precision=self.precision, tokenizer=self.tokenizer, context_window=self.context_window, end_tag=self.end_tag, validate=self.validate, progress=progress)
				else:
					self.__sapiens_model = self.__scnetwork(device=self.device, user_id=self.user_id, parallel_prediction=self.parallel_prediction, minimum_probability_for_candidates=self.minimum_probability_for_candidates, show_errors=self.show_errors)
					training_function = self.__sapiens_model.train(dataset_path=dataset_path, string=self.string, precision=self.precision, tokenizer=self.tokenizer, context_window=self.context_window, end_tag=self.end_tag, validate=self.validate, progress=progress)
			elif sub_architecture == 'hur':
				if self.learning_rate == 1.0: self.learning_rate = None
				if self.context_window == float('inf'): self.context_window = None
				self.__sapiens_model = self.__hur_multimodal(embedding_dim=self.embedding_dim, block_size=self.block_size, batch_size=self.batch_size, number_heads=self.number_heads, number_layers=self.number_layers, dropout=self.dropout, learning_rate=self.learning_rate, eval_interval=self.eval_interval, epochs=self.epochs, use_bit_net_quantization=self.use_bit_net_quantization, device=self.device)
				self.__set_hurnet_parameters()
				training_function = self.__sapiens_model.train(dataset_path=dataset_path, string=self.string, precision=self.precision, tokenizer=self.tokenizer, context_window=self.context_window, hurnet_initializer=self.hurnet_initializer, hurnet_layer=self.hurnet_layer, hurnet_fit=self.hurnet_fit, end_tag=self.end_tag, stream_dataset=self.stream_dataset, validate=self.validate, quantization=self.quantization, experts=self.experts, progress=progress)
				self.tokens_number = self.__sapiens_model.TOKENS_NUMBER
				self.parameters_number = self.__sapiens_model.PARAMETERS_NUMBER
			elif sub_architecture == 'mgt':
				self.__sapiens_model = self.__mgt(show_errors=self.show_errors, display_error_point=self.display_error_point, progress=self.progress and progress)
				_MGT__interpretation = self.__sapiens_model._MGT__interpretation
				_MGT__database = self.__sapiens_model._MGT__database
				_MGT__n_tokens = self.__sapiens_model._MGT__n_tokens
				old_interpretation = _MGT__interpretation if _MGT__interpretation else _MGT__database
				training_function = self.__sapiens_model.train(path=dataset_path, language=self.language, information_gain=self.information_gain)
				if old_interpretation and _MGT__n_tokens:
					self.__scnetwork().textSummary(text=old_interpretation, max_tokens=_MGT__n_tokens)
					self.__sapiens_model._MGT__interpretation = old_interpretation
			else:
				self.__sapiens_model = self.__scnetwork(device=self.device, user_id=self.user_id, parallel_prediction=self.parallel_prediction, minimum_probability_for_candidates=self.minimum_probability_for_candidates, show_errors=self.show_errors)
				training_function = self.__sapiens_model.train(dataset_path=dataset_path, string=self.string, precision=self.precision, tokenizer=self.tokenizer, context_window=self.context_window, end_tag=self.end_tag, validate=self.validate, progress=progress)
			self.__sub_architecture = sub_architecture
			return training_function
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.training: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return False
	def saveModel(self, model_path='', progress=True):
		try:
			model_path = str(model_path).strip()
			progress, progress_bar = bool(progress) if type(progress) in (bool, int, float) else True, None
			if not self.__sapiens_model:
				if self.__show_errors or self.show_error: print('The model has not yet been trained.')
				return False
			def _ensure_path_exists(file_path=''):
				from os.path import dirname, exists
				from os import makedirs
				directory_path = dirname(file_path)
				if len(directory_path) == 0: return
				if not exists(directory_path): makedirs(directory_path)
			_ensure_path_exists(file_path=model_path)
			if self.__sub_architecture in ('cpu', 'mgt'):
				if self.__sub_architecture == 'mgt': self.__sapiens_model._MGT__progress = progress
				if self.__sub_architecture == 'cpu' and progress:
					from tqdm import tqdm
					from shutil import get_terminal_size
					total_value, terminal_width = 100, get_terminal_size().columns
					progress_bar = tqdm(total=total_value, desc='Saving', ncols=terminal_width)
					progress_bar.update(50)
				saved_model = self.__sapiens_model.saveModel(model_path=model_path)
				if self.__sub_architecture == 'cpu' and progress and progress_bar is not None:
					progress_bar.update(50)
					progress_bar.n = 100
					progress_bar.refresh()
					progress_bar.close()
			else:
				if self.__copy_folder_to_temp and self.__sub_architecture == 'scn' and self.scn_architecture in ('level_2', 'level_3'):
					def _delete_folder(folder_path=''):
						from shutil import rmtree
						try:
							rmtree(folder_path)
							return True
						except: return False
					def _copy_files_with_defined_name(source_folder_path='', destination_folder_path='', defined_name=''):
						from os import listdir, makedirs
						from os.path import isfile, join, splitext
						from shutil import copy2
						makedirs(destination_folder_path, exist_ok=True)
						for item in listdir(source_folder_path):
							source_item_path = join(source_folder_path, item)
							if isfile(source_item_path):
								file_extension = splitext(item)[1]
								destination_item_path = join(destination_folder_path, defined_name + file_extension)
								copy2(source_item_path, destination_item_path)
					from pathlib import Path
					file_name = Path(model_path).name
					if not Path(model_path).is_dir(): model_path = str(Path(model_path).parent)
					_copy_files_with_defined_name(source_folder_path=self.__copy_folder_to_temp, destination_folder_path=model_path, defined_name=file_name)
					_delete_folder(folder_path=self.__copy_folder_to_temp)
					self.__copy_folder_to_temp, saved_model = '', True
				else: saved_model = self.__sapiens_model.saveModel(model_path=model_path, progress=progress)
			save_sapiens_json = self.__save_sapiens_json(directory_path=model_path)
			return saved_model and save_sapiens_json
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.saveModel: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return False
	def loadModel(self, model_path='', progress=True):
		try:
			loaded_model = False
			model_path = str(model_path).strip()
			progress = bool(progress) if type(progress) in (bool, int, float) else True
			loaded_model = self.__load_sapiens_json(directory_path=model_path)
			self.__model_path = model_path
			from pathlib import Path
			file_name = Path(model_path).name
			if model_path and '.' in file_name and not Path(model_path).is_file():
				if self.__show_errors or self.show_error: print(f'The referenced model "{model_path}" DOES NOT EXIST.')
				return False
			def _has_file_with_extensions(folder_path='', extensions=[]):
				if not Path(folder_path).is_dir(): folder_path = Path(folder_path).parent
				from os import walk
				normalized_extensions = []
				for extension in extensions:
					extension = extension.lower().strip()
					if not extension.startswith('.'): extension = '.' + extension
					normalized_extensions.append(extension)
				for root, directories, files in walk(folder_path):
					for file_name in files:
						lower_name = file_name.lower()
						for extension in normalized_extensions:
							if lower_name.endswith(extension): return True
				return False
			if _has_file_with_extensions(folder_path=model_path, extensions=['cpu']): self.__sub_architecture = 'cpu'
			elif _has_file_with_extensions(folder_path=model_path, extensions=['scconf', 'scnnet', 'vocabu']): self.__sub_architecture, self.scn_architecture = 'scn', 'level_1'
			elif _has_file_with_extensions(folder_path=model_path, extensions=['sccon', 'scnet']): self.__sub_architecture, self.scn_architecture = 'scn', 'level_2'
			elif _has_file_with_extensions(folder_path=model_path, extensions=['scn01', 'scn02', 'scn03']): self.__sub_architecture, self.scn_architecture = 'scn', 'level_3'
			elif _has_file_with_extensions(folder_path=model_path, extensions=['hurlm']): self.__sub_architecture = 'hur'
			elif _has_file_with_extensions(folder_path=model_path, extensions=['mini']): self.__sub_architecture = 'mgt'
			if self.__sub_architecture == 'cpu':
				self.__sapiens_model, progress_bar = self.__sapiens_cpu(show_errors=self.show_errors, display_error_point=self.display_error_point), None
				if progress:
					from tqdm import tqdm
					from shutil import get_terminal_size
					total_value, terminal_width = 100, get_terminal_size().columns
					progress_bar = tqdm(total=total_value, desc='Loading', ncols=terminal_width)
					progress_bar.update(50)
				loaded_model = self.__sapiens_model.loadModel(model_path=model_path)
				self.end_tag = self.__sapiens_model.END_TAG
				self.experts = self.__sapiens_model.N_EXPERTS
				if progress and progress_bar is not None:
					progress_bar.update(50)
					progress_bar.n = 100
					progress_bar.refresh()
					progress_bar.close()
			elif self.__sub_architecture == 'scn':
				if self.scn_architecture == 'level_1': self.__sapiens_model = self.__semantic_comparison_network()
				elif self.scn_architecture == 'level_2': self.__sapiens_model = self.__scnetwork(device=self.device, user_id=self.user_id, parallel_prediction=self.parallel_prediction, minimum_probability_for_candidates=self.minimum_probability_for_candidates, show_errors=self.show_errors)
				elif self.scn_architecture == 'level_3': self.__sapiens_model = self.__scn(device=self.device, user_id=self.user_id, parallel_prediction=self.parallel_prediction, minimum_probability_for_candidates=self.minimum_probability_for_candidates, show_errors=self.show_errors)
				loaded_model = self.__sapiens_model.loadModel(model_path=model_path, progress=progress)
				if self.scn_architecture in ('level_2', 'level_3'):
					self.__sapiens_model.user_id = self.user_id
					self.__sapiens_model.minimum_probability_for_candidates = self.minimum_probability_for_candidates
					self.__sapiens_model.fit_probability = self.min_fit_probability
					self.__sapiens_model.probability = self.min_probability
					self.parameters_number = self.__sapiens_model.parameters_number
			elif self.__sub_architecture == 'hur':
				self.__sapiens_model = self.__hur_multimodal(embedding_dim=self.embedding_dim, block_size=self.block_size, batch_size=self.batch_size, number_heads=self.number_heads, number_layers=self.number_layers, dropout=self.dropout, learning_rate=self.learning_rate, eval_interval=self.eval_interval, epochs=self.epochs, use_bit_net_quantization=self.use_bit_net_quantization, device=self.device)
				loaded_model = self.__sapiens_model.loadModel(model_path=model_path, progress=progress)
				self.embedding_dim = self.__sapiens_model.EMBEDDING_DIM
				self.block_size = self.__sapiens_model.BLOCK_SIZE
				self.batch_size = self.__sapiens_model.BATCH_SIZE
				self.number_heads = self.__sapiens_model.NUMBER_HEADS
				self.number_layers = self.__sapiens_model.NUMBER_LAYERS
				self.dropout = self.__sapiens_model.DROPOUT
				self.learning_rate = self.__sapiens_model.LEARNING_RATE
				self.eval_interval = self.__sapiens_model.EVAL_INTERVAL
				self.epochs = self.__sapiens_model.EPOCHS
				self.use_bit_net_quantization = self.__sapiens_model.USE_BIT_NET_QUANTIZATION
				self.device = self.__sapiens_model.DEVICE
				self.end_tag = self.__sapiens_model.END_TAG
				self.system_tag = self.__sapiens_model.SYSTEM_TAG
				self.user_tag = self.__sapiens_model.USER_TAG
				self.assistant_tag = self.__sapiens_model.ASSISTANT_TAG
				self.tokens_number = self.__sapiens_model.TOKENS_NUMBER
				self.parameters_number = self.__sapiens_model.PARAMETERS_NUMBER
				self.perplexity = self.__sapiens_model.PERPLEXITY
				self.weight_decay = self.__sapiens_model.WEIGHT_DECAY
				self.user_id = self.__sapiens_model.USER_ID
				self.hurnet_embedding_length = self.__sapiens_model.HURNET_EMBEDDING_LENGTH
				self.hurnet_division_method = self.__sapiens_model.HURNET_DIVISION_METHOD
				self.include_vocabulary_in_model = self.__sapiens_model.INCLUDE_VOCABULARY_IN_MODEL
				self.use_scheduler = self.__sapiens_model.USE_SCHEDULER
				self.hurnet_dtype = self.__sapiens_model.HURNET_DTYPE
				self.show_error = self.__sapiens_model.SHOW_ERROR
				self.show_error_details = self.__sapiens_model.SHOW_ERROR_DETAILS
				self.scheduled = self.__sapiens_model.SCHEDULED
			elif self.__sub_architecture == 'mgt':
				self.__sapiens_model = self.__mgt(show_errors=self.show_errors, display_error_point=self.display_error_point, progress=self.progress and progress)
				loaded_model = self.__sapiens_model.loadModel(model_path=model_path)
			else: loaded_model = False
			return loaded_model
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.loadModel: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return False
	def fineTuning(self, dataset_path='', progress=True):
		try:
			adjusted_model = False
			dataset_path = str(dataset_path).strip()
			progress = bool(progress) if type(progress) in (bool, int, float) else True
			if self.__sub_architecture == 'mgt':
				import tqdm
				original_tqdm_init = tqdm.tqdm.__init__
				def disable_tqdm():
					def silent_init(self, *args, **kwargs):
						kwargs['disable'] = True
						original_tqdm_init(self, *args, **kwargs)
					tqdm.tqdm.__init__ = silent_init
				def enable_tqdm(): tqdm.tqdm.__init__ = original_tqdm_init
				if not progress: disable_tqdm()
				try: adjusted_model = self.__sapiens_model.fineTuning(file_path=dataset_path)
				finally:
					if not progress: enable_tqdm()
			elif self.__sub_architecture == 'cpu': adjusted_model = self.__sapiens_model.fineTuning(dataset_path=dataset_path, progress=progress)
			else:
				if self.__model_path and self.__sub_architecture == 'scn' and self.scn_architecture in ('level_2', 'level_3'):
					from pathlib import Path
					from os.path import join
					def _copy_folder_to_temp(folder_path=''):
					    folder_path = Path(folder_path)
					    file_name = ''
					    if not folder_path.is_dir():
					        file_name = folder_path.stem
					        folder_path = folder_path.parent
					    from tempfile import gettempdir
					    from shutil import copytree, rmtree, copy2
					    from os.path import exists, join, splitext
					    from os import makedirs, listdir
					    temp_directory = gettempdir()
					    folder_name = folder_path.name
					    destination_path = join(temp_directory, folder_name)
					    if exists(destination_path): rmtree(destination_path)
					    if file_name != '':
					        makedirs(destination_path)
					        for current_file in listdir(folder_path):
					            if splitext(current_file)[0] == file_name: copy2(join(folder_path, current_file), destination_path)
					    else: copytree(folder_path, destination_path)
					    self.__copy_folder_to_temp = destination_path
					    return destination_path
					if self.scn_architecture == 'level_2' and self.__sapiens_model: del self.__sapiens_model
					elif self.scn_architecture == 'level_3': self.__sapiens_model.close()
					model_path = _copy_folder_to_temp(folder_path=self.__model_path)
					if self.scn_architecture == 'level_2': self.__sapiens_model = self.__scnetwork(device=self.device, user_id=self.user_id, parallel_prediction=self.parallel_prediction, minimum_probability_for_candidates=self.minimum_probability_for_candidates, show_errors=self.show_errors)
					elif self.scn_architecture == 'level_3': self.__sapiens_model = self.__scn(device=self.device, user_id=self.user_id, parallel_prediction=self.parallel_prediction, minimum_probability_for_candidates=self.minimum_probability_for_candidates, show_errors=self.show_errors)
					model_name = Path(self.__model_path).name
					model_path = join(model_path, model_name)
					self.__sapiens_model.loadModel(model_path=model_path, progress=progress)
				def _read_remote_file(remote_path=''):
					remote_path = str(remote_path).strip()
					from urllib.request import urlopen
					try:
						from os import environ
						from certifi import where
						environ['SSL_CERT_FILE'] = where()
						from logging import getLogger, ERROR
						getLogger('urlopen').setLevel(ERROR)
					except: pass
					remote_stream = urlopen(remote_path)
					content = remote_stream.read().decode('utf-8')
					return str(content).strip()
				is_json, string_content = dataset_path.lower().endswith('.json'), ''
				if dataset_path.startswith(('https://', 'http://')): string_content = _read_remote_file(remote_path=dataset_path)
				else:
					with open(dataset_path, 'r', encoding='utf-8') as file_object: string_content = str(file_object.read()).strip()
				if is_json:
					fit_structure, data = [], []
					from utilities_nlp import UtilitiesNLP as SapiensUtilities
					sapiens_utilities = SapiensUtilities(show_errors=self.__show_errors, display_error_point=self.__display_error_point)
					if string_content: fit_structure = sapiens_utilities.stringToDictionaryOrJSON(string=string_content)
					if fit_structure:
						if type(fit_structure) == dict:
							json_keys = list(fit_structure.keys())
							if 'data' in json_keys: data = list(fit_structure.get('data', []))
							else:
								data_key = str(json_keys[0]).strip()
								data = list(fit_structure.get(data_key, []))
						elif type(fit_structure) in (tuple, list): data = fit_structure
						if data:
							from tqdm import tqdm
							total_length = len(data)
							with tqdm(total=total_length, unit='item', disable=not progress) as progress_bar:
								for input_output in data:
									_input, _output, _file_path = '', '', ''
									input_output = self.__get_input_output(json_dictionary=input_output)
									_input, _output, _file_path = input_output.get('input', ''), input_output.get('output', ''), input_output.get('file_path', '')
									if _input and _output:
										if self.__sub_architecture == 'hur':
											try:
												if self.epochs: self.__sapiens_model.addFit(prompt=_input, answer=_output, file_path=_file_path)
												else: self.__sapiens_model.addSemanticFit(prompt=_input, answer=_output, file_path=_file_path, precision=self.precision)
											except: self.__sapiens_model.addFit(prompt=_input, answer=_output)
										else: self.__sapiens_model.addFit(prompt=_input, answer=_output)
									if progress:
										progress_bar.set_description('Adjusting')
										progress_bar.update(1)
							adjusted_model = total_length > 0
				elif self.__show_errors or self.show_error:
					print('The file must be a JSON with a "data" key containing an array of objects with the keys "input" and "output".')
					adjusted_model = False
			if self.__model_path and self.__sub_architecture == 'scn' and self.scn_architecture in ('level_2', 'level_3'):
				if self.scn_architecture == 'level_2' and self.__sapiens_model:
					del self.__sapiens_model
					self.__sapiens_model = self.__scnetwork(device=self.device, user_id=self.user_id, parallel_prediction=self.parallel_prediction, minimum_probability_for_candidates=self.minimum_probability_for_candidates, show_errors=self.show_errors)
				elif self.scn_architecture == 'level_3': self.__sapiens_model.close()
			elif self.__sub_architecture == 'hur':
				self.__set_hurnet_parameters()
				self.__sapiens_model.EPOCHS = self.epochs if self.epochs else 1000
				self.__sapiens_model.train(precision=self.precision, progress=progress)
			return adjusted_model
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.fineTuning: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return False			
	def inference(self, prompt='', file_path='', stream=False):
		try:
			prompt, file_path, inference_function = str(prompt).strip(), str(file_path).strip(), ''
			stream, task_names = bool(stream) if type(stream) in (bool, int, float) else False, []
			if not prompt: prompt = '?'
			def _get_tokens(inference_function='', stream=False, generator=False):
				if generator:
					if stream: return inference_function
					else:
						tokens = []
						for token in inference_function: tokens.append(token)
						inference_function = str(''.join(tokens)).strip()
						return inference_function
				else:
					tokens = inference_function.split(chr(32))
					def __get_tokens(tokens=[]):
						def ___capitalize_first_letter_preserve_rest(text=''):
							if not text: return text
							return text[0].upper() + text[1:]
						tokens_length = len(tokens)
						for index, token in enumerate(tokens):
							counter = index + 1
							if counter <= 1: token = ___capitalize_first_letter_preserve_rest(text=token.lstrip())
							if 1 <= counter < tokens_length: token = token + chr(32)
							if counter == tokens_length: token = token.rstrip()
							yield token
					if stream: return __get_tokens(tokens=tokens)
					else: return inference_function
			if self.mathematical_automation:
				mathematical_solution = self.__mathematical_solution(prompt=prompt)
				if mathematical_solution: inference_function = mathematical_solution
			if not inference_function and self.online_consultation:
				online_consultation = self.__get_online_answer(prompt=prompt)
				if online_consultation: inference_function = online_consultation
			inference_function = str(inference_function).strip()
			if inference_function: return _get_tokens(inference_function=inference_function, stream=stream, generator=False)
			from utilities_nlp import UtilitiesNLP as SapiensUtilities
			sapiens_utilities = SapiensUtilities(show_errors=False, display_error_point=False)
			task_names = sapiens_utilities.getTasks(prompt=prompt)
			from pathlib import Path
			if file_path and not Path(file_path).is_file():
				if self.__show_errors or self.show_error: print(f'The referenced file "{file_path}" DOES NOT EXIST.')
				return False
			elif file_path and self.__sub_architecture != 'hur':
				from INFINITE_CONTEXT_WINDOW import InfiniteContextWindow as SAPIENS_INFINITE_CONTEXT_WINDOW
				interpreted_file = SAPIENS_INFINITE_CONTEXT_WINDOW(show_errors=self.show_errors, display_error_point=self.display_error_point).interpreter(file_path=file_path)
				prompt = rf'{interpreted_file}\n\n{prompt}'
			authorized_task = False
			def _capitalize_sentences(text=''):
				result = []
				capitalize_next = True
				for character in text:
					if capitalize_next and character.isalpha():
						result.append(character.upper())
						capitalize_next = False
					else: result.append(character)
					if character in '.!?': capitalize_next = True
				return ''.join(result)
			if task_names and 'TEXT_SUMMARY' in task_names and self.summary_automation: inference_function, authorized_task = sapiens_utilities.summary(string=prompt, topics=False), True
			elif task_names and 'TEXT_SUMMARY_WITH_BULLET_POINTS' in task_names and self.summary_automation: inference_function, authorized_task = sapiens_utilities.summary(string=prompt, topics=True), True
			elif task_names and any(task.startswith('TRANSLATION_') for task in task_names) and self.translation_automation:
				target_language = 'en'
				for task in task_names:
					if task.startswith('TRANSLATION_'):
						target_language = task.split('TRANSLATION_')[-1].lower().strip()
						break
				inference_function, authorized_task = sapiens_utilities.translate(string=prompt, source_language='auto', target_language=target_language), True
			if authorized_task: inference_function = _capitalize_sentences(sapiens_utilities.formatPrompt(prompt=inference_function, task_names=task_names))
			if inference_function: return _get_tokens(inference_function=inference_function, stream=stream, generator=False)
			if not self.__sapiens_model:
				if self.__show_errors or self.show_error: print('This model has not yet been trained.')
				return False
			if self.__sub_architecture == 'cpu':
				if self.end_tag is not None: self.__sapiens_model.END_TAG = self.end_tag
				inference_function = self.__sapiens_model.infer(prompt=prompt, temperature=self.temperature, max_tokens=self.max_tokens)
				return _get_tokens(inference_function=inference_function, stream=stream, generator=True)
			elif self.__sub_architecture == 'scn':
				if self.scn_architecture in ('level_2', 'level_3'):
					if self.user_id is not None: self.__sapiens_model.user_id = self.user_id
					if self.minimum_probability_for_candidates is not None: self.__sapiens_model.minimum_probability_for_candidates = self.minimum_probability_for_candidates
					if self.min_fit_probability is not None: self.__sapiens_model.fit_probability = self.min_fit_probability
					if self.min_probability is not None: self.__sapiens_model.probability = self.min_probability
				if self.scn_architecture == 'level_1':
					inference_function = self.__sapiens_model.predict(prompt=prompt, minimum_score=self.minimum_score, hot=self.hot, stream=False)
					if len(self.end_tag.strip()) > 0 and self.end_tag in inference_function:
						parts_of_the_inference = inference_function.split(self.end_tag)
						inference_function = parts_of_the_inference[0].strip() if len(parts_of_the_inference[0].strip()) > 0 else parts_of_the_inference[-1].strip()
				else: inference_function = self.__sapiens_model.predict(prompt=prompt, max_tokens=self.max_tokens, min_fit_probability=self.min_fit_probability, min_probability=self.min_probability, generalization=self.generalization, stream=False)['answer']
				if self.scn_architecture == 'level_2': self.close()
			elif self.__sub_architecture == 'hur':
				try:
					self.__set_hurnet_parameters()
					if not self.real_time_generator:
						inference_function = self.__sapiens_model.predict(prompt=prompt, file_path=file_path, max_tokens=self.max_tokens, temperature=self.temperature, top_k=self.top_k, top_p=self.top_p, stream=stream)
						self.perplexity = self.__sapiens_model.PERPLEXITY
						return _get_tokens(inference_function=inference_function, stream=stream, generator=True)
					else: inference_function = self.__sapiens_model.predict(prompt=prompt, file_path=file_path, max_tokens=self.max_tokens, temperature=self.temperature, top_k=self.top_k, top_p=self.top_p, stream=False)
					self.perplexity = self.__sapiens_model.PERPLEXITY
				except:
					self.__sapiens_model = self.__hur(embedding_dim=self.embedding_dim, block_size=self.block_size, batch_size=self.batch_size, number_heads=self.number_heads, number_layers=self.number_layers, dropout=self.dropout, learning_rate=self.learning_rate, eval_interval=self.eval_interval, epochs=self.epochs, use_bit_net_quantization=self.use_bit_net_quantization, device=self.device)
					inference_function = self.__sapiens_model.predict(prompt=prompt, max_tokens=self.max_tokens, temperature=self.temperature, top_k=self.top_k, top_p=self.top_p, stream=False)
				try: self.perplexity = self.__sapiens_model.PERPLEXITY
				except: pass
			elif self.__sub_architecture == 'mgt':
				inference_function = self.__sapiens_model.infer(system=self.system, prompt=prompt, messages=self.messages, temperature=self.temperature, stream=False, sapiens_model_path=self.sapiens_model_path)
				if len(self.end_tag.strip()) > 0 and self.end_tag in inference_function:
					parts_of_the_inference = inference_function.split(self.end_tag)
					inference_function = parts_of_the_inference[0].strip() if len(parts_of_the_inference[0].strip()) > 0 else parts_of_the_inference[-1].strip()
			else: inference_function = self.__sapiens_model.predict(prompt=prompt, max_tokens=self.max_tokens, min_fit_probability=self.min_fit_probability, min_probability=self.min_probability, generalization=self.generalization, stream=False)['answer']
			return _get_tokens(inference_function=inference_function, stream=stream, generator=False)
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.inference: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return ''
	def completeMessages(self, messages=[], stream=False):
		try:
			complete_messages = {'answer': '', 'messages': [], 'next_token': ''}
			messages = list(messages) if type(messages) in (tuple, list, dict) else []
			stream = bool(stream) if type(stream) in (bool, int, float) else False
			complete_messages['messages'] = messages
			if messages:
				template, file_path = '', ''
				if self.__sub_architecture in ('hur', 'cpu') and len(messages) > 2:
					if self.__sub_architecture == 'cpu':
						_CPUModel__fine_tuning = self.__sapiens_model._CPUModel__fine_tuning
						if _CPUModel__fine_tuning: template = str(messages[-1].get('content', '')).strip()
					else:
						end_tag = self.end_tag if self.end_tag else ''
						for message in messages:
							role = str(message.get('role', '')).strip()
							content = str(message.get('content', '')).strip()
							if role and content: template += f'{role.capitalize()}:\n{content}{end_tag}\n'
						template = template.strip()
						if template: file_path = str(messages[-1].get('file_path', '')).strip()
				else: template = str(messages[-1].get('content', '')).strip()
				def _get_stream(template='', complete_messages={}, file_path=''):
					current_answer, message = '', {'role': 'assistant', 'content': ''}
					complete_messages['messages'].append(message)
					inference_function = self.inference(prompt=template, file_path=file_path, stream=True)
					for token in inference_function:
						current_answer += token
						complete_messages['answer'] = current_answer
						complete_messages['messages'][-1]['content'] = current_answer
						complete_messages['next_token'] = token
						yield complete_messages
				def _get_string(template='', complete_messages={}, file_path=''):
					inference_function = self.inference(prompt=template, file_path=file_path, stream=False)
					complete_messages['answer'] = inference_function
					message = {'role': 'assistant', 'content': inference_function}
					complete_messages['messages'].append(message)
					token = inference_function.split(chr(32))[-1].rstrip()
					complete_messages['next_token'] = token
					return complete_messages
				if stream: complete_messages = _get_stream(template=template, complete_messages=complete_messages, file_path=file_path)
				else: complete_messages = _get_string(template=template, complete_messages=complete_messages, file_path=file_path)
			return complete_messages
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.completeMessages: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return ''
	def printInference(self, prompt='', file_path='', stream=True):
		try:
			inference = self.inference(prompt=prompt, file_path=file_path, stream=stream)
			if stream:
				from time import sleep
				for token in inference:
					print(token, end='', flush=True)
					sleep(self.delay)
				print()
			else: print(inference)
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.printInference: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
	def printCompleteMessages(self, messages=[], stream=True):
		try:
			inference = self.completeMessages(messages=messages, stream=stream)
			if stream:
				from time import sleep
				for token in inference:
					print(token['next_token'], end='', flush=True)
					sleep(self.delay)
				print()
			else: print(inference['answer'])
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.printInference: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
	def close(self):
		try:
			if self.__sub_architecture == 'scn' and self.scn_architecture == 'level_3': self.__sapiens_model.close()
			else:
				try: del self.__sapiens_model
				except: pass
			return True
		except Exception as error:
			try:
				if self.__show_errors or self.show_error:
					error_message = 'ERROR in SapiensModel.close: '+str(error)
					print(error_message)
					try: self.__print_exc() if self.__display_error_point or self.show_error_details else None
					except: pass
			except: pass
			return False
class SapiensArchitecture(SapiensModel): pass
"""
This algorithm was designed, programmed, and developed by Sapiens Technology®️ to enable the construction, training, tuning, and inference of language models using the main architectural frameworks of Sapiens Technology®️.
The code includes a main class with the base architecture and several other internal sub-architectures that can be configured through the model's parameters.

Any changes to this code, reverse engineering, disclosure, or public commentary involving the technical aspects of the technology contained herein are strictly prohibited, and the authors will be duly prosecuted by our legal team.

WE DO NOT authorize the commercial use of this code without prior permission from Sapiens Technology®️.
"""
# --------------------------> A SAPIENS TECHNOLOGY®️ PRODUCTION) <--------------------------
