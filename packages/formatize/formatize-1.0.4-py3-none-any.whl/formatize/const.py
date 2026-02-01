from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated
from typing import List, Dict, Optional

integer = lambda val: int(val) if str(val).isnumeric() else -1

nums_to_str = ConfigDict(coerce_numbers_to_str=True, extra='ignore')
int_or_none = Annotated[int, BeforeValidator(lambda x: integer(x))]
str_or_none = Annotated[str, BeforeValidator(lambda x: x or '')]

class DbItemRow(BaseModel):
  sub: int_or_none=None
  ref: int_or_none=None
  uuid: Optional[str]=None
  head: Optional[str]=None
  info: Optional[str]=None
  note: Optional[str]=None
  dated: Optional[str]=None
  creator: int_or_none=None
  active: bool=True
  model_config = nums_to_str

class DbTxRow(BaseModel):
  uuid: Optional[str]=None
  tx: Optional[str]=None
  info: Optional[str]=None
  note: Optional[str]=None
  dated: Optional[str]=None
  ref: int_or_none=None
  account: int_or_none=None
  sub: int_or_none=None
  item: int_or_none=None
  debit: float=0
  credit: float=0
  creator: int_or_none=None
  model_config = nums_to_str

class DbTxs(BaseModel):
  uuid: Optional[str]=None
  dated: Optional[str]=None
  creator: int_or_none=None
  data: List[DbTxRow]=[DbTxRow()]
  model_config = nums_to_str

class DbTx(BaseModel):
  id: int_or_none=None
  uuid: Optional[str]=None
  tx: Optional[str]=None
  info: Optional[str]=None
  note: Optional[str]=None
  dated: Optional[str]=None
  datedfrom: Optional[str]=None
  datedto: Optional[str]=None
  ref: int_or_none=None
  refcode: Optional[str]=None
  account: int_or_none=None
  accountcode: Optional[str]=None
  sub: int_or_none=None
  subcode: Optional[str]=None
  item: int_or_none=None
  itemuuid: Optional[str]=None
  debit: float=0
  credit: float=0
  created: Optional[str]=None
  createdfrom: Optional[str]=None
  createdto: Optional[str]=None
  creator: int_or_none=None
  modified: Optional[str]=None
  modifier: int_or_none=None
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class DbItem(BaseModel):
  id: int_or_none=None
  uuid: Optional[str]=None
  sub: int_or_none=None
  subcode: Optional[str]=None
  account: int_or_none=None
  accountcode: Optional[str]=None
  ref: int_or_none=None
  refcode: Optional[str]=None
  head: Optional[str]=None
  info: Optional[str]=None
  note: Optional[str]=None
  dated: Optional[str]=None
  datedfrom: Optional[str]=None
  datedto: Optional[str]=None
  created: Optional[str]=None
  createdfrom: Optional[str]=None
  createdto: Optional[str]=None
  modified: Optional[str]=None
  creator: int_or_none=None
  modifier: int_or_none=None
  active: bool=True
  cancel: bool=False
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class DbItems(BaseModel):
  modifier: int_or_none=None
  active: bool=True
  cancel: bool=False
  ids: list=[]
  uuids: list=[]
  model_config = nums_to_str

class DbSub(BaseModel):
  id: int_or_none=None
  name: Optional[str]=None
  account: int_or_none=None
  accountcode: Optional[str]=None
  code: Optional[str]=None
  info: Optional[str]=None
  note: Optional[str]=None
  created: Optional[str]=None
  createdfrom: Optional[str]=None
  createdto: Optional[str]=None
  modified: Optional[str]=None
  creator: int_or_none=None
  modifier: int_or_none=None
  active: bool=True
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class DbAccount(BaseModel):
  id: int_or_none=None
  name: Optional[str]=None
  root: int_or_none=None
  rootcode: Optional[str]=None
  code: Optional[str]=None
  note: Optional[str]=None
  created: Optional[str]=None
  active: bool=True
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class DbRoot(BaseModel):
  id: int_or_none=None
  name: Optional[str]=None
  grup: int_or_none=None
  grupcode: Optional[str]=None
  code: Optional[str]=None
  note: Optional[str]=None
  created: Optional[str]=None
  active: bool=True
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class DbGroup(BaseModel):
  id: int_or_none=None
  name: Optional[str]=None
  code: Optional[str]=None
  note: Optional[str]=None
  created: Optional[str]=None
  active: bool=True
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class DbUserrole(BaseModel):
  name: Optional[str]=None
  user: int_or_none=None
  role: int_or_none=None
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class DbUserroles(BaseModel):
  name: Optional[str]=None
  user: int_or_none=None
  roles: list=[]
  model_config = nums_to_str

