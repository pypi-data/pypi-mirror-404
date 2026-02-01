from pydantic import BaseModel, NonNegativeInt
from typing import List, Optional, Union
from enum import Enum
from enum import Enum as BaseEnum
from enum import EnumMeta as BaseEnumMeta

# -- Base Classes --

class EnumMeta(BaseEnumMeta):
    # https://stackoverflow.com/questions/43634618/how-do-i-test-if-int-value-exists-in-python-enum-without-using-try-catch
    def __contains__(self, item):
        return isinstance(item, self) or item in {
            v.value for v in self.__members__.values()
        }

    # https://stackoverflow.com/questions/29503339/how-to-get-all-values-from-python-enum-class
    def __str__(self):
        return ", ".join(c.value for c in self)

    def __repr__(self):
        return self.__str__()

class Enum(BaseEnum, metaclass=EnumMeta):
    def __str__(self):
        return str(self.value)

class Base(BaseModel):
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # model_config = ConfigDict(
    #         protected_namespaces=(),
    #         extra="ignore",
    #         arbitrary_types_allowed=False,
    # )
    class Config:  
        use_enum_values = True
        protected_namespaces=()
        extra="ignore"
        arbitrary_types_allowed=False


class NameBase(Base):
    name: str = None
    description: Optional[str] = ""


class Metric(NameBase):
    model_version_id: Optional[str] = None
    value: float = 0.0

# -- Enums --

class JobType(str, Enum):
    TRAINING    = "training"
    VALIDATION  = "validation"
    CONVERSION  = "conversion"

class JobStatus(str, Enum):
    WAITING     = "waiting"
    STARTED     = "started"
    FINISHED    = "finished"
    ERROR       = "error"


# TODO:  Merge to one status class
class WorkflowStatus(str, Enum):
    PENDING     = "pending"
    WAITING     = "waiting"
    STARTED     = "started"
    FINISHED    = "finished"
    ERROR       = "error"

class ValueType(str, Enum):
    FLOAT              = 'float'
    INT                = 'int'
    TEXT               = 'text'
    STRING_ARRAY       = 'string_array'
    BOOL               = 'boolean'
    NUMBER             = 'number' # will be deprecated
    MULTI              = 'multi'

class DatasetFormat(str, Enum):
    FOLDERS     = "folders"
    YOLO        = "yolo"
    CSV         = "csv"
    SPACY_NER   = "spacy-ner"

class DatasetContentType(str, Enum):
    IMAGES      = "images"
    TEXT        = "text"
    TABULAR     = "tabular"
    NER         = "ner"
    DOCUMENTS   = "documents"

class AssetType(str, Enum):
    PKL             = "pkl"
    PT              = "pt"
    MLMODEL         = "mlmodel"
    TFLITE          = "tflite"
    ONNX            = "onnx"
    ONNX_INT8       = "onnx_int8"
    LABELS          = "labels"
    NAMES           = "names"
    WEIGHTS         = "weights"
    CFG             = "cfg"
    CONVERSION_CFG  = "conversion_cfg"
    LOGO            = "logo"

class ApplicationType(str, Enum):
    IMAGE_CLASSIFICATION    = "image_classification"
    OBJECT_DETECTION        = "object_detection"
    TEXT_CLASSIFICATION     = "text_classification"
    LANGUAGE_MODEL          = "language_model"
    LLM                     = "llm"
    STRUCTURED              = "structured"
    NER                     = "ner"
    OCR                     = "ocr"
    SPEECH_TO_TEXT          = "speech_to_text"
    SEARCH                  = "search"

