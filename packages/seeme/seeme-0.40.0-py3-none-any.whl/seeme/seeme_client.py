import os
import json
import requests
#import httpx as requests
import zipfile
from requests_toolbelt.multipart.encoder import MultipartEncoder
import random
from dotenv import dotenv_values
from .types import *
from typing import List, Union
from pydantic import TypeAdapter
from .helpers import *

import pandas as pd

REGISTER_ENDPOINT = 'register'
USERS_ENDPOINT = 'users'
LOGIN_ENDPOINT = 'login'
MODELS_ENDPOINT = 'models'
TRAINING_REQUESTS_ENDPOINT = 'trainingrequests'
JOBS_ENDPOINT = 'jobs'
INFERENCE_ENDPOINT = 'inferences'
DATASETS_ENDPOINT = 'datasets'
VERSIONS_ENDPOINT = 'versions'
LABELS_ENDPOINT = 'labels'
SPLITS_ENDPOINT = 'splits'
ITEMS_ENDPOINT = 'items'
ANNOTATIONS_ENDPOINT = 'annotations'
SHARES_ENDPOINT = 'share'
APPLICATIONS_ENDPOINT = 'applications'
ADD_INFERENCES_ENDPOINT = 'add_inferences'
WORKFLOWS_ENDPOINT = 'workflows'
NODES_ENDPOINT = 'nodes'
EDGES_ENDPOINT = 'edges'
POST_PROCESSORS_ENDPOINT = 'post-processors'
EXECUTIONS_ENDPOINT = 'executions'
GRAPHS_ENDPOINT = 'graphs'
ORGANIZATIONS_ENDPOINT = 'organizations'
PROJECTS_ENDPOINT = 'projects'
TEAMS_ENDPOINT = 'teams'
ROLES_ENDPOINT = 'roles'
PERMISSIONS_ENDPOINT = 'permissions'
MEMBERS_ENDPOINT = 'members'
RESOURCES_ENDPOINT = 'resources'
LOGO_ENDPOINT = 'logo'
ME_ENDPOINT = 'me'

SUPPORTED_DOWNLOAD_EXTENSIONS = [ "pkl", "mlmodel", "tflite", "onnx", "onnx_int8", "names", "labels", "weights", "cfg", "conversion_cfg" ]

# --- ENV Constants

SEEME_APIKEY = "SEEME_API_KEY"
SEEME_USERNAME = "SEEME_USERNAME"
SEEME_BACKEND = "SEEME_BACKEND"

