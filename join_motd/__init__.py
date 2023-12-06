import collections
import json
import os
from datetime import datetime
from typing import List, Optional, Callable, Any, Union, Dict

from mcdreforged.api.all import *


class ServerInfo(Serializable):
	name: str
	description: Optional[str] = None
	category: str = ''

	@classmethod
	def from_object(cls, obj) -> 'ServerInfo':
		if isinstance(obj, cls):
			return obj
		return ServerInfo(name=str(obj))

class WebInfo(Serializable):
	name: str
	URL: str = ''
	description: Optional[str] = None

class Config(Serializable):
	serverName: str = 'Survival Server'
	mainServerName: str = 'My Server'
	serverList: List[Union[str, ServerInfo]] = [
		'survival',
		'lobby',
		ServerInfo(name='creative1', description='CMP Server#1', category='CMP'),
		ServerInfo(name='creative2', description='CMP Server#2', category='CMP')
	]
	start_day: Optional[str] = None
	daycount_plugin_ids: List[str] = [
		'mcd_daycount',
		'day_count_reforged',
		'daycount_nbt'
	]
	webList: List[WebInfo] = [
		WebInfo(name='MCDR文档', description='点击前往MCDR文档！', URL='https://mcdreforged.readthedocs.io/zh_CN/latest/')
	]
	announcements: List[str] = [
		'§b在游玩复读世界的时候，请不要忘了阅读与更新复读百科哦~也请遵守复读公约的规定~§r',
		'{\"text\":\"在游玩复读世界的时候，请不要忘了阅读与更新复读百科哦~也请遵守复读公约的规定~\", \"color\":\"blue\"}'
		'[{\"text\":\"在游玩复读世界的时候，请不要忘了阅读与更新复读百科哦~也请遵守复读公约的规定~\", \"color\":\"blue\"}, {\"text\":\" 在游玩复读世界的时候，请不要忘了阅读与更新复读百科哦~也请遵守复读公约的规定~\", \"color\":\"blue\"}]'
	]


Prefix = '!!joinMOTD'
config: Config
ConfigFilePath = os.path.join('config', 'joinMOTD.json')

def to_message_text(message: str) -> Union[str, RTextBase]:
	try:
		json_object = json.loads(message)
	except ValueError:
		return message
	if type(json_object) is list:
		messages = []
		for object in json_object:
			messages.append(RTextBase.from_json_object(object))
		return RTextBase.join(' ', messages)
	else:
		return RTextBase.from_json_object(json_object)

def get_day(server: ServerInterface) -> str:
	try:
		startday = datetime.strptime(config.start_day, '%Y-%m-%d')
		now = datetime.now()
		output = now - startday
		return str(output.days)
	except:
		pass
	for pid in config.daycount_plugin_ids:
		api = server.get_plugin_instance(pid)
		if hasattr(api, 'getday') and callable(api.getday):
			return api.getday()
	try:
		import daycount
		return daycount.getday()
	except:
		return '?'


def display_motd(server: ServerInterface, reply: Callable[[Union[str, RTextBase]], Any]):
	reply('')
	reply('§7=======§r 欢迎回到 §e{}§7 =======§r'.format(config.serverName))
	reply('今天是§e{}§r开服的第§e{}§r天~'.format(config.mainServerName, get_day(server)))
	reply('§7-------§r 服务器列表 §7-------§r')

	server_dict: Dict[str, List[ServerInfo]] = collections.defaultdict(list)
	for entry in config.serverList:
		serverinfo = ServerInfo.from_object(entry)
		server_dict[serverinfo.category].append(serverinfo)
	for category, server_list in server_dict.items():
		header = RText('{}: '.format(category) if len(category) > 0 else '')
		messages = []
		for info in server_list:
			command = '/server {}'.format(info.name)
			hover_text = command
			if info.description is not None:
				hover_text = info.description + '\n' + hover_text
			messages.append(RText('[{}]'.format(info.name.upper()), color=RColor.light_purple).h(hover_text).c(RAction.run_command, command))
		reply(header + RTextBase.join(' ', messages))

	reply('')

	reply('§7-------§r 相关链接 §7-------§r')

	messages = []
	for info in config.webList:
		if info.description is not None:		
			hover_text = info.description
		else:
			hover_text = info.URL
		messages.append(RText('[{}]'.format(info.name), color=RColor.light_purple).h(hover_text).c(RAction.open_url, info.URL))
	reply(RTextBase.join(' ', messages))		

	for announment in config.announcements:
		reply(to_message_text(announment))
	
def on_player_joined(server: ServerInterface, player, info):
	display_motd(server, lambda msg: server.tell(player, msg))


def on_load(server: PluginServerInterface, old):
	global config
	config = server.load_config_simple(file_name=ConfigFilePath, in_data_folder=False, target_class=Config)
	server.register_help_message(Prefix, '显示欢迎消息')
	server.register_command(Literal(Prefix).runs(lambda src: display_motd(src.get_server(), src.reply)))
