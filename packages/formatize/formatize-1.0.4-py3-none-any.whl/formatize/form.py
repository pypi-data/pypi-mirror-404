from pydantic import BaseModel, ConfigDict, create_model
from typing import List, Dict, Optional
from importlib import import_module
from bs4 import BeautifulSoup

import datetime
import hashlib
import json
import math
import re
import inspect
import string
import uuid
import yaml

import socket
import smtplib
import dns.resolver

import tkinter as tk
from PIL import Image, ImageTk

LENGTH_MD5 = 32
LENGTH_SHA256 = 64
APP_YAML = 'app.yaml'
ENCODING = 'utf-8'
ENCODINGSIG = 'utf-8-sig'
YAML_ENCODE = 'utf-8-sig'

EMPTY = ''
SPACE = ' '
DATESTRS = '-'
TIMESTRS = ':'
REGPUNCS = r'[' + string.punctuation + r']+'
REGTIMES = r'[' + SPACE + r'T]+'

ERROR = 'error'
PARAMS = 'params'

ADMIN = 'admin'
ACCOUNTING = 'accounting'

APP_PATH = 'script.app_'
DBA_PATH = 'lib.db.dbase_'

ERR_INPUT = 'Invalid input data'

## OLD LAMBDAS

def err_input (e):
  return f'{ERR_INPUT}: {e}'

def data_dict ():
  return {ERROR: None, PARAMS: {}}

def uid ():
  return str(uuid.uuid4())

def md5 (text):
  return crypto_md5(text)

def sha (text):
  return crypto_sha256(text)

def now ():
  return str(datetime.datetime.now())

def hstr (x):
  return str(x or '')

def caller ():
  return inspect.stack()[1][3]

def extract (s, sep='.'):
  return s.split(sep)

def extract_input(s: str, sep: str=',', col: str=':') -> dict: ## <1.0.4>
  try:
    args = ''.join(s.split()).split(sep)
    return {item.split(col)[0].lower(): item.split(col)[1] for item in args}
  except:
    return None

def add_zero (n, zeros=2):
  return str(n).zfill(zeros)

def sort_dict (obj):
  return dict(sorted(obj.items()))

def copy_dict (obj): ## CloneObject
  return json.loads(json.dumps(obj))

def dict_contain (obj, keys):
  return all(key in obj for key in keys)

def sum_over_list_of_floats (lst):
  return math.fsum(lst)

def sum_over_list_of_dicts (list_of_dicts, key):
  return sum(float(d[key]) for d in list_of_dicts)

def format_decimal_number (num, dec=2):
  return ('{:,.' + str(dec) + 'f}').format(float(num))

def draw_aligned_number (num, spaces=20, symb='$', dec=2):
  return ralign(form(num, dec), spaces, symb)

def right_align_text (text, spaces=20, suffix=''):
  return ('{:>' + str(spaces) + '}').format(text) + suffix

def output_keyval (object, left, right, sep='\n'):
  return sep.join([('{:<' + str(left) + '}').format(key) + ('{:>' + str(right) + '}').format(object[key]) for key in object])

fs = sum_over_list_of_floats

lds = sum_over_list_of_dicts

form = format_decimal_number

number = draw_aligned_number

ralign = right_align_text

output = output_keyval

def to_upper (text):
  return str_clean(text).upper()

def to_title (text):
  return str_clean(text).title()

def dicts (models):
  return [x.model_dump() for x in models]

def merge_dict (dict1, dict2):
  return {**dict1, **dict2}

def generate_dict (items): ## TupleList
  return {key:val for key,val in items}

def generate_json (items): ## TupleList
  return json.dumps(generate_dict(items))

def create_dict (**kwargs): ## dcore.kwarg()
  return {arg:kwargs[arg] for arg in kwargs}

def function_module2 (modules, funcname):
  return next((key for key in modules if funcname in modules[key]), None)

def function_module (modules, funcname):
  return next((key for key in app_functions(modules) if funcname in dir(modules[key])), None)

def app_functions (modules):
  return {x: [y for y in dir(modules[x]) if callable(getattr(modules[x], y)) and y.lower()==y and not y.startswith('_')] for x in modules}