class Framework(str, Enum):
    PYTORCH                 = "pytorch"
    FASTAI                  = "fastai"
    YOLO                    = "yolo"
    XGBOOST                 = "xgboost"
    CATBOOST                = "catboost"
    LIGHTGBM                = "lightgbm"
    SPACY                   = "spacy"
    TESSERACT               = "tesseract"
    ONNX                    = "onnx"
    COREML                  = "coreml"
    TFLITE                  = "tflite"
    LLAMA_CPP_PYTHON        = "llama-cpp-python"
    WHISPER                 = "whisper"
    #PARAKEET                = "parakeet"
    INSANELY_FAST_WHISPER   = "insanely-fast-whisper"
    BM25S                   = "bm25s"
    UNSLOTH                 = "unsloth"

class WFNodeEntityType(str, Enum):
    MODEL                   = "model"
    DATASET                 = "dataset"


# -- Permissions (RBAC) --

class Permission(str, Enum):
    """
    Permission codes for Role-Based Access Control (RBAC).

    Permissions follow the pattern: resource:action
    Use these enum values when creating or updating roles to get
    autocomplete and type safety.

    Example:
        role = Role(
            name="Editor",
            permissions=[Permission.MODELS_CREATE, Permission.DATASETS_READ]
        )
    """
    # Wildcard - all permissions
    ALL = "*"

    # Models
    MODELS_LIST = "models:list"
    MODELS_READ = "models:read"
    MODELS_CREATE = "models:create"
    MODELS_UPDATE = "models:update"
    MODELS_DELETE = "models:delete"
    MODELS_UPLOAD = "models:upload"
    MODELS_SHARE = "models:share"
    MODELS_ALL = "models:*"

    # Model Versions
    MODEL_VERSIONS_CREATE = "model_versions:create"
    MODEL_VERSIONS_UPDATE = "model_versions:update"
    MODEL_VERSIONS_DELETE = "model_versions:delete"
    MODEL_VERSIONS_ALL = "model_versions:*"

    # Datasets
    DATASETS_LIST = "datasets:list"
    DATASETS_READ = "datasets:read"
    DATASETS_CREATE = "datasets:create"
    DATASETS_UPDATE = "datasets:update"
    DATASETS_DELETE = "datasets:delete"
    DATASETS_SHARE = "datasets:share"
    DATASETS_ALL = "datasets:*"

    # Dataset Versions
    DATASET_VERSIONS_CREATE = "dataset_versions:create"
    DATASET_VERSIONS_UPDATE = "dataset_versions:update"

    # Dataset Labels
    DATASET_LABELS_LIST = "dataset_labels:list"
    DATASET_LABELS_READ = "dataset_labels:read"
    DATASET_LABELS_CREATE = "dataset_labels:create"
    DATASET_LABELS_UPDATE = "dataset_labels:update"

    # Dataset Splits
    DATASET_SPLITS_CREATE = "dataset_splits:create"
    DATASET_SPLITS_UPDATE = "dataset_splits:update"

    # Dataset Items
    DATASET_ITEMS_LIST = "dataset_items:list"
    DATASET_ITEMS_READ = "dataset_items:read"
    DATASET_ITEMS_CREATE = "dataset_items:create"
    DATASET_ITEMS_UPDATE = "dataset_items:update"

    # Annotations
    ANNOTATIONS_CREATE = "annotations:create"
    ANNOTATIONS_UPDATE = "annotations:update"
    ANNOTATIONS_DELETE = "annotations:delete"
    ANNOTATIONS_ALL = "annotations:*"

    # Inferences
    INFERENCES_LIST = "inferences:list"
    INFERENCES_READ = "inferences:read"
    INFERENCES_CREATE = "inferences:create"
    INFERENCES_UPDATE = "inferences:update"
    INFERENCES_ALL = "inferences:*"

    # Jobs
    JOBS_LIST = "jobs:list"
    JOBS_READ = "jobs:read"
    JOBS_CREATE = "jobs:create"
    JOBS_UPDATE = "jobs:update"
    JOBS_DELETE = "jobs:delete"
    JOBS_ALL = "jobs:*"

    # Workflows
    WORKFLOWS_LIST = "workflows:list"
    WORKFLOWS_READ = "workflows:read"
    WORKFLOWS_CREATE = "workflows:create"
    WORKFLOWS_UPDATE = "workflows:update"
    WORKFLOWS_DELETE = "workflows:delete"
    WORKFLOWS_EXECUTE = "workflows:execute"
    WORKFLOWS_ALL = "workflows:*"

    # Workflow Executions
    WORKFLOW_EXECUTIONS_LIST = "workflow_executions:list"
    WORKFLOW_EXECUTIONS_READ = "workflow_executions:read"
    WORKFLOW_EXECUTIONS_ALL = "workflow_executions:*"

    # Graphs
    GRAPHS_LIST = "graphs:list"
    GRAPHS_READ = "graphs:read"
    GRAPHS_CREATE = "graphs:create"
    GRAPHS_UPDATE = "graphs:update"
    GRAPHS_DELETE = "graphs:delete"
    GRAPHS_ALL = "graphs:*"

    # Post Processors
    POST_PROCESSORS_LIST = "post_processors:list"
    POST_PROCESSORS_READ = "post_processors:read"
    POST_PROCESSORS_CREATE = "post_processors:create"
    POST_PROCESSORS_UPDATE = "post_processors:update"
    POST_PROCESSORS_DELETE = "post_processors:delete"
    POST_PROCESSORS_ALL = "post_processors:*"

    # Organizations
    ORGANIZATIONS_LIST = "organizations:list"
    ORGANIZATIONS_READ = "organizations:read"
    ORGANIZATIONS_CREATE = "organizations:create"
    ORGANIZATIONS_UPDATE = "organizations:update"
    ORGANIZATIONS_DELETE = "organizations:delete"
    ORGANIZATIONS_MANAGE_MEMBERS = "organizations:manage_members"

    # Projects
    PROJECTS_LIST = "projects:list"
    PROJECTS_READ = "projects:read"
    PROJECTS_CREATE = "projects:create"
    PROJECTS_UPDATE = "projects:update"
    PROJECTS_DELETE = "projects:delete"
    PROJECTS_ALL = "projects:*"

    # Teams
    TEAMS_LIST = "teams:list"
    TEAMS_READ = "teams:read"
    TEAMS_CREATE = "teams:create"
    TEAMS_UPDATE = "teams:update"
    TEAMS_DELETE = "teams:delete"
    TEAMS_ALL = "teams:*"

    # Roles
    ROLES_LIST = "roles:list"
    ROLES_READ = "roles:read"
    ROLES_CREATE = "roles:create"
    ROLES_UPDATE = "roles:update"
    ROLES_DELETE = "roles:delete"

    # Permissions
    PERMISSIONS_LIST = "permissions:list"


