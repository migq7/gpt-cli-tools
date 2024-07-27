#!/home/yutongwu/miniconda3/envs/openai/bin/python
import openai
import yaml
import json
import inquirer
from contextlib import contextmanager
import pickle
from datetime import datetime
import pytz
import curses
import sys
import select
import os
import copy
import hashlib
import tempfile
import subprocess

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.color import Color
from rich.pager import Pager
from rich.padding import Padding
from rich.align import Align
from wcwidth import wcwidth

class BasicGPT:
    role = {
        'user': 'user',
        'system': 'system',
        'assistant': 'assistant'
    }

    def __init__(self, cfg_path=''):
        # model condfiguration
        self._api_key = ''
        self._model = ''
        self._temperature = 0.8

        # net configuration
        self._proxy = ''

        # app info
        self._app_name = 'base'
        self._dialogs = []

        self._load_cfg(cfg_path)


    def _load_cfg(self, cfg_path='') -> int:
        if cfg_path == '':
            cfg_path = os.path.join(os.path.expanduser('~'), '.config', 'askgpt', 'config.yaml')

        # check cfg_path exist
        if not os.path.exists(cfg_path):
            raise Exception("[warning] config.yaml not found, failed to init GPT app")
            return -1

        with open(cfg_path, 'r') as yaml_file:
            cfg_content = yaml.safe_load(yaml_file)

        model_cfg = cfg_content.get('model', None)
        net_cfg = cfg_content.get('net', None)

        if model_cfg is not None:
            self._api_key = model_cfg.get('api_key', '')
            self._model = model_cfg.get('model', 'gpt-4o-mini')
            self._temperature = model_cfg.get('temperature', 0.8)
            if len(self._dialogs) == 0:
                system_prompts = model_cfg.get('system_prompt', [])
                for p in system_prompts:
                    self.add_system_prompt(p)

        if net_cfg is not None:
            self._proxy = net_cfg.get('proxy', None)

        return 0

    def add_system_prompt(self, msg):
        self._log_dialog(self.role['system'], msg)

    def _log_dialog(self, role, msg):
        self._dialogs.append({'role': role, 'content': msg})

    def dump_dialogs(self):
        return copy.deepcopy(self._dialogs)

    def load_dialogs(self, dialog):
        self._dialogs = copy.deepcopy(dialog)

    def clear_dialogs(self):
        self._dialogs = []

    def set_parameter(self, attr, value):
        if attr == 'temperature':
            self._temperature = value
        elif attr == 'model':
            self._model = value
        elif attr == 'proxy':
            self._proxy = value


    def _ask_gpt(self, stream: bool = False):
        assert self._api_key, '[error] no valid api_key'
        openai.api_key = self._api_key

        try:
            response = openai.ChatCompletion.create(
                model=self._model, messages=self._dialogs,
                temperature=self._temperature, stream=stream
            )
        except openai.error.RateLimitError as reason:
            now = datetime.datetime.now(pytz.timezone("Asia/Shanghai"))
            print(f"[[ {now.strftime('%H:%M:%S')} @system ]]\nLimitation has been reached. Take a break and try again later.\n\n")
            return

        return response

    def _r_piece(self, response):
        for chunk in response:
            try:
                rtxt = chunk.choices[0].delta.content
                rtxt = rtxt.split('\n')
                for idx in range(len(rtxt) - 1):
                    rtxt[idx] += '\n'
            except:
                rtxt = ['\n']

            for piece in rtxt:
                yield piece

    @contextmanager
    def _proxy_on(self):
        ori_http_proxy = os.environ.get('http_proxy')
        ori_https_proxy = os.environ.get('https_proxy')

        os.environ['http_proxy'] = self._proxy
        os.environ['https_proxy'] = self._proxy

        try:
            yield
        finally:
            if ori_http_proxy is None:
                del os.environ['http_proxy']
            else:
                os.environ['http_proxy'] = ori_http_proxy

            if ori_https_proxy is None:
                del os.environ['https_proxy']
            else:
                os.environ['https_proxy'] = ori_https_proxy