def prepare_json_info (info, InfoModel, defval=None):
  return json.dumps(InfoModel(**info).model_dump()) if type(info) is dict else defval

def unpack_one_vs_many_db_values (model, mid, mvals, formatfunc=int):
  return ','.join('(' + str(formatfunc(getattr(model,mid))) + ',' + str(formatfunc(v)) + ')' for v in getattr(model, mvals))

def flatten (matrix):
  return [item for row in matrix for item in row]

def find_item (data, key, val): ## data:DictList
  return find_item_in_list_of_dict(data, key, val)

def merge_list (list1, list2):
  return merge_two_list_exclusive(list1, list2)

def check_list (list1, list2):
  return any(x in list1 for x in list2)

def unpack_list_to_tuple_str (lst):
  return f'{*lst,}'

def str_to_list (s):
  return list(map(str.strip,s.split(',')))

def adjust_array (array, count, defval, defid=0):
  return [defval]*count if type(array)!=list or not array else (array if count==len(array) else [array[defid]]+[defval]*(count-1))

def fillup_array (array, count, defval, defid=0):
  return [defval]*count if type(array)!=list or not array else (array if count==len(array) else [array[defid]]*count)

news = adjust_array

dups = fillup_array

def default (params, attr, val):
  return params.setdefault(attr, val)

def integer (val, defval=-1):
  return int(float(val)) if is_numeric(val) else defval

def boolean (val):
  return 0 if not val else 1

def setattrs (Module, attrs=[], vals={}):
  return [setattr(Module, i, vals.get(i)) for i in attrs]

def get_attr (module, attr, defval=ValueError):
  return getattr(module, attr) if attr in dir(module) else defval

def popattr (module=None, attr=None):
  return getattr(module, attr) if attr in dir(module) else None

def popfunc (val, module=None, func=str, pattern=r'\/(.*?)\/'): ## val:/something/
  return (popattr(module, m.group(1)) if (m:=re.search(pattern,str(val))) else val) or func

## BASIC FORMATTINGS

def replace_dict_placeholders(text: str, vals: dict, quot: str="'", holder: str=r'\:\S+\b') -> str:
  ## This may cause ambiguous matter in SQL STRING/NUMBER comparison
  try:
    subs = re.findall(holder, text)
    items = iter(str(e) for e in subs)
    return re.sub(holder, lambda lm: f"{quot}{vals[next(items)[1:]]}{quot}", text)
  except:
    return None

def replace_placeholders(text: str, vals: list, quot: str="'", holder: str=r'\?', formatfunc=int) -> str:
  ## This may cause ambiguous matter in SQL STRING/NUMBER comparison
  try:
    count = len(re.findall(holder, text))
    if count != len(vals): return None
    items = iter(str(formatfunc(e)) for e in vals)
    return re.sub(holder, lambda lm: f"{quot}{next(items)}{quot}", text)
  except:
    return None

def crc16(data: bytes, encoding: str='utf-8', purehex: bool=False) -> str:
  if type(data)==str: data = data.encode(encoding)
  if type(data) is not bytes: return None
  crc = 0xFFFF
  for byte in data:
    crc ^= (byte << 8)
    for _ in range(8):
      if crc & 0x8000:
        crc = (crc << 1) ^ 0x1021
      else:
        crc <<= 1
      crc &= 0xFFFF
  res = f'0x{crc:04X}'
  return res if purehex else res[2:]

def module_extract(module, path: str, defval: any=None):
  try:
    obj = module
    paths = extract(path)
    for s in paths:
      obj = getattr(obj, s)
    return obj
  except:
    return defval

def dict_assign(object: dict, path: str, value: any, add: bool=False):
  obj = object ## NoCopy
  paths = extract(path)
  for i, s in enumerate(paths):
    if i==len(paths)-1:
      obj[s] = value
    else:
      if s not in obj or type(obj[s]) != dict:
        if add:
          obj[s] = {}
        else:
          return
      obj = obj[s]