# -- Shares --

class Shareable(NameBase):
    user_id: Optional[str] = None
    notes: Optional[str] = None
    has_logo: Optional[bool] = False
    logo: Optional[str] = ""
    public: Optional[bool] = False
    shared_with_me: Optional[bool] = False


class Share(Base):
    email: str
    entity_type: str
    entity_id: str
    without_invite: Optional[bool] = True

# -- Models --

class Model(Shareable):
    active_version_id: Optional[str] = ""
    can_inference: Optional[bool] = False
    kind: Optional[str] = ""
    config: Optional[str] = ""
    application_id: Optional[str] = ""
    has_ml_model: Optional[bool] = False
    has_onnx_model: Optional[bool] = False
    has_onnx_int8_model: Optional[bool] = False
    has_tflite_model: Optional[bool] = False
    has_labels_file: Optional[bool] = False
    auto_convert: Optional[bool] = True
    privacy_enabled: Optional[bool] = False


class ModelVersion(NameBase):
    model_id: Optional[str] = None
    user_id: Optional[str] = ""
    can_inference: Optional[bool] = False
    has_logo: Optional[bool] = False
    config: Optional[str] = ""
    application_id: str
    version: Optional[str] = ""
    version_number: Optional[int] = None
    has_ml_model: Optional[bool] = False
    has_onnx_model: Optional[bool] = False
    has_onnx_int8_model: Optional[bool] = False
    has_tflite_model: Optional[bool] = False
    has_labels_file: Optional[bool]= False
    dataset_id: Optional[str] = ""
    dataset_version_id: Optional[str] = ""
    job_id: Optional[str] = ""
    metrics: Optional[List[Metric]] = []