class Client():
  """ 
  Client class to interact with the SeeMe.ai backend, allowing you to manage models, datasets, predictions and training requests.
  
  Parameters:
  ---
  
  username (optional) : the username for the account you want to use;
  apikey (optional) : the API key for the username you want user;
  backend (prefilled): the backend the client communicates with.

  Note: 
  username and apikey are optional but they need to used together in order to be authenticated. Authentication will be used on subsequent requests.
  Alternatively, you can use the login method (see below)
  """
  def __init__(self, username:str=None, apikey:str=None, backend:str=None, env_file:str=".env"):
    self.headers = {}
    self.username = None
    self.apikey = None
    self.backend = None

    config = dotenv_values(env_file)
 
    env_apikey = config.get(SEEME_APIKEY)
    env_username = config.get(SEEME_USERNAME)
    env_backend = config.get(SEEME_BACKEND)

    if env_username is not None and env_apikey is not None:
      self.username = env_username
      self.update_auth_header(env_username, env_apikey)
      self.backend = env_backend

    if username is not None and apikey is not None:
      self.username = username
      self.update_auth_header(username, apikey)

    if env_backend is None:
      self.backend = "https://api.seeme.ai/api/v1/"

    if backend is not None:
      if not backend.endswith("/"):
        backend = backend + "/"
      self.backend = backend
      
    self.endpoints = {
      REGISTER_ENDPOINT: self.crud_endpoint(REGISTER_ENDPOINT),
      LOGIN_ENDPOINT: self.crud_endpoint(LOGIN_ENDPOINT),
      MODELS_ENDPOINT: self.crud_endpoint(MODELS_ENDPOINT),
      TRAINING_REQUESTS_ENDPOINT: self.crud_endpoint(TRAINING_REQUESTS_ENDPOINT),
      JOBS_ENDPOINT: self.crud_endpoint(JOBS_ENDPOINT),
      INFERENCE_ENDPOINT: self.crud_endpoint(INFERENCE_ENDPOINT),
      DATASETS_ENDPOINT: self.crud_endpoint(DATASETS_ENDPOINT),
      APPLICATIONS_ENDPOINT: self.crud_endpoint(APPLICATIONS_ENDPOINT),
      USERS_ENDPOINT: self.crud_endpoint(USERS_ENDPOINT),
      WORKFLOWS_ENDPOINT: self.crud_endpoint(WORKFLOWS_ENDPOINT),
      GRAPHS_ENDPOINT: self.crud_endpoint(GRAPHS_ENDPOINT),
      ORGANIZATIONS_ENDPOINT: self.crud_endpoint(ORGANIZATIONS_ENDPOINT),
      PROJECTS_ENDPOINT: self.crud_endpoint(PROJECTS_ENDPOINT),
      TEAMS_ENDPOINT: self.crud_endpoint(TEAMS_ENDPOINT),
      ROLES_ENDPOINT: self.crud_endpoint(ROLES_ENDPOINT),
      PERMISSIONS_ENDPOINT: self.crud_endpoint(PERMISSIONS_ENDPOINT),
      ME_ENDPOINT: self.crud_endpoint(ME_ENDPOINT),
    }
    self.applications = [Application]
    self.supported_dataset_export_formats = [ DatasetFormat.FOLDERS, DatasetFormat.YOLO, DatasetFormat.CSV, DatasetFormat.SPACY_NER ]
    self.supported_dataset_import_formats = [  DatasetFormat.FOLDERS, DatasetFormat.YOLO, DatasetFormat.CSV, DatasetFormat.SPACY_NER ]

    if self.is_logged_in():
      self.applications = self.get_applications()

  # -- Login / Registration --

  def register(self, username:str, email:str, password:str, firstname:str, name:str) -> User:
    """  
    Register a new user with a username, email and password. 
    
    Optionally, you can add a first and last name.
    """
    register_api = self.endpoints[REGISTER_ENDPOINT]

    register_data = Registration(
      username=username, 
      email=email, 
      name=name, 
      firstname=firstname, 
      password=password
    )

    r = requests.post(register_api, data=json.dumps(register_data.model_dump()), headers=self.headers)
 
    registered_user = r.json()

    if "message" in registered_user:
      raise ValueError(registered_user["message"])
    
    return User(**registered_user)

  def login(self, username:str, password:str) -> LoginReply:
    """ 
    Log in with a username and password.
    
    The username and password will be used to get the API key from the backend. 
    The method will fail if the user is not known, the password is incorrect, or the service cannot be reached.
    """
    login_api = self.endpoints[LOGIN_ENDPOINT]

    login_data = Credentials(username=username, password=password)
    
    logged_in = self.api_post(login_api, login_data)

    logged_in = LoginReply(**logged_in)

    username = logged_in.username
    apikey = logged_in.apikey

    user_id = logged_in.id

    self.update_auth_header(username, apikey)
    self.username = username
    self.user_id = user_id

    self.applications =  self.get_applications()

    return logged_in
      
  def logout(self):
    """ Log out the current user."""
    self.update_auth_header(None, None)

  def get_application_id(self, base_framework:str, framework:str, base_framework_version:str, framework_version, application:ApplicationType) -> str:
    """ Returns the application_id for the application you want to deploy:
    
    Parameters
    ---

    base_framework: the base_framework for the application (e.g. "pytorch", ...)
    base_framework_version: the version of the base_framework (e.g. "1.9.0", ...)
    framework: the framework for the application (e.g. "fastai", ...)
    framework_version: the version of the framework (e.g. "2.5.2", ...)
    application: the type of application you want to deply (e.g. "image_classification", "object_detection", "text_classification", "structured")

    Note
    ---

    To get a list of all the supported applications, see the "get_applications" method.
    """
    if len(self.applications) == 0:
      self.applications = self.get_applications()

    for f in self.applications:
      if f.base_framework == base_framework \
        and f.framework == framework \
        and f.base_framework_version == base_framework_version \
        and f.framework_version == framework_version \
        and f.application == application:
          return f.id
    
    for f in self.applications:
      if f.base_framework == base_framework \
        and f.framework == framework \
        and f.base_framework_version in base_framework_version \
        and f.framework_version == framework_version \
        and f.application == application:
          return f.id
    
    err_msg = f"\n\nYour config is not supported:\n\n--- \n\nBase framework: {base_framework} (v{base_framework_version})\nFramework:      {framework} (v{framework_version}) \nApplication:    {application} \n\n---\n\n is not supported.\n\nPlease contact: support@seeme.ai."
      
    raise NotImplementedError(err_msg)
    
  # -- CRUD models --

  def get_models(self) -> List[Model]:
    self.requires_login()

    models_api = self.endpoints[MODELS_ENDPOINT]

    ta = TypeAdapter(List[Model])
    return ta.validate_python(self.api_get(models_api))

  def create_model(self, model:Model) -> Model:
    self.requires_login()

    models_api = self.endpoints[MODELS_ENDPOINT]

    return Model(**self.api_post(models_api, model))

  def get_model(self, model_id:str) -> Model:
    self.requires_login()

    model_api = self.endpoints[MODELS_ENDPOINT] + "/" + model_id

    return  Model(**self.api_get(model_api))

  def update_model(self, model:Model) -> Model:
    self.requires_login()

    assert model
    assert model.id
    model_api = self.endpoints[MODELS_ENDPOINT] + "/" + model.id
    return Model(**self.api_put(model_api, model))

  def delete_model(self, model_id:str) -> str:
    self.requires_login()

    delete_api = self.endpoints[MODELS_ENDPOINT] + "/" + model_id

    return self.api_delete(delete_api)

  def upload_model(self, model_id:str, folder:str="data", filename:str="export.pkl") -> ModelVersion:
    self.requires_login()

    model_upload_api = self.endpoints[MODELS_ENDPOINT] + "/" + model_id  + "/upload"

    return ModelVersion(**self.upload(model_upload_api, folder, filename, 'application/octet-stream'))
  
  def upload_logo(self, model_id:str, folder:str="data", filename:str="logo.jpg") -> Model:
    self.requires_login()

    if filename.endswith("jpg"):
      content_type="image/jpg"
    elif filename.endswith("jpeg"):
      content_type="image/jpeg"
    elif filename.endswith("png"):
      content_type="image/png"

    model_upload_api = self.endpoints[MODELS_ENDPOINT] + "/" + model_id  + "/upload"

    return Model(**self.upload(model_upload_api, folder, filename,  content_type))
  
  def get_logo(self, model:Model):
    """Get model logo using legacy endpoint (deprecated, use get_model_logo instead)"""
    self.requires_login()

    logo_endpoint = self.endpoints[MODELS_ENDPOINT] + "/" + model.id + "/download/logo"
    return self.api_download(logo_endpoint, model.logo)

  def get_model_logo(self, model:Model, download_path:str=None):
    """Get model logo using new dedicated endpoint"""
    self.requires_login()

    logo_endpoint = self.endpoints[MODELS_ENDPOINT] + "/" + model.id + "/logo"
    filename = download_path if download_path else f"model_logo{model.logo}"
    return self.api_download(logo_endpoint, filename)

  def set_active_model_version(self, model:Union[Model, str], version_id:Union[str, ModelVersion]) -> Model:
    self.requires_login()

    if isinstance(model, str):
      model = self.get_model(model)

    if isinstance(version_id, ModelVersion):
      model.active_version_id = version_id.id
    else:
      model.active_version_id = version_id

    set_active_model_version_api = self.endpoints[MODELS_ENDPOINT] + "/" + model.id

    return Model(**self.api_put(set_active_model_version_api, model))
  
  def download_active_model(self, model:Model, asset_type:AssetType=AssetType.PKL, download_folder="."):
    if asset_type not in SUPPORTED_DOWNLOAD_EXTENSIONS:
      raise NotImplementedError

    model_endpoint = self.endpoints[MODELS_ENDPOINT] + "/" + model.id + "/download/" + asset_type

    extension = asset_type

    if asset_type == AssetType.LABELS:
      extension = "txt"

    name = model.active_version_id +"." + extension

    if asset_type == AssetType.CONVERSION_CFG:
      name = model.active_version_id +"_conversion.cfg"
    
    if asset_type == AssetType.ONNX_INT8:
      name = model.active_version_id + "_int8.onnx"

    download_folder = download_folder.rstrip("/")

    os.makedirs(download_folder, exist_ok=True)

    return self.api_download(model_endpoint, f"{download_folder}/{name}")

  def upload(self, url:str, folder:str, filename:str, content_type:str):
    self.requires_login()

    data = MultipartEncoder(
                fields={
                    'file': (filename, open(folder + "/" + filename, 'rb'), content_type)}
                       )

    content_headers = self.headers

    content_headers['Content-Type'] = data.content_type

    return self.api_upload(url, data=data, headers=content_headers)

  # -- CRUD Model Versions

  def get_model_versions(self, model_id:str) -> List[ModelVersion]:
    self.requires_login()

    model_versions_api = f"{self.endpoints[MODELS_ENDPOINT]}/{model_id}/{VERSIONS_ENDPOINT}"

    ta = TypeAdapter(List[ModelVersion])
    return ta.validate_python(self.api_get(model_versions_api))

  def get_model_version(self, model_id:str, version_id:str) -> ModelVersion:
    self.requires_login()

    model_version_api = f"{self.endpoints[MODELS_ENDPOINT]}/{model_id}/{VERSIONS_ENDPOINT}/{version_id}"

    return ModelVersion(**self.api_get(model_version_api))

  def create_model_version(self, model_id:str, version:ModelVersion) -> ModelVersion:
    self.requires_login()

    model_version_api = f"{self.endpoints[MODELS_ENDPOINT]}/{model_id}/{VERSIONS_ENDPOINT}"

    return ModelVersion(**self.api_post(model_version_api, version))
  
  def update_model_version(self, version:ModelVersion) -> ModelVersion:
    self.requires_login()

    model_version_api = f"{self.endpoints[MODELS_ENDPOINT]}/{version.model_id}/{VERSIONS_ENDPOINT}/{version.id}"

    return ModelVersion(**self.api_put(model_version_api, version))

  def delete_model_version(self, model_id:str, version_id:str) -> str:
    self.requires_login()

    model_version_api = f"{self.endpoints[MODELS_ENDPOINT]}/{model_id}/{VERSIONS_ENDPOINT}/{version_id}"

    return self.api_delete(model_version_api)

  def upload_model_version(self, version:ModelVersion, folder:str="data", filename:str="export.pkl") -> ModelVersion:

    model_version_upload_api = self.endpoints[MODELS_ENDPOINT] + "/" + version.model_id  + "/"+ VERSIONS_ENDPOINT + "/" + version.id + "/upload"

    return ModelVersion(**self.upload(model_version_upload_api, folder, filename, 'application/octet-stream'))

  def upload_model_version_logo(self, model_id:str, version_id:str, folder:str="data", filename:str="logo.jpg") -> ModelVersion:
    if filename.endswith("jpg"):
      content_type="image/jpg"
    elif filename.endswith("jpeg"):
      content_type="image/jpeg"
    elif filename.endswith("png"):
      content_type="image/png"

    model_version_upload_api = self.endpoints[MODELS_ENDPOINT] + "/" + model_id  + "/"+ VERSIONS_ENDPOINT + version_id + "/upload"

    return ModelVersion(**self.upload(model_version_upload_api, folder, filename, content_type))

  def download_model_version(self, model_version:ModelVersion, asset_type:AssetType=AssetType.PKL, download_folder:str="."):
    self.requires_login()

    extension = asset_type

    if asset_type == AssetType.LABELS:
      extension = "txt"

    name = model_version.id +"." + extension

    if asset_type == AssetType.CONVERSION_CFG:
      name = model_version.id +"_conversion.cfg"
    
    if asset_type == AssetType.ONNX_INT8:
      name = model_version.id + "_int8.onnx"

    version_endpoint = self.endpoints[MODELS_ENDPOINT] + "/" + model_version.model_id + "/" + VERSIONS_ENDPOINT + "/" + model_version.id + "/download/" + asset_type
    
    download_folder = download_folder.rstrip("/")

    os.makedirs(download_folder, exist_ok=True)
    
    return self.api_download(version_endpoint, f"{download_folder}/{name}")
  
  # -- Share model --
  def share_model(self, model_id:str, email:str, send_invite:bool=False) -> Share:
    self.requires_login()

    share = Share(
      email=email,
      entity_type=MODELS_ENDPOINT,
      entity_id=model_id,
      without_invite= not send_invite
    )

    share_url = f"{self.endpoints[MODELS_ENDPOINT]}/{model_id}/{SHARES_ENDPOINT}"

    return Share(**self.api_post(share_url, share))

  def get_model_shares(self, model_id:str) -> List[Share]:
    self.requires_login()

    share_url = f"{self.endpoints[MODELS_ENDPOINT]}/{model_id}/{SHARES_ENDPOINT}"

    ta = TypeAdapter(List[Share])
    return ta.validate_python(self.api_get(share_url))

  def delete_model_share(self, model_id:str, share_id:str) -> str:
    self.requires_login()

    share_url = f"{self.endpoints[MODELS_ENDPOINT]}/{model_id}/{SHARES_ENDPOINT}/{share_id}"

    return self.api_delete(share_url)

  # -- CRUD JOBS --
  def get_jobs(self, application_id:str="", states:List[JobStatus]=[JobStatus.WAITING, JobStatus.STARTED,JobStatus.FINISHED, JobStatus.ERROR], job_types:List[JobType]=[JobType.TRAINING]) -> List[Job]:
    self.requires_login()

    jobs_api = self.endpoints[JOBS_ENDPOINT]

    states = [elem if type(elem) == str else elem.value for elem in states]
    job_types = [elem if type(elem) == str else elem.value for elem in job_types]

    states_param = ",".join(states)
    jobs_param = ",".join(job_types)

    jobs_api += f"?applicationId={application_id}&status={states_param}&jobType={jobs_param}"

    ta = TypeAdapter(List[Job])

    return ta.validate_python(self.api_get(jobs_api))
  
  def get_job(self, job_id:str) -> Job:
    self.requires_login()

    job_api = self.endpoints[JOBS_ENDPOINT] + "/" + job_id

    return Job(**self.api_get(job_api))
  
  def create_job(self, job:Job) -> Job:
    self.requires_login()

    jobs_api = self.endpoints[JOBS_ENDPOINT]

    return Job(**self.api_post(jobs_api, job))
  
  def update_job(self, job:Job) -> Job:
    self.requires_login()

    jobs_api = self.endpoints[JOBS_ENDPOINT]  + "/" + job.id

    return Job(**self.api_put(jobs_api, job))
  
  def delete_job(self, job_id:str) -> str:
    self.requires_login()

    jobs_api = self.endpoints[JOBS_ENDPOINT] + "/" + job_id

    return self.api_delete(jobs_api)

  # -- CRUD Inference --

  def predict(self, model_id:str, item:Union[str,dict], application_type:ApplicationType=ApplicationType.IMAGE_CLASSIFICATION) -> Inference:
      return self.inference(model_id, item, application_type)

  def inference(self, model_id:str, item:Union[str,dict], application_type:ApplicationType=ApplicationType.IMAGE_CLASSIFICATION) -> Inference:
    self.requires_login()

    inference_api = self.endpoints[INFERENCE_ENDPOINT] + "/" + model_id

    if application_type==ApplicationType.IMAGE_CLASSIFICATION \
      or application_type==ApplicationType.OBJECT_DETECTION \
      or application_type==ApplicationType.OCR \
      or application_type==ApplicationType.SPEECH_TO_TEXT:

      item_name = os.path.basename(item)
      data = MultipartEncoder(
                  fields={
                      'file': (item_name, open(item, 'rb'), 'application/octet-stream')}
                        )

      content_headers = self.headers

      content_headers['Content-Type'] = data.content_type

      return Inference(**self.api_upload(inference_api, data=data, headers=content_headers))
    elif application_type==ApplicationType.TEXT_CLASSIFICATION \
      or application_type==ApplicationType.LANGUAGE_MODEL \
      or application_type==ApplicationType.NER:
      data = TextInput(input_text=item)

      return Inference(**self.api_post(inference_api, data))
    elif application_type==ApplicationType.STRUCTURED \
      or application_type==ApplicationType.SEARCH:
      item = json.dumps(item)
      data = TextInput(input_text=item)

      return Inference(**self.api_post(inference_api, data))
    else:
      raise NotImplementedError

  def version_predict(self, version:ModelVersion, item:Union[str,dict], application_type:ApplicationType=ApplicationType.IMAGE_CLASSIFICATION) -> Inference:
    return self.version_inference(version, item, application_type)

  # Obsolete, will be replaced by version_predict
  def version_inference(self, version:ModelVersion, item:Union[str,dict], application_type:ApplicationType=ApplicationType.IMAGE_CLASSIFICATION) -> Inference:
    self.requires_login()

    inference_api = self.endpoints[INFERENCE_ENDPOINT] + "/" + version.model_id + "/" + VERSIONS_ENDPOINT + "/" + version.id

    if application_type==ApplicationType.IMAGE_CLASSIFICATION or application_type==ApplicationType.OBJECT_DETECTION or application_type==ApplicationType.OCR:

      item_name = os.path.basename(item)
      data = MultipartEncoder(
                  fields={
                      'file': (item_name, open(item, 'rb'), 'application/octet-stream')}
                        )

      content_headers = self.headers

      content_headers['Content-Type'] = data.content_type

      return Inference(**self.api_upload(inference_api, data=data, headers=content_headers))
    elif application_type==ApplicationType.TEXT_CLASSIFICATION or application_type==ApplicationType.LANGUAGE_MODEL or application_type==ApplicationType.NER:
      data = TextInput(input_text=item)

      return Inference(**self.api_post(inference_api, data))
    elif application_type==ApplicationType.STRUCTURED:
      item = json.dumps(item)
      data = TextInput(input_text=item)

      return Inference(**self.api_post(inference_api, data))
    else:
      raise NotImplementedError

  def add_inference(self, model_id:str, inference:Inference) -> Inference:
     self.requires_login()

     add_inference_endpoint = self.endpoints[INFERENCE_ENDPOINT] + "/" + model_id + "/add"

     return Inference(**self.api_post(add_inference_endpoint, inference))

  def add_inference_file(self, inference_id:str, folder:str, filename:str, content_type:str) -> Inference:
    self.requires_login()

    add_inference_file_endpoint = self.endpoints[INFERENCE_ENDPOINT] + "/" + inference_id + "/upload"

    return Inference(**self.upload(add_inference_file_endpoint, folder, filename, content_type))

  def download_inference_file(self, inference_id:str, filename:str):

    self.requires_login()
    download_inference_endpoint = self.endpoints[INFERENCE_ENDPOINT] + "/" + inference_id + "/download"

    self.api_download(download_inference_endpoint, filename)

  def update_inference(self, inference:Inference) -> Inference:
    self.requires_login()

    inference_api = self.endpoints[INFERENCE_ENDPOINT] + "/" + inference.id

    return Inference(**self.api_put(inference_api, inference))

  def get_inferences(self, model_id:str, model_version_ids:List[str]=[], page_count:int=0, page_size:int=25, include_already_added:bool=False, show_hidden:bool=False) -> List[Inference]:
    self.requires_login()

    model_inferences_api = f"{self.endpoints[MODELS_ENDPOINT]}/{model_id}/{INFERENCE_ENDPOINT}"

    params = {
      "pageCount": page_count, 
      "pageSize": page_size,
      "modelVersionIds": ",".join(model_version_ids),
      "includeAlreadyAdded": include_already_added,
      "showHidden": show_hidden
    }

    result = self.api_get(model_inferences_api, params=params)
    if result is None:
      return []
    ta = TypeAdapter(List[Inference])
    return ta.validate_python(result)
  
  def add_inferences(self, dataset_id:str, dataset_version_id:str, dataset_split_id:str, add_inferences:AddInferences) -> AddInferences:
    self.requires_login()

    add_inferences_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{SPLITS_ENDPOINT}/{dataset_split_id}/{ADD_INFERENCES_ENDPOINT}"

    return AddInferences(** self.api_post(add_inferences_api, add_inferences))

  def get_inference_stats(self, model_id:str) -> float:
    self.requires_login()
    inference_stats_endpoint = f"{self.endpoints[MODELS_ENDPOINT]}/{model_id}/stats"

    return self.api_get(inference_stats_endpoint)

  # -- CRUD applicationS --
  def get_applications(self) -> List[Application]:
    self.requires_login()

    application_api = self.endpoints[APPLICATIONS_ENDPOINT]
    
    ta = TypeAdapter(List[Application])

    return ta.validate_python(self.api_get(application_api))

  # -- CRUD DATASETS --

  def get_datasets(self) -> List[Dataset]:
    self.requires_login()

    dataset_api = self.endpoints[DATASETS_ENDPOINT]

    ta = TypeAdapter(List[Dataset])

    return ta.validate_python(self.api_get(dataset_api))

  def create_dataset(self, dataset:Dataset) -> Dataset:
    self.requires_login()

    dataset_api = self.endpoints[DATASETS_ENDPOINT]

    ds = self.api_post(dataset_api, dataset)

    return Dataset(**ds)

  def get_dataset(self, dataset_id:str) -> Dataset:
    self.requires_login()

    dataset_api = self.endpoints[DATASETS_ENDPOINT] + "/" + dataset_id

    return Dataset(**self.api_get(dataset_api))

  def update_dataset(self, dataset:Dataset) -> Dataset:
    self.requires_login()

    assert dataset
    assert dataset.id
    dataset_api = self.endpoints[DATASETS_ENDPOINT] + "/" + dataset.id
    return Dataset(**self.api_put(dataset_api, dataset))

  def upload_dataset_logo(self, dataset_id:str, folder:str="data", filename:str="logo.jpg") -> Dataset:
    if filename.endswith("jpg"):
      content_type="image/jpg"
    elif filename.endswith("jpeg"):
      content_type="image/jpeg"
    elif filename.endswith("png"):
      content_type="image/png"

    datasets_upload_api = self.endpoints[DATASETS_ENDPOINT] + "/" + dataset_id  + "/upload"

    return Dataset(**self.upload(datasets_upload_api, folder, filename,  content_type))

  def get_dataset_logo(self, dataset:Dataset):
    logo_endpoint = self.endpoints[DATASETS_ENDPOINT] + "/" + dataset.id + "/logo"
    return self.api_download(logo_endpoint, dataset.logo)

  def delete_dataset(self, id:str) -> str:
    self.requires_login()
    dataset_api = self.endpoints[DATASETS_ENDPOINT] + "/" + id

    return self.api_delete(dataset_api)
  
  # -- Share Dataset --
  def share_dataset(self, dataset_id:str, email:str, send_invite:bool=False) -> Share:
    self.requires_login()

    share = Share(
      email=email,
      entity_type= DATASETS_ENDPOINT,
      entity_id= dataset_id,
      without_invite= not send_invite
    )

    share_url = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{SHARES_ENDPOINT}"

    return Share(**self.api_post(share_url, share))

  # --- Dataset Versions ---

  def get_dataset_versions(self, dataset_id:str)-> List[DatasetVersion]:
    self.requires_login()

    dataset_version_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}"

    ta = TypeAdapter(List[DatasetVersion])
    return ta.validate_python(self.api_get(dataset_version_api))
  
  def create_dataset_version(self, dataset_id:str, dataset_version:DatasetVersion) -> DatasetVersion:
    self.requires_login()

    dataset_version_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}"

    return DatasetVersion(**self.api_post(dataset_version_api, dataset_version))

  def get_dataset_version(self, dataset_id:str, dataset_version_id:str) -> DatasetVersion:
    self.requires_login()

    dataset_version_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}"

    return DatasetVersion(**self.api_get(dataset_version_api))

  def update_dataset_version(self, dataset_id:str, dataset_version:DatasetVersion) -> DatasetVersion:
    self.requires_login()

    dataset_version_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version.id}"

    return DatasetVersion(**self.api_put(dataset_version_api, dataset_version))

  def duplicate_dataset_version(self, dataset_id:str, dataset_version_id:str) -> DatasetVersion:
    duplicate_dataset_version_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/new"

    return DatasetVersion(**self.api_post(duplicate_dataset_version_api, DatasetVersion(dataset_id=dataset_id)))

  def delete_dataset_version(self, dataset_id:str, dataset_version_id:str) -> str:
    self.requires_login()

    dataset_version_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}"

    return self.api_delete(dataset_version_api)
  
  # --- Dataset Labels ---

  def create_dataset_label(self, dataset_id:str, dataset_version_id:str, label:Label) -> Label:
    self.requires_login()

    labels_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{LABELS_ENDPOINT}"

    return Label(**self.api_post(labels_api, label))

  def get_dataset_labels(self, dataset_id:str, dataset_version_id:str) -> List[Label]:
    self.requires_login()

    labels_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{LABELS_ENDPOINT}"

    result = self.api_get(labels_api)
    if result is None:
      return []
    ta = TypeAdapter(List[Label])
    return ta.validate_python(result)
  
  def get_dataset_label(self, dataset_id:str, dataset_version_id:str, label_id:str) -> Label:
    self.requires_login()

    labels_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{LABELS_ENDPOINT}/{label_id}"

    return Label(**self.api_get(labels_api))

  def update_dataset_label(self, dataset_id:str, dataset_version_id:str, label:Label) -> Label:
    self.requires_login()

    labels_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{LABELS_ENDPOINT}/{label.id}"

    return Label(**self.api_put(labels_api, label))

  def delete_dataset_label(self, dataset_id:str, dataset_version_id:str, label_id:str) -> str:
    self.requires_login()

    labels_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{LABELS_ENDPOINT}/{label_id}"

    return self.api_delete(labels_api)
  
  def get_label_stats(self, dataset_id:str, dataset_version_id:str, split_id:str) -> List[LabelStat]:
    self.requires_login()

    label_stats_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{LABELS_ENDPOINT}/{SPLITS_ENDPOINT}/{split_id}"

    result = self.api_get(label_stats_api)
    if result is None:
      return []
    ta = TypeAdapter(List[LabelStat])
    return ta.validate_python(result)
  
  def get_stats_for_unlabelled(self, label_stats:List[LabelStat]) -> List[LabelStat]:
    return self.get_stats_for_label(label_stats, "")

  def get_stats_for_label(self, label_stats:List[LabelStat], label_id:str) -> LabelStat:
    found_label_stat =  [ l for l in label_stats if l.label_id == label_id]
    return found_label_stat[0]
  
  # --- Dataset Splits ---
  
  def create_dataset_split(self, dataset_id:str, dataset_version_id:str, split:DatasetSplit) -> DatasetSplit:
    self.requires_login()

    splits_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{SPLITS_ENDPOINT}"

    return DatasetSplit(**self.api_post(splits_api, split))

  def get_dataset_splits(self, dataset_id:str, dataset_version_id:str) -> List[DatasetSplit]:
    self.requires_login()

    splits_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{SPLITS_ENDPOINT}"

    result = self.api_get(splits_api)
    if result is None:
      return []
    ta = TypeAdapter(List[DatasetSplit])
    return ta.validate_python(result)
  
  def get_dataset_split(self, dataset_id:str, dataset_version_id:str, split_id:str) -> DatasetSplit:
    self.requires_login()

    splits_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{SPLITS_ENDPOINT}/{split_id}"

    return DatasetSplit(**self.api_get(splits_api))

  def update_dataset_split(self, dataset_id:str, dataset_version_id:str, split:DatasetSplit) -> DatasetSplit:
    self.requires_login()

    splits_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{SPLITS_ENDPOINT}/{split.id}"

    return DatasetSplit(**self.api_put(splits_api, split))

  def delete_dataset_split(self, dataset_id:str, dataset_version_id:str, split:DatasetSplit) -> str:
    self.requires_login()

    splits_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{SPLITS_ENDPOINT}/{split.id}"

    return self.api_delete(splits_api)

  # --- Dataset Items ---
  
  def get_dataset_items(self, dataset_id:str, dataset_version_id:str, params:dict=None) -> List[DatasetItem]:
    self.requires_login()

    items_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{ITEMS_ENDPOINT}"

    result = self.api_get(items_api, params=params)
    if result is None:
      return []
    ta = TypeAdapter(List[DatasetItem])
    return ta.validate_python(result)

  def create_dataset_item(self, dataset_id:str, dataset_version_id:str, item:DatasetItem) -> DatasetItem:
    self.requires_login()

    items_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{ITEMS_ENDPOINT}"

    return DatasetItem(**self.api_post(items_api, item))

  def get_dataset_item(self, dataset_id:str, dataset_version_id:str, item_id:str) -> DatasetItem:
    self.requires_login()

    items_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{ITEMS_ENDPOINT}/{item_id}"

    return DatasetItem(**self.api_get(items_api))

  def update_dataset_item(self,  dataset_id:str, dataset_version_id:str, item:DatasetItem) -> DatasetItem:
    self.requires_login()

    items_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{ITEMS_ENDPOINT}/{item.id}"

    return DatasetItem(**self.api_put(items_api, item))

  def delete_dataset_item(self, dataset_id:str, dataset_version_id:str, split_id:str, item_id:str) -> DatasetItem:
    self.requires_login()

    items_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{SPLITS_ENDPOINT}/{split_id}/{ITEMS_ENDPOINT}/{item_id}"

    return DatasetItem(**self.api_delete(items_api))

  def upload_dataset_item_image(self, dataset_id:str, dataset_version_id:str, item_id:str, folder:str, filename:str) -> DatasetItem:
    self.requires_login()

    items_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{ITEMS_ENDPOINT}/{item_id}/upload"
    
    if filename.endswith("jpg"):
      content_type="image/jpg"
    elif filename.endswith("jpeg"):
      content_type="image/jpeg"
    elif filename.endswith("png"):
      content_type="image/png"
    else:
      print("Image type not supported")
      return

    data = MultipartEncoder(
                fields={
                    'file': (filename, open(folder + "/" + filename, 'rb'), content_type)}
                       )

    content_headers = self.headers

    content_headers['Content-Type'] = data.content_type

    return DatasetItem(**self.api_upload(items_api, data=data, headers=content_headers))

  def download_dataset_item_image(self, dataset_id:str, dataset_version_id:str, item_id:str, download_location:str, thumbnail:bool=False):
    self.requires_login()

    items_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{ITEMS_ENDPOINT}/{item_id}/download"
  
    if thumbnail:
      items_api += "?thumbnail=true"

    return self.api_download(items_api, download_location)
  
    def download_dataset_item_file(self, dataset_id:str, dataset_version_id:str, item_id:str, download_location:str, thumbnail:bool=False):
      self.requires_login()

      items_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{ITEMS_ENDPOINT}/{item_id}/download"
    
      if thumbnail:
        items_api += "?thumbnail=true"

      return self.api_download(items_api, download_location)
  
  # --- Dataset Annotations ---
  
  def annotate(self, dataset_id:str, dataset_version_id:str, annotation:Annotation) -> Annotation:

    # TODO: handle non-multi label dataset: see if there already is an annotation, delete it first. Or should this be on the API?
    self.requires_login()

    annotation_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{ANNOTATIONS_ENDPOINT}"

    return Annotation(**self.api_post(annotation_api, annotation))

  def update_annotation(self, dataset_id:str, dataset_version_id:str, annotation:Annotation) -> Annotation:
    self.requires_login()

    annotation_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{ANNOTATIONS_ENDPOINT}/{annotation.id}"

    return Annotation(**self.api_put(annotation_api, annotation))

  def delete_annotation(self, dataset_id:str, dataset_version_id:str, annotation_id:str) -> Annotation:
    self.requires_login()

    annotation_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/{ANNOTATIONS_ENDPOINT}/{annotation_id}"

    return Annotation(**self.api_delete(annotation_api))

  # --- Uploade/Download Datasets ---

  def download_dataset(self, dataset_id:str, dataset_version_id:str, split_id:str="", extract_to_folder:str="data", download_file:str="dataset.zip", remove_download_file:bool=True, export_format:DatasetFormat=None, params:dict={}):
    self.requires_login()

    dataset_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/download"

    if split_id != "":
      dataset_api = f"{dataset_api}/{split_id}"

    if export_format:
      if export_format not in self.supported_dataset_export_formats:
        print(f"WARNING: Requested export format: '{export_format}' not supported. Returning the default export format.")

      params["format"]= export_format.value

    self.api_download(dataset_api, download_file, params=params)

    with zipfile.ZipFile(download_file, 'r') as zip_ref:
      zip_ref.extractall(extract_to_folder)

    if remove_download_file:
      os.remove(download_file)
    
  def upload_dataset_version(self, dataset_id:str, dataset_version_id:str, folder:str="data", filename:str="dataset.zip", format:DatasetFormat=None) -> DatasetVersion:
    self.requires_login()

    dataset_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{VERSIONS_ENDPOINT}/{dataset_version_id}/upload"

    if format:
      if format in self.supported_dataset_import_formats: dataset_api = f"{dataset_api}/{format.value}"
      else:
        print("Supported import formats")
        print(self.supported_dataset_import_formats)
        raise NotImplementedError()

    content_type="application/x-zip-compressed"

    data = MultipartEncoder(
            fields={
                'file': (filename, open(folder + "/" + filename, 'rb'), content_type)
            }
          )

    content_headers = self.headers

    content_headers['Content-Type'] = data.content_type

    return DatasetVersion(**self.api_upload(dataset_api, data=data, headers=content_headers))

  # --- Workflows ---

  def get_workflows(self) -> List[Workflow]:
    self.requires_login()

    workflow_api = self.endpoints[WORKFLOWS_ENDPOINT]

    ta = TypeAdapter(List[Workflow])

    return ta.validate_python(self.api_get(workflow_api))

  def create_workflow(self, workflow:Workflow) -> Workflow:
    self.requires_login()

    workflow_api = self.endpoints[WORKFLOWS_ENDPOINT]

    wf = self.api_post(workflow_api, workflow)

    return Workflow(**wf)

  def get_workflow(self, workflow_id:str) -> Workflow:
    self.requires_login()

    workflow_api = self.endpoints[WORKFLOWS_ENDPOINT] + "/" + workflow_id

    return Workflow(**self.api_get(workflow_api))
  
  def update_workflow(self, workflow:Workflow) -> Workflow:
    self.requires_login()

    assert workflow
    assert workflow.id

    workflow_api = self.endpoints[WORKFLOWS_ENDPOINT] + "/" + workflow.id

    return Workflow(**self.api_put(workflow_api, workflow))
  
  def delete_workflow(self, id:str) -> str:
    self.requires_login()
    workflow_api = self.endpoints[WORKFLOWS_ENDPOINT] + "/" + id

    return self.api_delete(workflow_api)

  # --- Workflow Logo ---
  def upload_workflow_logo(self, workflow_id:str, folder:str="data", filename:str="logo.jpg") -> Workflow:
    self.requires_login()

    if filename.endswith("jpg"):
      content_type="image/jpg"
    elif filename.endswith("jpeg"):
      content_type="image/jpeg"
    elif filename.endswith("png"):
      content_type="image/png"

    workflow_logo_api = self.endpoints[WORKFLOWS_ENDPOINT] + "/" + workflow_id + "/logo"

    return Workflow(**self.upload(workflow_logo_api, folder, filename, content_type))

  def get_workflow_logo(self, workflow:Workflow, download_path:str=None):
    self.requires_login()

    logo_endpoint = self.endpoints[WORKFLOWS_ENDPOINT] + "/" + workflow.id + "/logo"
    filename = download_path if download_path else f"workflow_logo{workflow.logo}"
    return self.api_download(logo_endpoint, filename)

  def delete_workflow_logo(self, workflow_id:str) -> str:
    self.requires_login()
    workflow_logo_api = self.endpoints[WORKFLOWS_ENDPOINT] + "/" + workflow_id + "/logo"
    return self.api_delete(workflow_logo_api)

  def run_workflow(self, workflow_id:str, item:Union[str,dict]) -> WorkflowExecutionResponse:
    self.requires_login()

    wf = self.get_workflow(workflow_id)

    if not wf.active_version_id:
      raise Exception("No active worklow version")
    
    workflow_version = self.find_item_in_array(wf.versions,"id", wf.active_version_id, first_item=True, t=WorkflowVersion)

    sorter = WorkflowSorter(workflow_version.nodes, workflow_version.edges)
    sorted_nodes = sorter.sorted_nodes()

    #print("sorted nodes")
    #print(sorted_nodes) 

    if len(sorted_nodes) == 0:
      raise Exception("Workflow is empty")

    first_node = sorted_nodes[0]

    if first_node.entity_type == "dataset":
      raise Exception("Dataset as starting not is not supported")
    

    model = self.get_model(first_node.entity_id)

    #print("model")
    #print(model)

    #print("applications")
    #print(self.applications)

    ## TODO: turn into a helper
    application = self.find_item_in_array(self.applications, "id", model.application_id, first_item=True, t=Application)
    application_type = application.application
    
    #print("model_application")
    #print(application_type)


    workflow_api = self.endpoints[WORKFLOWS_ENDPOINT] + "/" + workflow_id + "/execute"

    if application_type==ApplicationType.IMAGE_CLASSIFICATION \
      or application_type==ApplicationType.OBJECT_DETECTION \
      or application_type==ApplicationType.OCR \
      or application_type==ApplicationType.SPEECH_TO_TEXT:

      item_name = os.path.basename(item)
      data = MultipartEncoder(
                  fields={
                      'file': (item_name, open(item, 'rb'), 'application/octet-stream')}
                        )

      content_headers = self.headers

      content_headers['Content-Type'] = data.content_type

      return WorkflowExecutionResponse(**self.api_upload(workflow_api, data=data, headers=content_headers))
    elif application_type==ApplicationType.TEXT_CLASSIFICATION \
      or application_type==ApplicationType.LANGUAGE_MODEL \
      or application_type==ApplicationType.NER:
      data = TextInput(input_text=item)

      return WorkflowExecutionResponse(**self.api_post(workflow_api, data))
    elif application_type==ApplicationType.STRUCTURED \
      or application_type==ApplicationType.SEARCH:
      item = json.dumps(item)
      data = TextInput(input_text=item)

      return WorkflowExecutionResponse(**self.api_post(workflow_api, data))
    else:
      raise NotImplementedError

  # --- Workflow Versions ---
  
  def get_workflow_versions(self, workflow_id:str) -> List[WorkflowVersion]:
    self.requires_login()

    workflow_version_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}"

    ta = TypeAdapter(List[WorkflowVersion])
    return ta.validate_python(self.api_get(workflow_version_api))
  
  def create_workflow_version(self, workflow_id:str, workflow_version:WorkflowVersion) -> WorkflowVersion:
    self.requires_login()

    assert workflow_version
    
    workflow_version_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}"

    return WorkflowVersion(**self.api_post(workflow_version_api, workflow_version))

  def get_workflow_version(self, workflow_id:str, workflow_version_id:str) -> WorkflowVersion:
    self.requires_login()

    workflow_version_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version_id}"

    return WorkflowVersion(**self.api_get(workflow_version_api))

  def update_workflow_version(self, workflow_id:str, workflow_version:WorkflowVersion) -> WorkflowVersion:
    self.requires_login()

    assert workflow_version
    assert workflow_version.id

    workflow_version_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version.id}"

    return WorkflowVersion(**self.api_put(workflow_version_api, workflow_version))

  def delete_workflow_version(self, workflow_id:str, workflow_version_id:str) -> str:
    self.requires_login()

    workflow_version_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version_id}"

    return self.api_delete(workflow_version_api)

  # --- Workflow Nodes ---

  def get_workflow_nodes(self, workflow_id:str, workflow_version_id:str) -> List[WorkflowNode]:
    self.requires_login()

    workflow_node_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version_id}/{NODES_ENDPOINT}"

    ta = TypeAdapter(List[WorkflowNode])
    return ta.validate_python(self.api_get(workflow_node_api))
  
  def create_workflow_node(self, workflow_id:str, workflow_version_id:str, workflow_node:WorkflowNode) -> WorkflowNode:
    self.requires_login()

    assert workflow_id
    assert workflow_version_id
    assert workflow_node
    
    workflow_node_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version_id}/{NODES_ENDPOINT}"

    return WorkflowNode(**self.api_post(workflow_node_api, workflow_node))

  def get_workflow_node(self, workflow_id:str, workflow_version_id:str, node_id:str) -> WorkflowNode:
    self.requires_login()

    workflow_node_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version_id}/{NODES_ENDPOINT}/{node_id}"

    return WorkflowNode(**self.api_get(workflow_node_api))

  def update_workflow_node(self, workflow_id:str, workflow_version_id:str, node:WorkflowNode) -> WorkflowNode:
    self.requires_login()

    assert workflow_id
    assert workflow_version_id
    assert node

    workflow_node_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version_id}/{NODES_ENDPOINT}/{node.id}"

    return WorkflowNode(**self.api_put(workflow_node_api, node))

  def delete_workflow_node(self, workflow_id:str, workflow_version_id:str, node_id:str) -> str:
    self.requires_login()

    workflow_node_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version_id}/{NODES_ENDPOINT}/{node_id}"

    return self.api_delete(workflow_node_api)

  # --- Workflow Edges ---

  def get_workflow_edges(self, workflow_id:str, workflow_version_id:str) -> List[WorkflowEdge]:
    self.requires_login()

    workflow_edge_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version_id}/{EDGES_ENDPOINT}"

    ta = TypeAdapter(List[WorkflowEdge])
    return ta.validate_python(self.api_get(workflow_edge_api))
  
  def create_workflow_edge(self, workflow_id:str, workflow_version_id:str, workflow_edge:WorkflowEdge) -> WorkflowEdge:
    self.requires_login()

    assert workflow_id
    assert workflow_version_id
    assert workflow_edge
    
    workflow_edge_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version_id}/{EDGES_ENDPOINT}"

    return WorkflowNode(**self.api_post(workflow_edge_api, workflow_edge))

  def get_workflow_edge(self, workflow_id:str, workflow_version_id:str, edge_id:str) -> WorkflowEdge:
    self.requires_login()

    workflow_edge_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version_id}/{EDGES_ENDPOINT}/{edge_id}"

    return WorkflowEdge(**self.api_get(workflow_edge_api))

  def update_workflow_edge(self, workflow_id:str, workflow_version_id:str, edge:WorkflowEdge) -> WorkflowEdge:
    self.requires_login()

    assert workflow_id
    assert workflow_version_id
    assert edge

    workflow_edge_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version_id}/{EDGES_ENDPOINT}/{edge.id}"

    return WorkflowEdge(**self.api_put(workflow_edge_api, edge))

  def delete_workflow_edge(self, workflow_id:str, workflow_version_id:str, edge_id:str) -> str:
    self.requires_login()

    workflow_edge_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{workflow_version_id}/{EDGES_ENDPOINT}/{edge_id}"

    return self.api_delete(workflow_edge_api)

  # --- Post-Processors ---

  def get_post_processors(self, dataset_id:str) -> List[PostProcessorWithModel]:
    """Get all post-processors for a dataset."""
    self.requires_login()

    post_processors_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{POST_PROCESSORS_ENDPOINT}"

    result = self.api_get(post_processors_api)
    if result is None:
      return []
    ta = TypeAdapter(List[PostProcessorWithModel])
    return ta.validate_python(result)

  def get_post_processor(self, dataset_id:str, processor_id:str) -> PostProcessorWithModel:
    """Get a single post-processor by ID."""
    self.requires_login()

    post_processor_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{POST_PROCESSORS_ENDPOINT}/{processor_id}"

    return PostProcessorWithModel(**self.api_get(post_processor_api))

  def create_post_processor(self, dataset_id:str, processor:CreatePostProcessorRequest) -> DatasetPostProcessor:
    """Create a new post-processor for a dataset."""
    self.requires_login()

    post_processors_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{POST_PROCESSORS_ENDPOINT}"

    return DatasetPostProcessor(**self.api_post(post_processors_api, processor))

  def update_post_processor(self, dataset_id:str, processor_id:str, updates:UpdatePostProcessorRequest) -> DatasetPostProcessor:
    """Update an existing post-processor."""
    self.requires_login()

    post_processor_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{POST_PROCESSORS_ENDPOINT}/{processor_id}"

    return DatasetPostProcessor(**self.api_put(post_processor_api, updates))

  def delete_post_processor(self, dataset_id:str, processor_id:str) -> str:
    """Delete a post-processor."""
    self.requires_login()

    post_processor_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{POST_PROCESSORS_ENDPOINT}/{processor_id}"

    return self.api_delete(post_processor_api)

  def get_post_processor_jobs(self, dataset_id:str, params:dict=None) -> List[PostProcessorJobWithDetails]:
    """Get post-processor jobs for a dataset."""
    self.requires_login()

    jobs_api = f"{self.endpoints[DATASETS_ENDPOINT]}/{dataset_id}/{POST_PROCESSORS_ENDPOINT}/jobs"

    result = self.api_get(jobs_api, params=params)
    if result is None:
      return []
    ta = TypeAdapter(List[PostProcessorJobWithDetails])
    return ta.validate_python(result)

  # --- Workflow Executions ---

  def execute_workflow_async(self, workflow_id:str, request:WorkflowExecutionRequest) -> WorkflowExecutionResponse:
    """Execute a workflow asynchronously. Returns immediately with an execution ID."""
    self.requires_login()

    execute_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/execute"

    return WorkflowExecutionResponse(**self.api_post(execute_api, request))

  def execute_workflow_async_with_file(self, workflow_id:str, folder:str, filename:str) -> WorkflowExecutionResponse:
    """Execute a workflow asynchronously with a file upload."""
    self.requires_login()

    execute_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/execute"

    return WorkflowExecutionResponse(**self.upload(execute_api, folder, filename, 'application/octet-stream'))

  def get_workflow_executions(self, workflow_id:str) -> List[WorkflowExecution]:
    """Get all executions for a workflow."""
    self.requires_login()

    executions_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{EXECUTIONS_ENDPOINT}"

    result = self.api_get(executions_api)
    if result is None:
      return []
    ta = TypeAdapter(List[WorkflowExecution])
    return ta.validate_python(result)

  def get_workflow_execution(self, workflow_id:str, execution_id:str) -> WorkflowExecution:
    """Get a specific workflow execution."""
    self.requires_login()

    execution_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{EXECUTIONS_ENDPOINT}/{execution_id}"

    return WorkflowExecution(**self.api_get(execution_api))

  def download_workflow_execution_input_file(self, workflow_id:str, execution_id:str, download_location:str):
    """Download the input file for a workflow execution."""
    self.requires_login()

    input_file_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{EXECUTIONS_ENDPOINT}/{execution_id}/input-file"

    return self.api_download(input_file_api, download_location)

  def cancel_workflow_execution(self, workflow_id:str, execution_id:str) -> str:
    """Cancel a running workflow execution."""
    self.requires_login()

    cancel_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{EXECUTIONS_ENDPOINT}/{execution_id}/cancel"

    # POST with empty body
    class EmptyRequest(BaseModel):
      pass

    return self.api_post(cancel_api, EmptyRequest())

  def execute_workflow_version_async(self, workflow_id:str, version_id:str, request:WorkflowExecutionRequest) -> WorkflowExecutionResponse:
    """Execute a specific workflow version asynchronously."""
    self.requires_login()

    execute_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{version_id}/execute"

    return WorkflowExecutionResponse(**self.api_post(execute_api, request))

  def execute_workflow_version_async_with_file(self, workflow_id:str, version_id:str, folder:str, filename:str) -> WorkflowExecutionResponse:
    """Execute a specific workflow version asynchronously with a file upload."""
    self.requires_login()

    execute_api = f"{self.endpoints[WORKFLOWS_ENDPOINT]}/{workflow_id}/{VERSIONS_ENDPOINT}/{version_id}/execute"

    return WorkflowExecutionResponse(**self.upload(execute_api, folder, filename, 'application/octet-stream'))

  # --- Graphs ---

  def get_graphs(self) -> List[Graph]:
    """Get all graphs for the current user."""
    self.requires_login()

    graphs_api = self.endpoints[GRAPHS_ENDPOINT]

    result = self.api_get(graphs_api)
    if result is None:
      return []
    ta = TypeAdapter(List[Graph])
    return ta.validate_python(result)

  def get_graph(self, graph_id:str) -> Graph:
    """Get a single graph by ID."""
    self.requires_login()

    graph_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}"

    return Graph(**self.api_get(graph_api))

  def create_graph(self, graph:Graph) -> Graph:
    """Create a new graph."""
    self.requires_login()

    graphs_api = self.endpoints[GRAPHS_ENDPOINT]

    return Graph(**self.api_post(graphs_api, graph))

  def update_graph(self, graph:Graph) -> Graph:
    """Update an existing graph."""
    self.requires_login()

    graph_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph.id}"

    return Graph(**self.api_put(graph_api, graph))

  def delete_graph(self, graph_id:str) -> str:
    """Delete a graph."""
    self.requires_login()

    graph_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}"

    return self.api_delete(graph_api)

  def get_graph_stats(self, graph_id:str) -> dict:
    """Get statistics for a graph."""
    self.requires_login()

    stats_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/stats"

    return self.api_get(stats_api)

  # --- Graph Versions ---

  def get_graph_versions(self, graph_id:str) -> List[GraphVersion]:
    """Get all versions of a graph."""
    self.requires_login()

    versions_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}"

    result = self.api_get(versions_api)
    if result is None:
      return []
    ta = TypeAdapter(List[GraphVersion])
    return ta.validate_python(result)

  def get_graph_version(self, graph_id:str, version_id:str) -> GraphVersion:
    """Get a specific graph version."""
    self.requires_login()

    version_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}"

    return GraphVersion(**self.api_get(version_api))

  def create_graph_version(self, graph_id:str, version:GraphVersion) -> GraphVersion:
    """Create a new graph version."""
    self.requires_login()

    versions_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}"

    return GraphVersion(**self.api_post(versions_api, version))

  def update_graph_version(self, graph_id:str, version:GraphVersion) -> GraphVersion:
    """Update a graph version."""
    self.requires_login()

    version_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version.id}"

    return GraphVersion(**self.api_put(version_api, version))

  def delete_graph_version(self, graph_id:str, version_id:str) -> str:
    """Delete a graph version."""
    self.requires_login()

    version_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}"

    return self.api_delete(version_api)

  def set_active_graph_version(self, graph_id:str, version_id:str) -> dict:
    """Set a graph version as the active version."""
    self.requires_login()

    activate_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}/activate"

    class EmptyRequest(BaseModel):
      pass

    return self.api_post(activate_api, EmptyRequest())

  def duplicate_graph_version(self, graph_id:str, version_id:str) -> GraphVersion:
    """Duplicate a graph version."""
    self.requires_login()

    duplicate_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}/duplicate"

    class EmptyRequest(BaseModel):
      pass

    return GraphVersion(**self.api_post(duplicate_api, EmptyRequest()))

  # --- Graph Nodes ---

  def create_graph_node(self, graph_id:str, version_id:str, node:GraphNode) -> dict:
    """Create a node in the graph."""
    self.requires_login()

    nodes_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}/nodes"

    return self.api_post(nodes_api, node)

  def create_graph_nodes(self, graph_id:str, version_id:str, nodes:List[GraphNode]) -> dict:
    """Create multiple nodes in bulk."""
    self.requires_login()

    nodes_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}/nodes/bulk"

    request = BulkNodeRequest(nodes=nodes)
    return self.api_post(nodes_api, request)

  def get_graph_node(self, graph_id:str, version_id:str, node_uid:str) -> dict:
    """Get a specific node by UID."""
    self.requires_login()

    node_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}/nodes/{node_uid}"

    return self.api_get(node_api)

  def update_graph_node(self, graph_id:str, version_id:str, node_uid:str, node:GraphNode) -> dict:
    """Update a node."""
    self.requires_login()

    node_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}/nodes/{node_uid}"

    return self.api_put(node_api, node)

  def delete_graph_node(self, graph_id:str, version_id:str, node_uid:str) -> dict:
    """Delete a node."""
    self.requires_login()

    node_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}/nodes/{node_uid}"

    return self.api_delete(node_api)

  def query_graph_nodes(self, graph_id:str, version_id:str, params:dict=None) -> List[dict]:
    """Query nodes in the graph."""
    self.requires_login()

    query_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}/nodes/query"

    return self.api_get(query_api, params=params)

  # --- Graph Edges ---

  def create_graph_edge(self, graph_id:str, version_id:str, edge:GraphEdge) -> dict:
    """Create an edge in the graph."""
    self.requires_login()

    edges_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}/edges"

    return self.api_post(edges_api, edge)

  def create_graph_edges(self, graph_id:str, version_id:str, edges:List[GraphEdge]) -> dict:
    """Create multiple edges in bulk."""
    self.requires_login()

    edges_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}/edges/bulk"

    request = BulkEdgeRequest(edges=edges)
    return self.api_post(edges_api, request)

  def delete_graph_edge(self, graph_id:str, version_id:str, params:dict=None) -> dict:
    """Delete an edge."""
    self.requires_login()

    edges_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}/edges"

    return self.api_delete(edges_api)

  # --- Graph Queries ---

  def execute_graph_query(self, graph_id:str, version_id:str, query:str) -> dict:
    """Execute a DQL query on the graph."""
    self.requires_login()

    query_api = f"{self.endpoints[GRAPHS_ENDPOINT]}/{graph_id}/{VERSIONS_ENDPOINT}/{version_id}/query"

    class QueryRequest(BaseModel):
      query: str

    return self.api_post(query_api, QueryRequest(query=query))

  # --- Organizations (RBAC) ---

  def get_organizations(self) -> List[Organization]:
    """Get all organizations for the current user."""
    self.requires_login()

    orgs_api = self.endpoints[ORGANIZATIONS_ENDPOINT]

    result = self.api_get(orgs_api)
    if result is None:
      return []
    ta = TypeAdapter(List[Organization])
    return ta.validate_python(result)

  def get_organization(self, org_id:str) -> Organization:
    """Get a single organization by ID."""
    self.requires_login()

    org_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{org_id}"

    return Organization(**self.api_get(org_api))

  def create_organization(self, organization:Organization) -> Organization:
    """Create a new organization."""
    self.requires_login()

    orgs_api = self.endpoints[ORGANIZATIONS_ENDPOINT]

    return Organization(**self.api_post(orgs_api, organization))

  def update_organization(self, organization:Organization) -> Organization:
    """Update an existing organization."""
    self.requires_login()

    assert organization and organization.id

    org_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{organization.id}"

    return Organization(**self.api_put(org_api, organization))

  def delete_organization(self, org_id:str) -> str:
    """Delete an organization."""
    self.requires_login()

    org_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{org_id}"

    return self.api_delete(org_api)

  # --- Organization Members ---

  def get_organization_members(self, org_id:str) -> List[OrganizationMember]:
    """Get all members of an organization."""
    self.requires_login()

    members_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{org_id}/{MEMBERS_ENDPOINT}"

    result = self.api_get(members_api)
    if result is None:
      return []
    ta = TypeAdapter(List[OrganizationMember])
    return ta.validate_python(result)

  def invite_to_organization(self, org_id:str, email:str, role_id:str=None) -> OrganizationMember:
    """Invite a user to an organization by email."""
    self.requires_login()

    members_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{org_id}/{MEMBERS_ENDPOINT}"

    invite = OrganizationInvite(email=email, role_id=role_id)

    return OrganizationMember(**self.api_post(members_api, invite))

  def remove_organization_member(self, org_id:str, member_id:str) -> str:
    """Remove a member from an organization."""
    self.requires_login()

    member_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{org_id}/{MEMBERS_ENDPOINT}/{member_id}"

    return self.api_delete(member_api)

  def update_organization_member_role(self, org_id:str, member_id:str, role_id:str) -> OrganizationMember:
    """Update the role of an organization member."""
    self.requires_login()

    role_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{org_id}/{MEMBERS_ENDPOINT}/{member_id}/role"

    role_update = UpdateMemberRole(role_id=role_id)

    return OrganizationMember(**self.api_put(role_api, role_update))

  # --- Organization Logo ---

  def upload_organization_logo(self, org_id:str, folder:str="data", filename:str="logo.jpg") -> Organization:
    """Upload a logo for an organization."""
    self.requires_login()

    if filename.endswith("jpg"):
      content_type = "image/jpg"
    elif filename.endswith("jpeg"):
      content_type = "image/jpeg"
    elif filename.endswith("png"):
      content_type = "image/png"
    else:
      content_type = "image/jpeg"

    logo_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{org_id}/{LOGO_ENDPOINT}"

    return Organization(**self.upload(logo_api, folder, filename, content_type))

  def get_organization_logo(self, org_id:str, download_location:str):
    """Download the logo for an organization."""
    self.requires_login()

    logo_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{org_id}/{LOGO_ENDPOINT}"

    return self.api_download(logo_api, download_location)

  def delete_organization_logo(self, org_id:str) -> str:
    """Delete the logo of an organization."""
    self.requires_login()

    logo_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{org_id}/{LOGO_ENDPOINT}"

    return self.api_delete(logo_api)

  # --- Organization Scoped Resources ---

  def get_organization_projects(self, org_id:str) -> List[Project]:
    """Get all projects belonging to an organization."""
    self.requires_login()

    projects_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{org_id}/{PROJECTS_ENDPOINT}"

    result = self.api_get(projects_api)
    if result is None:
      return []
    ta = TypeAdapter(List[Project])
    return ta.validate_python(result)

  def get_organization_teams(self, org_id:str) -> List[Team]:
    """Get all teams belonging to an organization."""
    self.requires_login()

    teams_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{org_id}/{TEAMS_ENDPOINT}"

    result = self.api_get(teams_api)
    if result is None:
      return []
    ta = TypeAdapter(List[Team])
    return ta.validate_python(result)

  def get_organization_roles(self, org_id:str) -> List[Role]:
    """Get all roles belonging to an organization."""
    self.requires_login()

    roles_api = f"{self.endpoints[ORGANIZATIONS_ENDPOINT]}/{org_id}/{ROLES_ENDPOINT}"

    result = self.api_get(roles_api)
    if result is None:
      return []
    ta = TypeAdapter(List[Role])
    return ta.validate_python(result)

  # --- Projects (RBAC) ---

  def get_projects(self, organization_id: str = None, team_id: str = None) -> List[Project]:
    """Get all projects for the current user, optionally filtered by organization or team."""
    self.requires_login()

    projects_api = self.endpoints[PROJECTS_ENDPOINT]

    params = {}
    if organization_id:
      params["organization_id"] = organization_id
    if team_id:
      params["team_id"] = team_id

    if params:
      query_string = "&".join(f"{k}={v}" for k, v in params.items())
      projects_api = f"{projects_api}?{query_string}"

    result = self.api_get(projects_api)
    if result is None:
      return []
    ta = TypeAdapter(List[Project])
    return ta.validate_python(result)

  def get_team_projects(self, team_id: str) -> List[Project]:
    """Get all projects for a specific team."""
    return self.get_projects(team_id=team_id)

  def get_project(self, project_id:str) -> Project:
    """Get a single project by ID."""
    self.requires_login()

    project_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project_id}"

    return Project(**self.api_get(project_api))

  def create_project(self, project:Project) -> Project:
    """Create a new project."""
    self.requires_login()

    projects_api = self.endpoints[PROJECTS_ENDPOINT]

    return Project(**self.api_post(projects_api, project))

  def update_project(self, project:Project) -> Project:
    """Update an existing project."""
    self.requires_login()

    assert project and project.id

    project_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project.id}"

    return Project(**self.api_put(project_api, project))

  def delete_project(self, project_id:str) -> str:
    """Delete a project."""
    self.requires_login()

    project_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project_id}"

    return self.api_delete(project_api)

  # --- Project Members ---

  def get_project_members(self, project_id:str) -> List[ProjectMember]:
    """Get all members of a project."""
    self.requires_login()

    members_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project_id}/{MEMBERS_ENDPOINT}"

    result = self.api_get(members_api)
    if result is None:
      return []
    ta = TypeAdapter(List[ProjectMember])
    return ta.validate_python(result)

  def add_project_member(self, project_id:str, user_id:str, role_id:str=None) -> ProjectMember:
    """Add a member to a project."""
    self.requires_login()

    members_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project_id}/{MEMBERS_ENDPOINT}"

    member = AddProjectMember(user_id=user_id, role_id=role_id)

    return ProjectMember(**self.api_post(members_api, member))

  def remove_project_member(self, project_id:str, member_id:str) -> str:
    """Remove a member from a project."""
    self.requires_login()

    member_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project_id}/{MEMBERS_ENDPOINT}/{member_id}"

    return self.api_delete(member_api)

  def update_project_member_role(self, project_id:str, member_id:str, role_id:str) -> ProjectMember:
    """Update the role of a project member."""
    self.requires_login()

    role_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project_id}/{MEMBERS_ENDPOINT}/{member_id}/role"

    role_update = UpdateMemberRole(role_id=role_id)

    return ProjectMember(**self.api_put(role_api, role_update))

  # --- Project Resources ---

  def get_project_resources(self, project_id:str) -> List[ProjectResource]:
    """Get all resources assigned to a project."""
    self.requires_login()

    resources_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project_id}/{RESOURCES_ENDPOINT}"

    result = self.api_get(resources_api)
    if result is None:
      return []
    ta = TypeAdapter(List[ProjectResource])
    return ta.validate_python(result)

  def assign_resource_to_project(self, project_id:str, resource_type:str, resource_id:str) -> ProjectResource:
    """Assign a resource (model, dataset, workflow, graph) to a project."""
    self.requires_login()

    resources_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project_id}/{RESOURCES_ENDPOINT}"

    resource = AssignProjectResource(resource_type=resource_type, resource_id=resource_id)

    return ProjectResource(**self.api_post(resources_api, resource))

  def remove_resource_from_project(self, project_id:str, resource_type:str, resource_id:str) -> str:
    """Remove a resource from a project."""
    self.requires_login()

    resource_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project_id}/{RESOURCES_ENDPOINT}/{resource_type}/{resource_id}"

    return self.api_delete(resource_api)

  # --- Project Logo ---

  def upload_project_logo(self, project_id:str, folder:str="data", filename:str="logo.jpg") -> Project:
    """Upload a logo for a project."""
    self.requires_login()

    if filename.endswith("jpg"):
      content_type = "image/jpg"
    elif filename.endswith("jpeg"):
      content_type = "image/jpeg"
    elif filename.endswith("png"):
      content_type = "image/png"
    else:
      content_type = "image/jpeg"

    logo_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project_id}/{LOGO_ENDPOINT}"

    return Project(**self.upload(logo_api, folder, filename, content_type))

  def get_project_logo(self, project_id:str, download_location:str):
    """Download the logo for a project."""
    self.requires_login()

    logo_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project_id}/{LOGO_ENDPOINT}"

    return self.api_download(logo_api, download_location)

  def delete_project_logo(self, project_id:str) -> str:
    """Delete the logo of a project."""
    self.requires_login()

    logo_api = f"{self.endpoints[PROJECTS_ENDPOINT]}/{project_id}/{LOGO_ENDPOINT}"

    return self.api_delete(logo_api)

  # --- Teams (RBAC) ---

  def get_teams(self) -> List[Team]:
    """Get all teams for the current user."""
    self.requires_login()

    teams_api = self.endpoints[TEAMS_ENDPOINT]

    result = self.api_get(teams_api)
    if result is None:
      return []
    ta = TypeAdapter(List[Team])
    return ta.validate_python(result)

  def get_team(self, team_id:str) -> Team:
    """Get a single team by ID."""
    self.requires_login()

    team_api = f"{self.endpoints[TEAMS_ENDPOINT]}/{team_id}"

    return Team(**self.api_get(team_api))

  def create_team(self, team:Team) -> Team:
    """Create a new team."""
    self.requires_login()

    teams_api = self.endpoints[TEAMS_ENDPOINT]

    return Team(**self.api_post(teams_api, team))

  def update_team(self, team:Team) -> Team:
    """Update an existing team."""
    self.requires_login()

    assert team and team.id

    team_api = f"{self.endpoints[TEAMS_ENDPOINT]}/{team.id}"

    return Team(**self.api_put(team_api, team))

  def delete_team(self, team_id:str) -> str:
    """Delete a team."""
    self.requires_login()

    team_api = f"{self.endpoints[TEAMS_ENDPOINT]}/{team_id}"

    return self.api_delete(team_api)

  # --- Team Members ---

  def get_team_members(self, team_id:str) -> List[TeamMember]:
    """Get all members of a team."""
    self.requires_login()

    members_api = f"{self.endpoints[TEAMS_ENDPOINT]}/{team_id}/{MEMBERS_ENDPOINT}"

    result = self.api_get(members_api)
    if result is None:
      return []
    ta = TypeAdapter(List[TeamMember])
    return ta.validate_python(result)

  def add_team_member(self, team_id:str, user_id:str, role_id:str=None) -> TeamMember:
    """Add a member to a team."""
    self.requires_login()

    members_api = f"{self.endpoints[TEAMS_ENDPOINT]}/{team_id}/{MEMBERS_ENDPOINT}"

    member = AddTeamMember(user_id=user_id, role_id=role_id)

    return TeamMember(**self.api_post(members_api, member))

  def remove_team_member(self, team_id:str, member_id:str) -> str:
    """Remove a member from a team."""
    self.requires_login()

    member_api = f"{self.endpoints[TEAMS_ENDPOINT]}/{team_id}/{MEMBERS_ENDPOINT}/{member_id}"

    return self.api_delete(member_api)

  def update_team_member_role(self, team_id:str, member_id:str, role_id:str) -> TeamMember:
    """Update the role of a team member."""
    self.requires_login()

    role_api = f"{self.endpoints[TEAMS_ENDPOINT]}/{team_id}/{MEMBERS_ENDPOINT}/{member_id}/role"

    role_update = UpdateMemberRole(role_id=role_id)

    return TeamMember(**self.api_put(role_api, role_update))

  # --- Team Logo ---

  def upload_team_logo(self, team_id:str, folder:str="data", filename:str="logo.jpg") -> Team:
    """Upload a logo for a team."""
    self.requires_login()

    if filename.endswith("jpg"):
      content_type = "image/jpg"
    elif filename.endswith("jpeg"):
      content_type = "image/jpeg"
    elif filename.endswith("png"):
      content_type = "image/png"
    else:
      content_type = "image/jpeg"

    logo_api = f"{self.endpoints[TEAMS_ENDPOINT]}/{team_id}/{LOGO_ENDPOINT}"

    return Team(**self.upload(logo_api, folder, filename, content_type))

  def get_team_logo(self, team_id:str, download_location:str):
    """Download the logo for a team."""
    self.requires_login()

    logo_api = f"{self.endpoints[TEAMS_ENDPOINT]}/{team_id}/{LOGO_ENDPOINT}"

    return self.api_download(logo_api, download_location)

  def delete_team_logo(self, team_id:str) -> str:
    """Delete the logo of a team."""
    self.requires_login()

    logo_api = f"{self.endpoints[TEAMS_ENDPOINT]}/{team_id}/{LOGO_ENDPOINT}"

    return self.api_delete(logo_api)

  # --- Roles & Permissions (RBAC) ---

  def get_roles(self) -> List[Role]:
    """Get all roles."""
    self.requires_login()

    roles_api = self.endpoints[ROLES_ENDPOINT]

    result = self.api_get(roles_api)
    if result is None:
      return []
    ta = TypeAdapter(List[Role])
    return ta.validate_python(result)

  def get_role(self, role_id:str) -> Role:
    """Get a single role by ID."""
    self.requires_login()

    role_api = f"{self.endpoints[ROLES_ENDPOINT]}/{role_id}"

    return Role(**self.api_get(role_api))

  def create_role(self, role:Role) -> Role:
    """Create a new role."""
    self.requires_login()

    roles_api = self.endpoints[ROLES_ENDPOINT]

    return Role(**self.api_post(roles_api, role))

  def update_role(self, role:Role) -> Role:
    """Update an existing role."""
    self.requires_login()

    assert role and role.id

    role_api = f"{self.endpoints[ROLES_ENDPOINT]}/{role.id}"

    return Role(**self.api_put(role_api, role))

  def delete_role(self, role_id:str) -> str:
    """Delete a role."""
    self.requires_login()

    role_api = f"{self.endpoints[ROLES_ENDPOINT]}/{role_id}"

    return self.api_delete(role_api)

  def get_permissions(self) -> List[PermissionInfo]:
    """Get all available permissions from the API."""
    self.requires_login()

    permissions_api = self.endpoints[PERMISSIONS_ENDPOINT]

    result = self.api_get(permissions_api)
    if result is None:
      return []
    ta = TypeAdapter(List[PermissionInfo])
    return ta.validate_python(result)

  def get_current_user_context(self) -> UserContext:
    """Get the current user's context including organizations, roles, and permissions."""
    self.requires_login()

    context_api = f"{self.endpoints[ME_ENDPOINT]}/context"

    return UserContext(**self.api_get(context_api))

  # --- Dataset Higher level helper methods ---

  def add_columns_structured_dataset_version(self, dataset_version:DatasetVersion, column_names:List, csv_separator:str=",") -> DatasetVersion:
    if column_names:
        config = {
          "column_names": csv_separator.join(column_names),
          "csv_separator": csv_separator
        }
        dataset_version.config = json.dumps(config)
    
    return self.update_dataset_version(dataset_version.dataset_id, dataset_version)

  def create_structured_dataset_item(self, dataset_version:DatasetVersion, dataset_split:DatasetSplit, item:dict) -> DatasetItem:
    self.requires_login()

    try:
        config = json.loads(dataset_version.config)
        csv_separator = config["csv_separator"]
        columns = config["column_names"].split(csv_separator)
    except:
        raise Exception(f"Could not load version config: {dataset_version.config}")
    
    line_str = ""
    for idx, column in enumerate(columns):
        line_str += str(item[column])
        if idx < len(columns) - 1:
            line_str += csv_separator
    
    di = DatasetItem(
        splits=[dataset_split],
        text=line_str
    )

    di = self.create_dataset_item(dataset_version.dataset_id, dataset_version.id, di)
    return di

  def get_structured_dataset_item(self, dataset_id:str, dataset_version_id:str, item_id:str)  -> dict:
    self.requires_login()

    di = self.get_dataset_item(dataset_id, dataset_version_id, item_id)

    dataset_version = self.get_dataset_version(dataset_id, dataset_version_id)

    try:
        config = json.loads(dataset_version.config)
        csv_separator = config["csv_separator"]
        columns = config["column_names"].split(csv_separator)
    except:
        raise Exception(f"Could not load version config: {dataset_version.config}")

    line_items = di.text.split(csv_separator)

    item = {}
    
    for idx, column in enumerate(columns):
        item[column] = line_items[idx]
    
    return item

  # Convenience methods

  def get_apikey(self) -> str:
    return self.apikey
  
  def random_color(self) -> str:
    r = random.randint(0,255)
    g = random.randint(0,255)
    b = random.randint(0,255)
    rgb = (r,g,b)

    return '#%02x%02x%02x' % rgb

  # Convenience

  ## Tabular / Structured
  def read_df(self, folder:str, filename:str, extension=".csv", separator=",", **kwargs):
    import pandas as pd
    fullpath = f"{folder}/{filename}{extension}"
    return pd.read_csv(fullpath, sep=separator, **kwargs)

  def download_df(self,
      dataset_id:str=None,
      dataset_version_id:str=None,
      download_folder:str="tmp",
      separator=",",
      **kwargs
          ):

    # download dataset version
    self.download_dataset(dataset_id, dataset_version_id , extract_to_folder=download_folder)
    # load dataset to df

    df = self.read_df(download_folder, dataset_version_id, separator=separator, **kwargs)

    return df

  def upload_df(self,
      df:pd.DataFrame=None, 
      dataset_id=None, 
      name="my_dataset_version", 
      keep_index=False, 
      index_label="index",
      separator=",", 
      split_column="split",
      label_column="labels", 
      multi_label=False,
      label_separator=" "
  ) -> DatasetVersion:
    if not dataset_id:
        dataset = Dataset(
            name=name,
            content_type= DatasetContentType.TABULAR,
            multi_label= multi_label,
            default_splits= False
        )
        dataset = self.create_dataset(dataset)
        dataset_id = dataset.id
        ds_version = dataset.versions[0]
        ds_version_id = ds_version.id
    else:
        ds_version = DatasetVersion(
            name=name,
            dataset_id=dataset_id
        )
        ds_version = self.create_dataset_version(dataset_id, ds_version)
        ds_version_id = ds_version.id

    name = name.lower().replace("/", "_")
    fn = f"{name}.csv"
    df.to_csv(fn, index=keep_index, index_label=index_label, sep=separator)

    # write config.json
    config = {
        "multi_label": multi_label,
        "split_column": split_column,
        "label_column": label_column,
        "label_separator": label_separator,
        "filename": fn,
        "csv_separator": separator
    }

    # check if there already is a config.json?
    json_object = json.dumps(config, indent=4)
    with open("config.json", "w") as outfile:
        outfile.write(json_object)

    zip_filename = f"{name}.zip"

    # create zip file
    compress_files(files=["config.json", fn], zip_filename=zip_filename)

    uploaded_version = self.upload_dataset_version(dataset_id, ds_version_id, folder=".", filename=zip_filename, format=DatasetFormat.CSV)

    os.remove("config.json")
    os.remove(zip_filename)
    os.remove(fn)

    return uploaded_version

  # Helpers

  def requires_login(self):
    if not self.is_logged_in():
      raise Exception("You need to be logged in for this.")

  def update_applications(self):
    self.applications = self.get_applications()

  def update_auth_header(self, username:str=None, apikey:str=None):
    if not username or not apikey:
      del self.headers["Authorization"]
      self.apikey = apikey
      self.user_id = None
      self.username = username
      self.backend = None
      self.applications = List[Application]

      return

    self.apikey = apikey
    
    self.headers = {
      "Authorization": f"{username}:{apikey}"
    }
  
  def is_logged_in(self):
    return "Authorization" in self.headers
  
  def delete_user(self):
    self.requires_login()

    users_api = self.endpoints[USERS_ENDPOINT] + "/" + self.user_id

    self.api_delete(users_api)

    self.logout()

  def crud_endpoint(self, endpoint:str) -> str:
    return f"{self.backend}{endpoint}"
  
  def find_value_for_item_name(self, job:Job, item_name:str, failover=None):
    item = self.find_job_item(job, "name", item_name)

    if item:
      return self.find_value_for_item_key(item)

    return failover
  
  def find_job_item(self, job:Job, item_key:str, item_value:Union[dict,Base]):
    for item in job.items:
      item = item.model_dump()
      if item_key in item:
        if item[item_key] == item_value:
          return item
    
    return None
  
  def find_value_for_item_key(self, item:Union[dict,Base]):
      try:
        value = item["value"]
      except:
        item = item.model_dump()
        value = item["value"]

      if item["value_type"] == ValueType.INT:
          return int(value)
      if item["value_type"] == ValueType.FLOAT:
          return float(value)
    
      if item["value_type"] == ValueType.NUMBER:
        try:
          return int(value)
        except:
          return float(value)
      
      if item["value_type"] == ValueType.BOOL:
        return True if value == 'true' or value == True else False
      
      return value

  def find_label_with_name(self, labels:List[Label], name:str) -> Union[Label, None]:
    return self.find_item_in_array(labels, "name", name, first_item=True, t=Label)
  
  def find_split_with_name(self, splits:List[DatasetSplit], name:str) -> Union[DatasetSplit, None]:
    return self.find_item_in_array(splits, "name", name, first_item=True, t=DatasetSplit)
  
  def find_item_in_array(self, ar, prop, value, first_item=False, t:Base=None) -> Union[Base, None]:
    #TODO: handle case of NOT FOUDN anything or empty ar (array)!!
    try:
      results = [i for i in ar if i[prop] == value]
    except:
      results = [i.model_dump() for i in ar if i.model_dump()[prop] == value]
    
    if not results:
      return None

    if first_item:
      if t:
        return t(**results[0])
      else:
        return results[0]
    
    if t:
      ta = TypeAdapter(t)
      return ta.validate_python(results)
    else:
      return results

  ## CRUD API methods

  def api_get(self, api:str, params:dict=None) -> str:
      r = requests.get(api, headers=self.headers, params=params)
      r.raise_for_status()
      return r.json()

  def api_post(self, api:str, data, params=None) -> str:
    data = json.dumps(data.model_dump())
    r = requests.post(api, data=data, headers=self.headers, params=params)
    r.raise_for_status()
    return r.json()

  def api_upload(self, api:str, data, headers) -> str:
    r = requests.post(api, data=data, headers=headers)
    r.raise_for_status()
    return r.json()
  
  def api_put(self, api:str, data) -> str:
    data = json.dumps(data.model_dump(), default=str)
    r = requests.put(api, data=data, headers=self.headers)
    r.raise_for_status()
    return r.json()
  
  def api_delete(self, api:str) -> dict:
    r = requests.delete(api, headers=self.headers)
    r.raise_for_status()
    # Handle empty response (204 No Content)
    if r.status_code == 204 or not r.text:
      return {}
    return r.json()

  def api_download(self, api:str, filename:str, params=None):
    r = requests.get(api, allow_redirects=True, headers=self.headers, params=params)
    r.raise_for_status()
    open(filename, "wb").write(r.content)