def dict_extract(object: dict, path: str, defval: any=None) -> any:
  try:
    obj = copy_dict(object)
    paths = extract(path)
    for s in paths:
      obj = obj.get(s)
    return obj
  except:
    return defval

def dict_sort(object: dict, path: str='') -> dict:
  subdict = dict_extract(object, path)
  if subdict:
    dict_assign(object, path, value=sort_dict(subdict))
  else:
    object = sort_dict(object)
  return object

def merge_dicts(err: str, *sources) -> dict:
  merged_dict = {}
  for d in sources:
    if not isinstance(d, dict): raise TypeError(err)
    merged_dict.update(d)
  return merged_dict

def find_field_in_list_of_dict(data: list, sub: dict, field: str, defval: any=None) -> any:
  return next((item.get(field) for item in data if type(item)==dict and item.get(k:=list(sub.keys())[0])==sub[k]), defval)

def find_item_in_list_of_dict(data: list, key: str, val: any) -> dict:
  return next((item for item in data if item[key]==val), None)

def select_items_from_dict(data: dict, selected_keys: list) -> dict:
  for k in selected_keys:
    if k not in data: selected_keys.remove(k)
  return {k: data[k] for k in selected_keys}

def merge_two_list_exclusive(list1: list, list2: list) -> list:
  return list(set(list(set(list2)-set(list1))+list1))

def str_is_hex(s: str) -> bool:
  hex_digits = set(string.hexdigits)
  return all(c in hex_digits for c in s)

def is_numeric(val: any, func=float) -> bool:
  try:
    func(val)
    return True
  except:
    return False

def prepare_password(params: dict, col_hpwd: str) -> bool:
  params[col_hpwd] = prepare_hash_password(params.get(col_hpwd))
  return True

def prepare_info(params: dict, col_info: str, InfoModel) -> bool:
  params[col_info] = prepare_json_info(params.get(col_info), InfoModel, params.setdefault(col_info,''))
  return True

def prepare_workinterval(model) -> bool:
  model.workbegin = parse_time(model.workbegin)
  model.workend = parse_time(model.workend)
  return True

def prepare_worktime(model) -> bool:
  model.worktime = model.worktime or now()
  model.worktime = parse_time(model.worktime)
  return True

def totime(time: any=None, defval=None) -> datetime.datetime:
  if not (time:=parse_time(time)): return defval
  return datetime.datetime.fromisoformat(time)

def parse_doc_date(time: any=None) -> str:
  if not (time:=parse_time(time)): return None ## For DATE()
  return time[:10]

def parse_date (datestr: str, dateform: str='%d/%m/%Y') -> str: ## <1.0.3>
  try:
    date = datetime.datetime.strptime(datestr, dateform)
  except:
    date = datetime.datetime.now()
  return date.strftime('%Y-%m-%d')

def parse_time(time: any=None) -> str:
  if not time:
    return None
  elif type(time) is datetime.datetime:
    return str(time)
  elif type(time) is int:
    return str(datetime.datetime.fromtimestamp(time))
  try:
    return str(datetime.datetime.fromisoformat(time))
  except Exception:
    try:
      time = str_time_clean(time)
      return str(datetime.datetime.fromisoformat(time))
    except Exception:
      return now()

def str_time_clean(text: str) -> str:
  text = re.sub(REGTIMES,SPACE,text).strip()
  part = text.split(SPACE)
  try:
    date = str_add_zero(str_clean(part[0],DATESTRS),DATESTRS)
    time = str_add_zero(str_clean(part[1],TIMESTRS),TIMESTRS)
  except IndexError:
    time = ''
  return (date+SPACE+time).strip()

def str_clean(text: str, sep: str=SPACE) -> str:
  return re.sub(REGPUNCS,sep,text).strip()

def str_add_zero(text: str, sep: str) -> str:
  try: 
    text = text.split(sep)
    part = [f"{int(x):02d}" for x in text]
    return sep.join(part)
  except Exception:
    return ''