# -- Datasets --

class Label(NameBase):
    user_id: Optional[str] = ""
    version_id: str
    color: Optional[str] = ""
    index: Optional[int] = 0
    shortcut: Optional[str] = ""


class LabelStat(Base):
    label_id: str
    split_id: str
    count: Optional[NonNegativeInt] = 0
    annotation_count: Optional[NonNegativeInt] = 0
    item_count: Optional[NonNegativeInt] = 0


class Annotation(Base):
    label_id: str
    item_id: str
    split_id: str
    coordinates: Optional[str] = ""
    user_id: Optional[str] = ""


class DatasetSplit(NameBase):
    user_id: Optional[str] = ""
    version_id: str


class DatasetItem(NameBase):
    user_id: Optional[str] = ""
    text: Optional[str] = ""
    splits: Optional[List[DatasetSplit]] = []
    annotations: Optional[List[Annotation]] = []
    extension: Optional[str] = ""


class DatasetVersion(NameBase):
    labels: Optional[List[Label]] = []
    user_id: Optional[str] = ""
    dataset_id: str
    splits: Optional[List[DatasetSplit]] = []
    default_split: Optional[str] = ""
    config: Optional[str] = ""


class Dataset(Shareable):
    versions: Optional[List[DatasetVersion]] = []
    multi_label: bool = False
    default_splits: bool = False
    content_type: Union[str,DatasetContentType]


# -- Jobs --

class JobItem(NameBase):
    job_id: Optional[str] = None
    default_value: Optional[str] = ""
    value_type: Union[ValueType, str]
    label: str
    value: Optional[str] = ""

class Job(NameBase):
    job_type: Optional[JobType] 
    application_id: Optional[str] = ""
    status: Optional[JobStatus] 
    status_message: Optional[str] = ""
    user_id: Optional[str] = ""
    cpu_start_time: Optional[str] = ""
    cpu_end_time: Optional[str] = ""
    gpu_start_time: Optional[str] = ""
    gpu_end_time: Optional[str] = ""
    agent_name: Optional[str] = ""
    dataset_id: Optional[str] = ""
    dataset_version_id: Optional[str] = ""
    model_id: Optional[str] = ""
    model_version_id: Optional[str] = ""
    start_model_id: Optional[str] = ""
    start_model_version_id: Optional[str] = ""
    items: Optional[List[JobItem]] = []


# -- Login --

class Registration(BaseModel):
    username: str
    email: str
    name: Optional[str]
    firstname: Optional[str]
    password: str


class Credentials(BaseModel):
    username: str
    password: str


class LoginReply(BaseModel):
    id: str
    username: str
    name: str
    email: str
    firstname: str
    apikey: str


class RegistrationError(BaseModel):
    message: Optional[str]
    severity: Optional[str]
    registration: Optional[Registration]


class User(Base):
    username: Optional[str]
    email: Optional[str]
    name: Optional[str]
    firstname: Optional[str]
    apikey: Optional[str]

# -- Inferences --

class TextInput(BaseModel):
    input_text: Optional[str]

class InferenceItem(Base):
    prediction: Optional[str]  = ""
    confidence: Optional[float] = 0.0
    inference_id: Optional[str] = ""
    coordinates: Optional[str] = ""