class DbUserspec(BaseModel):
  name: Optional[str]=None
  user: int_or_none=None
  spec: int_or_none=None
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class DbUserspecs(BaseModel):
  name: Optional[str]=None
  user: int_or_none=None
  specs: list=[]
  model_config = nums_to_str

class DbSpecrole(BaseModel):
  spec: int_or_none=None
  role: int_or_none=None
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class DbSpecroles(BaseModel):
  spec: int_or_none=None
  roles: list=[]
  model_config = nums_to_str

class DbSpec(BaseModel):
  id: int_or_none=None
  name: Optional[str]=None
  note: Optional[str]=None
  created: Optional[str]=None
  active: bool=True
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class DbRole(BaseModel):
  id: int_or_none=None
  name: Optional[str]=None
  note: Optional[str]=None
  created: Optional[str]=None
  active: bool=True
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class DbUser(BaseModel):
  id: int_or_none=None
  name: Optional[str]=None
  zone: int_or_none=None
  zoneidn: Optional[str]=None
  useridn: Optional[str]=None
  conuser: Optional[str]=None
  hpwd: Optional[str]=None
  mail: Optional[str]=None
  info: Optional[str]=None
  note: Optional[str]=None
  created: Optional[str]=None
  modified: Optional[str]=None
  creator: Optional[int]=1
  modifier: int_or_none=None
  workbegin: Optional[str]=None
  workend: Optional[str]=None
  active: bool=False
  zadmin: bool=False
  worktime: Optional[str]=None
  newpass: Optional[str]=None
  oldpass: Optional[str]=None
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class DbZone(BaseModel):
  id: int_or_none=None
  name: Optional[str]=None
  zoneidn: Optional[str]=None
  useridn: Optional[str]=None
  info: Optional[str]=None
  note: Optional[str]=None
  created: Optional[str]=None
  modified: Optional[str]=None
  creator: int=1
  modifier: int_or_none=None
  active: bool=False
  offset: int=0
  limit: int=20
  model_config = nums_to_str

class Token(BaseModel):
  user: Optional[str]=None
  id: int_or_none=None
  zone: int_or_none=None
  zadmin: bool=False
  access_token: Optional[str]=None
  token_type: Optional[str]=None
  model_config = nums_to_str

class User(BaseModel):
  id: int_or_none=None
  name: Optional[str]=None
  zone: int_or_none=None
  mail: Optional[str]=None
  zadmin: bool=False
  active: bool=False
  found: bool=False
  zoneidn: Optional[str]=None
  useridn: Optional[str]=None
  conuser: Optional[str]=None
  model_config = nums_to_str

token_crypto_algorithm = 'HS256'
token_expire_minutes = 30

host_for_admin = '0.0.0.0'
host_for_api = '0.0.0.0'

port_for_admin = 900
port_for_api = 911
port_http = 80
port_httpa = 8080
port_https = 443

port_allowed = 65535
client_port_not_allowed = lambda port: (port:=int(port)) in [port_for_admin,port_for_api] or port>port_allowed or port<0

cors_base_url = 'http://localhost'
local_common_url = 'http://localhost'
local_secure_url = 'https://localhost'

cors_allowed_origins = lambda baseurl=cors_base_url: [
  f"{local_common_url}",
  f"{local_secure_url}",
  f"{baseurl}:{port_for_api}",
  f"{baseurl}:{port_for_admin}",
  f"{baseurl}:{port_http}",
  f"{baseurl}:{port_httpa}",
  f"{baseurl}:{port_https}",
]