def prepare_hash_password(given_pwd: str, default_pwd: str='123456') -> str:
  if not given_pwd:
    return text_to_password(default_pwd)
  elif len(given_pwd)==LENGTH_MD5 and str_is_hex(given_pwd):
    return crypto_sha256(given_pwd)
  elif len(given_pwd)!=LENGTH_SHA256 or not str_is_hex(given_pwd):
    return text_to_password(given_pwd)
  return given_pwd

def text_to_password(text: str) -> str:
  return crypto_sha256(crypto_md5(text))

def crypto_encode(text: str) -> (str, str):
  return crypto_sha256(text), crypto_md5(text)

def crypto_sha256(text: str) -> str:
  try:
    text_bytes = text.encode(ENCODING)
    sha256_hash = hashlib.sha256()
    sha256_hash.update(text_bytes)
    return sha256_hash.hexdigest()
  except Exception:
    return None

def crypto_md5(text: str) -> str:
  try:
    text_bytes = text.encode(ENCODING)
    md5_hash = hashlib.md5()
    md5_hash.update(text_bytes)
    return md5_hash.hexdigest()
  except Exception:
    return None

def render_html(filename: str, dtexts: dict={}, dattributes: dict={}) -> BeautifulSoup:
  soup = soup_from_template(filename)
  return render_soup(soup, dtexts, dattributes) #soup

def render_soup(soup: BeautifulSoup, dtexts: dict={}, dattributes: dict={'placeholder':{}}) -> BeautifulSoup:
  for id in dtexts:
    soup = soup_replace_value(soup, id, dtexts[id])
  for attr in dattributes:
    for id in dattributes[attr]:
      soup = soup_replace_attribute(soup, id, attr, dattributes[attr][id])
  return soup

def soup_replace_attribute(soup: BeautifulSoup, id: str, attribute: str, newvalue: str) -> BeautifulSoup:
  find = soup.find(id=id)
  if find:
    find[attribute] = newvalue
  return soup

def soup_replace_value(soup: BeautifulSoup, id: str, newvalue: str) -> BeautifulSoup:
  find = soup.find(id=id)
  if find:
    find.string.replace_with(newvalue)
  return soup

def soup_from_template(filename: str, folder: str='') -> BeautifulSoup:
  with open(f"{folder}{filename}", 'r', encoding=ENCODING) as file:
    filetext = file.read()
  return BeautifulSoup(filetext, 'html.parser')

def param_load_from_request(jsonstr: str) -> dict:
  result = data_dict()
  try:
    result[PARAMS] = json.loads(jsonstr)
    if type(result[PARAMS]) is not dict:
      result[ERROR] = ERR_INPUT
  except json.JSONDecodeError as e:
    result[ERROR] = err_input(e)
  except Exception as e:
    result[ERROR] = err_input(e)
  return result

def data_load_from_csv_file(filepath: str, ffill: bool=True, nonan: bool=True) -> dict:
  import pandas as pd
  import numpy as np
  result = data_dict()
  try:
    df = pd.read_csv(filepath)
    if ffill: df = df.fillna(method='ffill')
    if nonan: df = df.replace({np.nan: None})
    result[PARAMS] = df.to_dict(orient='records')
  except Exception as e:
    result[ERROR] = err_input(e)
  return result

def data_load_from_json_file(filepath: str) -> dict:
  result = data_dict()
  try:
    with open(filepath, encoding=ENCODINGSIG) as file:
      result[PARAMS] = json.load(file)
  except json.JSONDecodeError as e:
    result[ERROR] = err_input(e)
  except Exception as e:
    result[ERROR] = err_input(e)
  return result

def data_load_from_yaml_file(filepath: str=APP_YAML) -> dict:
  result = data_dict()
  try:
    with open(filepath, encoding=ENCODINGSIG) as file:
      result[PARAMS] = yaml.load(file, yaml.Loader)
    if type(result[PARAMS]) is not dict:
      result[ERROR] = ERR_INPUT
      result[PARAMS] = {}
  except Exception as e:
    result[ERROR] = err_input(e)
  return result