class Inference(NameBase):
    prediction: Optional[str] = "" # deprecated
    confidence: Optional[float] = 0.0# deprecated
    model_id: Optional[str] = ""
    model_version_id: Optional[str] = ""
    extension: Optional[str] = ""
    user_id: Optional[str] = ""
    error_reported: Optional[bool] = False
    error: Optional[str] = ""
    application_id: Optional[str] = ""
    inference_host: Optional[str] = ""
    inference_time: Optional[str] = ""
    end_to_end_time: Optional[str] = ""
    dataset_item_id: Optional[str] = ""
    result: Optional[str] = ""
    inference_items: Optional[List[InferenceItem]] = []
    hidden: Optional[bool] = False
    privacy_enabled: Optional[bool] = False
    config: Optional[str] = ""


class AddInferences(BaseModel):
    keep_annotations: bool = True
    inferences: List[Inference] = []

# -- Applications --


class Application(NameBase):
    base_framework: Optional[str]
    base_framework_version: Optional[str]
    framework: Optional[str]
    framework_version: Optional[str]
    application: Optional[str]
    inference_host: Optional[str]
    can_convert_to_onnx: Optional[bool]
    can_convert_to_tensorflow: Optional[bool]
    can_convert_to_tflite: Optional[bool]
    continual_training: Optional[bool]
    has_embedding_support: Optional[bool]
    has_labels_file: Optional[bool]
    inference_extensions: Optional[str]



# -- Workflows --

# -- Workflows --

class WorkflowEdge(NameBase):
    user_id: Optional[str] = ""
    version_id: str
    begin_node_id: Optional[str] = ""
    end_node_id: Optional[str] = ""

class WorkflowNode(NameBase):
    entity_type: str = ""
    entity_id: str = ""
    entity_version_id: str = ""
    config: str = ""
    user_id: Optional[str] = ""
    version_id: str

class WorkflowVersion(NameBase):
    user_id: Optional[str] = ""
    workflow_id: str
    nodes: Optional[List[WorkflowNode]] = []
    edges: Optional[List[WorkflowEdge]] = []

class Workflow(Shareable):
    active_version_id: Optional[str] = ""
    versions: Optional[List[WorkflowVersion]] = []

class WorkflowNodeExecution(Base):
    run_id: str
    node_id: str
    status: Optional[WorkflowStatus] = "" # TODO enum?
    started_at: Optional[str] = ""
    completed_at: Optional[str] = ""
    inference_id: Optional[str] = ""
    inference: Optional[Inference] = None
    dataset_id: Optional[str] = "" # REMOVE?
    dataset_version_id: Optional[str] = "" # REMOVE?
    dataset_item_id: Optional[str] = "" # REMOVE?
    dataset_items: Optional[List[DatasetItem]] = []
    error: Optional[str] = ""

class WorkflowRun(Base):
    user_id: str
    workflow_id: str
    version_id:  str
    status: Optional[WorkflowStatus] = ""
    #input_data: Optional[str] = ""
    #output_dataset_id: Optional[str] = ""
    started_at: Optional[str] = ""
    completed_at: Optional[str] = ""
    error: Optional[str] = ""
    node_executions: Optional[List[WorkflowNodeExecution]]


# -- Post-Processors --

class PostProcessorModelType(str, Enum):
    STT             = "stt"
    STT_DIARIZATION = "stt-diarization"
    CLASSIFICATION  = "classification"
    DETECTION       = "detection"
    NER             = "ner"
    OCR             = "ocr"
    LLM             = "llm"

class PostProcessorOutputTarget(str, Enum):
    TEXT        = "text"
    ANNOTATIONS = "annotations"
    BOTH        = "both"