class AskGPT(BasicGPT):
    def __init__(self, cfg_path=''):
        super().__init__(cfg_path)

        # app params
        self._app_name = 'askGPT'
        self._ui_color = 'cyan'
        self._max_width = 120
        self._tz = pytz.timezone("Asia/Shanghai")

        self._width = min(self._max_width, Console().size.width)

        # init console objects
        self._console = Console(width=self._width)

    def _put_prompt(self, str):
        title = self._app_name + ' | ' + self._model
        self._console.print(
            Panel(str, title=title, title_align="left", border_style=self._ui_color)
        )

    def _put_timeinfo(self):
        now = datetime.now(self._tz)
        formatted_date_time = Text(now.strftime("%Y %B %d - %I:%M %p"), style=self._ui_color)
        self._console.rule(formatted_date_time, style=self._ui_color)

    @staticmethod
    def _get_text_width(text):
        width = sum(wcwidth(char) for char in text)
        return width

    def _handle_response(self, response, silent=False):
        r_all = ''
        w_pos = 0

        for piece in self._r_piece(response):
            r_all += piece
            if silent:
                continue

            if w_pos + self._get_text_width(piece) > self._width:
                self._console.print('\n' + piece.lstrip(' '), end='')
                w_pos = self._get_text_width(piece.lstrip(' '))
            else:
                self._console.print(piece, end='')
                w_pos += self._get_text_width(piece)

            if '\n' in piece:
                w_pos = 0

        return r_all

    def talk(self, msg, silent=False):
        if not silent:
            self._put_prompt(msg)

        self._log_dialog(self.role['user'], msg)
        with self._proxy_on():
            r = self._ask_gpt(stream=True)
            r_all = self._handle_response(r, silent)
        self._log_dialog(self.role['assistant'], r_all)

        if not silent:
            self._put_timeinfo()

        return r_all


class RecordGPT:
    def __init__(self, cfg_path=''):
        self._share_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'askgpt')
        self._records_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'askgpt', 'records')
        self._dialog_list_path = os.path.join(self._share_path, 'dialog_list.json')

        self._dialog_list = []
        self._max_record_num = 10

        self._reload_dialog_list()
        self._load_cfg()


    def _load_cfg(self, cfg_path='') -> int:
        if cfg_path == '':
            cfg_path = os.path.join(os.path.expanduser('~'), '.config', 'askgpt', 'config.yaml')

        # check cfg_path exist
        if not os.path.exists(cfg_path):
            raise Exception("[warning] config.yaml not found, failed to init GPT app")
            return -1

        with open(cfg_path, 'r') as yaml_file:
            cfg_content = yaml.safe_load(yaml_file)

        record_cfg = cfg_content.get('record', None)

        if record_cfg is not None:
            self._max_record_num = record_cfg.get('max', 10)

        return 0


    def _save_dialog_list(self):
        if not os.path.exists(self._share_path):
            os.makedirs(self._share_path)

        if not os.path.exists(self._records_path):
            os.makedirs(self._records_path)

        # update dialog_list.json
        with open(self._dialog_list_path, 'w') as f:
            json.dump(self._dialog_list, f, ensure_ascii=False, indent=4)


    def _reload_dialog_list(self):
        if not os.path.exists(self._share_path):
            os.makedirs(self._share_path)

        if not os.path.exists(self._records_path):
            os.makedirs(self._records_path)

        if not os.path.exists(self._dialog_list_path):
            with open(self._dialog_list_path, 'w') as f:
                f.write('[]')

        with open(self._dialog_list_path, 'r') as f:
            dialog_list = json.load(f)

        self._dialog_list = dialog_list


    def _save_dialog(self, filename, dialog):
        with open(os.path.join(self._records_path, filename), 'wb') as f:
            pickle.dump(dialog, f)


    def top(self):
        if len(self._dialog_list) == 0 or self._dialog_list[0]['filename'] == '':
            return None

        filename = self._dialog_list[0]['filename']
        with open(os.path.join(self._records_path, filename), 'rb') as f:
            dialog = pickle.load(f)

        return dialog


    def update_top(self, dialog):
        if len(self._dialog_list) == 0:
            self.push_blank()

        if self._dialog_list[0]['filename'] == '':
            filename = str(hashlib.sha256(str(dialog).encode('utf-8')).hexdigest())[:10]
            while os.path.exists(os.path.join(self._records_path, filename)):
                filename += '_'
            summary = summarize_dialog(dialog)

            self._dialog_list[0]['filename'] = filename
            self._dialog_list[0]['summary'] = summary

            self._save_dialog_list()
        else:
            filename = self._dialog_list[0]['filename']

        self._save_dialog(filename, dialog)


    def push_blank(self):
        if len(self._dialog_list) and self._dialog_list[0]['filename'] == '':
            return

        rec = {
            'filename': '',
            'summary': ''
        }

        self._dialog_list.insert(0, rec)
        self._save_dialog_list()

        if len(self._dialog_list) > self._max_record_num:
            for idx in range(len(self._dialog_list) - 1, self._max_record_num - 1, -1):
                self.remove(idx)


    def remove(self, record_idx):
        if record_idx >= len(self._dialog_list):
            return

        filename = self._dialog_list[record_idx]['filename']
        try:
            os.remove(os.path.join(self._records_path, filename))
        except:
            print(f'[warning] failed to remove {filename}')

        self._dialog_list.pop(record_idx)
        self._save_dialog_list()


    def remove_all(self):
        for _ in range(len(self._dialog_list)):
            self.remove(0)


    def pick(self, idx):
        if idx >= len(self._dialog_list):
            return

        new_list = [self._dialog_list[idx]]
        self._dialog_list.pop(idx)

        for item in self._dialog_list:
            if item['filename'] != '':
                new_list.append(item)

        self._dialog_list = new_list
        self._save_dialog_list()


    def list_iter(self):
        for r in self._dialog_list:
            yield r['summary']