def data_dump_to_yaml_file(data: any, filepath: str, encoding=ENCODINGSIG, sort_keys=False) -> bool:
  try:
    with open(filepath, 'w', encoding=encoding) as file:
      yaml.dump(data, file, default_flow_style=False, sort_keys=sort_keys)
    return True
  except:
    return False

def data_dump_to_csv_file(listofdicts: list, filepath: str) -> bool:
  import pandas as pd
  try:
    df = pd.DataFrame(listofdicts)
    df.to_csv(filepath, index=False)
    return True
  except:
    return False

dump_csv = data_dump_to_csv_file

def jsonloads(text: str) -> dict:
  try:
    return json.loads(text)
  except:
    return None

def str_to_json(val: str) -> str:
  if type(val) in [dict, list]: return json.dumps(val)
  try:
    return json.dumps(json.loads(str(val)))
  except:
    return '{}'

def load_yaml(yamlfile: str) -> dict:
  with open(yamlfile, encoding=YAML_ENCODE) as file:
    return yaml.load(file, Loader=yaml.Loader)

def dump_yaml(data: any, yamlfile: str) -> bool:
  return data_dump_to_yaml_file(data, yamlfile, YAML_ENCODE)

def parse_model_dat(dat: dict) -> dict:
  d = {x: tuple([eval(dat[x][0]), dat[x][1]]) for x in dat}
  return d

def load_model(modelname: str, dat: dict) -> BaseModel:
  return create_model(modelname, **parse_model_dat(dat), __config__=ConfigDict(coerce_numbers_to_str=True))

def load_model_from_yaml(modelname: str, modelfile: str='model.yaml') -> BaseModel:
  try:
    models = load_yaml(modelfile)
    return load_model(modelname, models.get(modelname))
  except:
    return None

def load_models_from_yaml(modelfile: str='model.yaml') -> dict:
  dat = {}
  try:
    models = load_yaml(modelfile)
    for model in models: dat[model] = load_model(model, models[model])
  except:
    return None
  return dat

def add_models_from_yaml(Module, modelfile: str='model.yaml') -> bool:
  return update_module(Module, load_models_from_yaml(modelfile))

def prepare_model(model, BuildModel, DefModel):
  if type(model) is dict:
    return BuildModel(**model)
  elif type(model) is list:
    if issubclass(type(model[0]), BaseModel):
      model = [x.model_dump() for x in model]
    elif type(model[0]) is dict:
      model = [BuildModel(**x).model_dump() for x in model]
    return DefModel(array=model, limit=len(model))
  return model

def ext_modules(appfile: str='app.yaml') -> list:
  return data_load_from_yaml_file(appfile)[PARAMS].get('modules')

def merge_modules(source: str, targetmodule, exlist: list=[]):
  sourcemodule = import_module(source)
  for item in filter(lambda attr: attr in exlist or attr not in dir(targetmodule), dir(sourcemodule)):
    setattr(targetmodule, item, getattr(sourcemodule, item))

def load_modules(sources: list, targetmodule, path: str=APP_PATH):
  for source in sources: merge_modules(f'{path}{source}', targetmodule)

def load_ext_modules(targetmodule):
  load_modules(ext_modules(), targetmodule)

add_modules_from_yaml = load_ext_modules

def setattrs_from_yaml(Module, iofile: str='io.yaml') -> bool:
  return update_module(Module, data_load_from_yaml_file(iofile)[PARAMS])

add_consts_from_yaml = setattrs_from_yaml

def get_module(module, path=APP_PATH):
  try:
    return import_module(f'{path}{module}')
  except:
    return None

def get_modules_from_yaml(path: str=APP_PATH, appfile: str='app.yaml') -> dict:
  modules = [ADMIN, ACCOUNTING]
  params = data_load_from_yaml_file(appfile)[PARAMS]
  if params:
    mx = params.get('modules')
    if type(mx) is str: mx = list(map(str.strip, mx.split(',')))
    if type(mx) is list: modules = merge_list(modules, mx)
  try:
    return {module: get_module(module, path) for module in modules}
  except:
    return {}

def update_module(Module, vals: dict) -> bool:
  try:
    setattrs(Module, [x for x in vals], vals)
    return True
  except:
    return False