class PostProcessorJobStatus(str, Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"

class ExternalProvider(str, Enum):
    OPENAI    = "openai"
    ANTHROPIC = "anthropic"

class DatasetPostProcessor(Base):
    dataset_id: str
    name: str
    description: Optional[str] = ""
    enabled: Optional[bool] = True
    order: Optional[int] = 0

    # Internal model reference
    model_id: Optional[str] = None
    model_version: Optional[str] = None

    # External provider
    external_provider: Optional[str] = None
    external_model: Optional[str] = None
    external_config: Optional[str] = None

    # Processing configuration
    model_type: str
    output_target: Optional[str] = "text"
    auto_create_labels: Optional[bool] = False
    confidence_threshold: Optional[float] = 0.0

    # LLM-specific config
    prompt: Optional[str] = None

    user_id: Optional[str] = ""

class PostProcessorJob(NameBase):
    post_processor_id: str
    dataset_item_id: str
    dataset_id: str
    status: Optional[str] = "pending"
    attempts: Optional[int] = 0
    max_attempts: Optional[int] = 3
    error: Optional[str] = None
    result: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    user_id: Optional[str] = ""

class PostProcessorWithModel(NameBase):
    model_name: Optional[str] = None
    model_kind: Optional[str] = None
    is_external: Optional[bool] = False
    provider_name: Optional[str] = None
    model_type: Optional[str] = None

class PostProcessorJobWithDetails(NameBase):
    post_processor_name: Optional[str] = ""
    item_name: Optional[str] = ""

class CreatePostProcessorRequest(NameBase):
    name: str
    description: Optional[str] = ""
    enabled: Optional[bool] = True
    order: Optional[int] = 0
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    external_provider: Optional[str] = None
    external_model: Optional[str] = None
    external_config: Optional[str] = None
    model_type: str
    output_target: Optional[str] = "text"
    auto_create_labels: Optional[bool] = False
    confidence_threshold: Optional[float] = 0.0
    prompt: Optional[str] = None

class UpdatePostProcessorRequest(NameBase):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    order: Optional[int] = None
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    external_provider: Optional[str] = None
    external_model: Optional[str] = None
    external_config: Optional[str] = None
    model_type: Optional[str] = None
    output_target: Optional[str] = None
    auto_create_labels: Optional[bool] = None
    confidence_threshold: Optional[float] = None
    prompt: Optional[str] = None

class ItemJobStatus(NameBase):
    pending: Optional[int] = 0
    processing: Optional[int] = 0
    completed: Optional[int] = 0
    failed: Optional[int] = 0
    total: Optional[int] = 0

class ItemWithJobStatus(DatasetItem):
    job_status: Optional[ItemJobStatus] = None


# -- Workflow Executions --

class ExecutionStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    CANCELLED = "cancelled"

class InputMode(str, Enum):
    SINGLE = "single"
    BATCH  = "batch"

class DatasetOperation(str, Enum):
    LOOKUP  = "lookup"
    JOIN    = "join"
    FILTER  = "filter"
    ITERATE = "iterate"

class ExecutionProgress(NameBase):
    total_items: Optional[int] = 0
    processed_items: Optional[int] = 0
    failed_items: Optional[int] = 0
    current_node_id: Optional[str] = None
    current_node_idx: Optional[int] = 0
    total_nodes: Optional[int] = 0

class BatchInputConfig(NameBase):
    dataset_id: str
    dataset_version_id: str
    input_field: str
    filter_query: Optional[str] = None
    parallelism: Optional[int] = 1

class MatchConfig(NameBase):
    dataset_field: str
    match_value: str
    match_type: Optional[str] = "exact"

class FilterConfig(NameBase):
    condition: str
    max_items: Optional[int] = None

class IterateConfig(NameBase):
    item_variable: str
    parallelism: Optional[int] = 1

class DatasetInputConfig(NameBase):
    dataset_id: str
    dataset_version_id: str
    operation: Union[DatasetOperation, str]
    match_config: Optional[MatchConfig] = None
    filter_config: Optional[FilterConfig] = None
    iterate_config: Optional[IterateConfig] = None
    output_as: str
    output_fields: Optional[List[str]] = None

class NodeExecutionRecord(NameBase):
    node_id: str
    node_name: Optional[str] = ""
    entity_type: Optional[str] = ""
    status: Optional[str] = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output: Optional[dict] = None
    error: Optional[str] = None

class ExecutionResult(NameBase):
    dataset_item_id: Optional[str] = None
    input_value: Optional[str] = ""
    output: Optional[dict] = None
    node_outputs: Optional[dict] = None
    error: Optional[str] = None
    processed_at: Optional[str] = None

class ExecutionContext(NameBase):
    execution_id: str
    user_id: Optional[str] = ""
    variables: Optional[dict] = None
    input: Optional[str] = ""
    input_file_path: Optional[str] = None
    input_file_name: Optional[str] = None
    current_node: Optional[str] = None

class WorkflowExecution(NameBase):
    workflow_id: str
    workflow_version_id: Optional[str] = None
    user_id: Optional[str] = ""

    # Execution status
    status: Optional[Union[ExecutionStatus, str]] = "pending"
    progress: Optional[ExecutionProgress] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

    # Input configuration
    input_mode: Optional[Union[InputMode, str]] = "single"
    single_input: Optional[str] = None
    input_file_path: Optional[str] = None
    input_file_name: Optional[str] = None
    batch_config: Optional[BatchInputConfig] = None

    # Results
    results: Optional[List[ExecutionResult]] = None
    node_executions: Optional[List[NodeExecutionRecord]] = None

class WorkflowExecutionRequest(NameBase):
    input_mode: Union[InputMode, str]
    single_input: Optional[str] = None
    batch_config: Optional[BatchInputConfig] = None

class WorkflowExecutionResponse(NameBase):
    execution_id: str
    status: Union[ExecutionStatus, str]
    progress: Optional[ExecutionProgress] = None
    message: Optional[str] = None


# -- Graphs (DGraph) --

class GraphMetric(NameBase):
    graph_version_id: str
    metric_type: Optional[str] = ""  # "centrality", "clustering", "density"
    value: Optional[float] = 0.0
    user_id: Optional[str] = ""

class GraphVersion(NameBase):
    user_id: Optional[str] = ""
    graph_id: str
    version: Optional[str] = ""
    version_number: Optional[int] = 0

    # DGraph specific
    space_name: Optional[str] = ""
    graph_schema: Optional[str] = ""
    node_count: Optional[int] = 0
    edge_count: Optional[int] = 0

    # Configuration
    config: Optional[str] = ""

    # Metrics
    metrics: Optional[List[GraphMetric]] = []

class Graph(Shareable):
    active_version_id: Optional[str] = None
    kind: Optional[str] = ""  # "property", "knowledge", "social", "network"
    config: Optional[str] = ""  # JSON config
    schema_config: Optional[str] = ""  # Node/edge type definitions
    versions: Optional[List[GraphVersion]] = []

class NodeProperty(NameBase):
    node_type_id: str
    user_id: Optional[str] = ""
    property_type: Optional[str] = "string"  # "string", "int", "float", "bool", "datetime"
    required: Optional[bool] = False
    default_value: Optional[str] = ""

class EdgeProperty(NameBase):
    edge_type_id: str
    user_id: Optional[str] = ""
    property_type: Optional[str] = "string"
    required: Optional[bool] = False
    default_value: Optional[str] = ""

class NodeType(NameBase):
    schema_id: str
    user_id: Optional[str] = ""
    properties: Optional[List[NodeProperty]] = []
    color: Optional[str] = ""
    icon: Optional[str] = ""

class EdgeType(NameBase):
    schema_id: str
    user_id: Optional[str] = ""
    properties: Optional[List[EdgeProperty]] = []
    color: Optional[str] = ""
    directed: Optional[bool] = True

class GraphSchema(NameBase):
    graph_version_id: str
    user_id: Optional[str] = ""
    node_types: Optional[List[NodeType]] = []
    edge_types: Optional[List[EdgeType]] = []

class GraphQuery(NameBase):
    graph_id: str
    graph_version_id: Optional[str] = None
    user_id: Optional[str] = ""
    query: Optional[str] = ""  # DQL query
    query_type: Optional[str] = "dql"  # "dql", "graphql"
    public: Optional[bool] = False
    favorite: Optional[bool] = False

class GraphNode(NameBase):
    uid: Optional[str] = None
    external_id: Optional[str] = None
    type: str
    properties: Optional[dict] = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class GraphEdge(NameBase):
    uid: Optional[str] = None
    source_uid: str
    target_uid: str
    type: str
    properties: Optional[dict] = {}

class BulkNodeRequest(NameBase):
    nodes: List[GraphNode]

class BulkEdgeRequest(NameBase):
    edges: List[GraphEdge]

class GraphExportConfig(NameBase):
    format: Optional[str] = "json"  # "graphml", "gexf", "json", "csv"
    include_schema: Optional[bool] = True
    node_types: Optional[List[str]] = []
    edge_types: Optional[List[str]] = []
    max_nodes: Optional[int] = 0
    max_edges: Optional[int] = 0

class GraphImportConfig(NameBase):
    format: Optional[str] = "json"
    node_file: Optional[str] = None
    edge_file: Optional[str] = None
    column_mappings: Optional[dict] = {}
    create_schema: Optional[bool] = True
    separator: Optional[str] = ","


# -- Organizations (RBAC) --

class Organization(Shareable):
    slug: Optional[str] = None
    website: Optional[str] = None
    owner_id: Optional[str] = None


class OrganizationMember(Base):
    organization_id: str
    user_id: str
    role_id: Optional[str] = None
    role_name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    firstname: Optional[str] = None
    name: Optional[str] = None


class OrganizationInvite(BaseModel):
    email: str
    role_id: Optional[str] = None


class UpdateMemberRole(BaseModel):
    role_id: str


# -- Projects (RBAC) --

class Project(Shareable):
    organization_id: Optional[str] = None
    team_id: Optional[str] = None
    slug: Optional[str] = None


class ProjectMember(Base):
    project_id: str
    user_id: str
    role_id: Optional[str] = None
    role_name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    firstname: Optional[str] = None
    name: Optional[str] = None


class AddProjectMember(BaseModel):
    user_id: str
    role_id: Optional[str] = None


class ProjectResource(Base):
    project_id: str
    resource_type: str  # "model", "dataset", "workflow", "graph"
    resource_id: str
    resource_name: Optional[str] = None


class AssignProjectResource(BaseModel):
    resource_type: str
    resource_id: str


# -- Teams (RBAC) --

class Team(Shareable):
    organization_id: Optional[str] = None
    slug: Optional[str] = None


class TeamMember(Base):
    team_id: str
    user_id: str
    role_id: Optional[str] = None
    role_name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    firstname: Optional[str] = None
    name: Optional[str] = None


class AddTeamMember(BaseModel):
    user_id: str
    role_id: Optional[str] = None


# -- Roles & Permissions (RBAC) --

class PermissionInfo(NameBase):
    """
    Permission information returned from the API.

    This is the Pydantic model for API responses. For setting permissions
    on roles, use the Permission enum instead.
    """
    code: Optional[str] = None
    category: Optional[str] = None


class Role(NameBase):
    organization_id: Optional[str] = None
    scope: Optional[str] = "organization"  # 'organization' or 'system'
    slug: Optional[str] = None
    permissions: Optional[List[Union[Permission, str]]] = []  # List of permission codes (enum or string)
    permission_list: Optional[List[Union[Permission, str]]] = None  # Alternative field for permissions
    is_system_role: Optional[bool] = False
    is_system: Optional[bool] = False  # Backend uses this field name


class UserContext(Base):
    user_id: str
    organizations: Optional[List[Organization]] = []
    current_organization_id: Optional[str] = None
    current_organization: Optional[Organization] = None
    roles: Optional[List[Role]] = []
    permissions: Optional[List[str]] = []