@contextmanager
def gpt_open_new(cfg_path=''):
    app = AskGPT(cfg_path)
    record = RecordGPT(cfg_path)

    record.push_blank()

    try:
        yield app
    finally:
        dialog = app.dump_dialogs()
        record.update_top(dialog)


@contextmanager
def gpt_open_top(cfg_path=''):
    app = AskGPT(cfg_path)
    record = RecordGPT(cfg_path)

    dialog = record.top()
    if not dialog is None:
        app.load_dialogs(dialog)

    try:
        yield app
    finally:
        dialog = app.dump_dialogs()
        record.update_top(dialog)


def summarize_dialog(dialogs):
    summary = AskGPT()
    log = [line for line in dialogs if line['role'] != 'system']
    if len(log) > 2:
        log = log[:2]

    summary.set_parameter('temperature', 0.0)
    summary.set_parameter('model', 'gpt-4o-mini')
    summary.clear_dialogs()

    summary.add_system_prompt('Summarize the theme of the text.')
    summary.add_system_prompt('The shorter, the better.')
    summary.add_system_prompt('Within 10 words.')
    summary.add_system_prompt('Avoid using any punctuation as much as possible while ensuring fluency.')

    return summary.talk(str(log), silent=True).strip()


def get_prompt_from_editor(editor_bin='vim', prompt=''):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        if len(prompt) > 0:
            temp_file.write(prompt.encode('utf-8'))
        temp_file_path = temp_file.name

    process = subprocess.call([editor_bin, temp_file_path], stdin=open('/dev/tty'))

    with open(temp_file_path, 'r') as f:
        input_str = f.read().strip()

    os.remove(temp_file_path)

    return input_str

def get_editor_path(cfg_path=''):
    if cfg_path == '':
        cfg_path = os.path.join(os.path.expanduser('~'), '.config', 'askgpt', 'config.yaml')

    # check cfg_path exist
    if not os.path.exists(cfg_path):
        raise Exception("[warning] config.yaml not found, failed to init GPT app")

    with open(cfg_path, 'r') as yaml_file:
        cfg_content = yaml.safe_load(yaml_file)

    interface_cfg = cfg_content.get('interface', None)

    editor_bin = 'nano'
    if interface_cfg is not None:
        editor_bin = interface_cfg.get('editor', 'nano')
    
    return editor_bin


if __name__ == "__main__":
    app = AskGPT()
    # app.add_system_prompt('all in chinese please')
    app.talk('给我介绍一下 rust 语言')
    talks = app.dump_dialogs()
    # print(talks)