## FRONTEND FORMATTINGS

def load_yaml_temp (filepath):
  return data_load_from_yaml_file(filepath).get(PARAMS)

def load_yaml_account_temp (filename, folder='temp/yaml/account/'):
  return load_yaml_temp(f'{folder}{filename}')

def load_yaml_subaccount_temp (filename='subaccount.yaml'):
  return load_yaml_account_temp(filename).get('subaccount_data')

def load_yaml_detailaccount_temp (filename='detailaccount.yaml'):
  return load_yaml_account_temp(filename).get('detailaccount_data')

def load_csv_temp (filepath):
  return data_load_from_csv_file(filepath).get(PARAMS)

def load_csv_account_temp (filename, folder='temp/csv/account/'):
  return load_csv_temp(f'{folder}{filename}')

def load_csv_subaccount_temp (filename='subaccount.csv'):
  return load_csv_account_temp(filename)

def load_csv_detailaccount_temp (filename='detailaccount.csv'):
  return load_csv_account_temp(filename)

class Napas:
  QRORDER = 'form.method.account.currency.amount.country'

  def __init__(self, napas: dict, dcopy: dict, banks: list):
    self.napas = napas
    self.dcopy = dcopy
    self.banks = banks

  def dget(self):
    return self.dcopy

  def concat(self, path: str) -> str:
    item = dict_extract(self.dcopy, path)
    if type(item)!=dict or not dict_contain(item, extract('id.length.value')):
      raise ValueError('Invalid values assigned')
    return f"{item['id']}{item['length']}{item['value']}"

  def dset(self,
    config: str,
    bankcode: str,
    account: str,
    currency: str,
    country: str,
    amount: float=0,
    data: dict=None):
    method = dict_extract(self.napas, f'method.value.{config.lower()}')
    if not method:
      raise ValueError('Invalid initiation method')
    dict_assign(self.dcopy, 'method.value', method)
    service = dict_extract(self.napas, f'account.value.service.value.{config.lower()}')
    if not service:
      raise ValueError('Invalid service code')
    dict_assign(self.dcopy, 'account.value.service.value', service)
    bankbin = find_field_in_list_of_dict(self.banks, {'code': bankcode.upper()}, 'bin')
    if not bankbin:
      raise ValueError('Invalid bank code')
    dict_assign(self.dcopy, 'account.value.bank.value.acquirer.value', bankbin)
    if not account:
      raise ValueError('Invalid beneficiary account')
    accountlength = len(account)
    len_merchant = add_zero(accountlength)
    len_bank = add_zero(accountlength + 14)
    len_account = add_zero(accountlength + 44)
    dict_assign(self.dcopy, 'account.value.bank.value.merchant.value', account)
    dict_assign(self.dcopy, 'account.value.bank.value.merchant.length', len_merchant)
    dict_assign(self.dcopy, 'account.value.bank.length', len_bank)
    dict_assign(self.dcopy, 'account.length', len_account)
    currencycode = dict_extract(self.napas, f'currency.value.{currency.upper()}.code')
    if not currencycode:
      raise ValueError('Invalid currency code')
    dict_assign(self.dcopy, 'currency.value', currencycode)
    if float(amount)<0:
      raise ValueError('Invalid billing amount')
    amount = str(amount)
    amountlength = len(amount)
    len_amount = add_zero(amountlength)
    dict_assign(self.dcopy, 'amount.value', amount)
    dict_assign(self.dcopy, 'amount.length', len_amount)
    countrycode = dict_extract(self.napas, f'country.value.{country.upper()}.code')
    if not countrycode:
      raise ValueError('Invalid country code')
    dict_assign(self.dcopy, 'country.value', countrycode)
    guidstring = self.concat('account.value.guid')
    acquirerstring = self.concat('account.value.bank.value.acquirer')
    merchantstring = self.concat('account.value.bank.value.merchant')
    dict_assign(self.dcopy, 'account.value.bank.value', acquirerstring+merchantstring)
    bankstring = self.concat('account.value.bank')
    servicestring = self.concat('account.value.service')
    accountstring = f'{guidstring}{bankstring}{servicestring}'
    dict_assign(self.dcopy, 'account.value', accountstring)
    beforedatastring = ''
    for i in extract(self.QRORDER):
      beforedatastring += self.concat(i)
    napasdata = dict_extract(self.napas, 'data.value.id')
    if data and dict_contain(napasdata, data):
      more = ''
      for key in data:
        more += f"{napasdata[key]['code']}{add_zero(len(data[key]))}{data[key]}"
      morelength = len(more)
      dict_assign(self.dcopy, 'data.value', more)
      dict_assign(self.dcopy, 'data.length', add_zero(morelength))
      datastring = self.concat('data')
    else:
      del self.dcopy['data']
      datastring = ''
    beforecrcstring = f'{beforedatastring}{datastring}6304'
    crcstring = crc16(beforecrcstring)
    dict_assign(self.dcopy, 'crc.value', crcstring)
    return f'{beforecrcstring}{crcstring}'

  def qextract(self, qstr: str, qmodel=None, idcol='id') -> dict:
    join = lambda d: ''.join(d.values())
    take = lambda s: {'id': s[:2], 'length': s[2:4], 'value': s[4:4+int(s[2:4])]}
    section = lambda qmodel, id: next(key for key in qmodel if qmodel[key][idcol]==id)
    if qmodel is None: qmodel = self.napas
    qdata = {}
    try:
      while len(qstr)>0:
        d = take(qstr)
        qdata[section(qmodel, d['id'])] = d
        qstr = qstr[len(join(d)):]
      return {'error': None, 'result': qdata}
    except Exception as e:
      return {'error': f'IOError: {e}', 'result': None}

  def qextract2(self, qstr: str) -> dict:
    qext = self.qextract(qstr)
    if qext['error']: return qext
    qdata = qext['result']
    try:
      qaccount = qdata['account']
      account = self.qextract(qaccount['value'], dict_extract(self.napas, 'account.value'))['result']
      bank = self.qextract(dict_extract(account, 'bank.value'), dict_extract(self.napas, 'account.value.bank.value'))['result']
      service = account['service']
      guid = account['guid']
      qdata['account']['value'] = {'guid': guid, 'bank': bank, 'service': service}
      dataval = dict_extract(qdata, 'data.value')
      if dataval: qdata['data']['value'] = self.qextract(dataval, dict_extract(self.napas, 'data.value.id'), idcol='code')['result']
      return {'error': None, 'result': qdata}
    except Exception as e:
      return {'error': f'IOError: {e}', 'result': None}

  write = dset
  read = qextract2

def mailvalid(address: str) -> bool:
  records = dns.resolver.resolve('gmail.com', 'MX')
  mxRecord = records[0].exchange
  mxRecord = str(mxRecord)
  host = socket.gethostname()
  server = smtplib.SMTP()
  server.set_debuglevel(0)
  server.connect(mxRecord)
  server.helo(host)
  server.mail('me@domain.com')
  code, message = server.rcpt(str(address))
  server.quit()
  return True if code==250 else False

def print_qrcode(data: str, path: str) -> bool:
  import qrcode
  try:
    img = qrcode.make(data)
    img.save(f'{path}.png')
    return True
  except:
    return False

def popup_image(filepath, title: str='Image Popup', errfile: str='File not found or bad', errload: str='Error loading file'):
  popup = tk.Toplevel()
  popup.title(title)
  try:
    img = Image.open(filepath)
    tkimg = ImageTk.PhotoImage(img)
    label = tk.Label(popup, image=tkimg)
    label.image = tkimg
    label.pack()
  except FileNotFoundError:
    label = tk.Label(popup, text=f'FileError: {errfile}')
    label.pack()
  except Exception as e:
    label = tk.Label(popup, text=f'LoadError: {errload}: {e}')
    label.pack()

def window_image(filepath: str, title: str='Image Window'):
  root = tk.Tk()
  root.title(title)
  tkimg = ImageTk.PhotoImage(Image.open(filepath))
  label = tk.Label(root, image=tkimg)
  label.pack()
  root.mainloop()
