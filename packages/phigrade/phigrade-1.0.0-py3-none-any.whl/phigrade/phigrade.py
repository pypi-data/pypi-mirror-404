import os
import inspect
import requests
from dataclasses import dataclass
from typing import Optional, Callable, Any
from omegaconf import OmegaConf
from phigrade.server import Server as LocalServer
from phigrade.gradescope_output import write_gradescope_json_file
import uuid
import numpy as np

_config = None
_local_server = None
_results = []
_submission_id = None
_utest_attempt_ids = {}
_utest_definition_cache = set()

@dataclass
class PhiGradeConfig:
    """Loads phigrade test configuration from a YAML file using OmegaConf."""
    course_id: str
    assignment_id: str
    use_local_server: bool = False
    server_url: Optional[str] = None
    api_key: Optional[str] = None
    teacher_mode: bool = False
    timeout_seconds: int = 2
    local_server_db_file: Optional[str] = None
    gradescope_json_file: Optional[str] = None
    submission_files: Optional[list] = None

    @classmethod
    def _find_config_file(cls, test_func: Callable, config_filename: str = 'phigrade.yaml') -> str:
        """Find the configuration file relative to the test function."""
        # Get the directory of this test file
        test_file = inspect.getfile(inspect.getmodule(test_func))
        test_file_dir = os.path.dirname(os.path.abspath(test_file))
        # Construct the full path to the YAML file
        return os.path.join(test_file_dir, config_filename)
    
    @classmethod
    def from_test_func_file(cls, test_func: Callable, config_filename: str = 'phigrade.yaml') -> 'PhiGradeConfig':
        """Load configuration from a YAML file relative to the test function."""
        config_file = cls._find_config_file(test_func, config_filename)
        return cls.from_file(config_file)

    @classmethod
    def from_file(cls, config_file: str) -> 'PhiGradeConfig':
        """Load configuration from YAML file."""
        try:
            # Load YAML configuration with OmegaConf
            config = OmegaConf.load(config_file)
            
            # Convert to structured config with validation
            structured_config = OmegaConf.structured(cls)
            merged_config = OmegaConf.merge(structured_config, config)
            
            # Validate required fields based on mode
            use_local_server = OmegaConf.select(merged_config, 'use_local_server')
            if use_local_server is False:
                required_keys = ['server_url', 'api_key', 'course_id', 'assignment_id']
                for key in required_keys:
                    if not OmegaConf.select(merged_config, key):
                        raise ValueError(f"Required key '{key}' not found in {config_file}")
            else:
                required_keys = ['course_id', 'assignment_id']
                for key in required_keys:
                    if not OmegaConf.select(merged_config, key):
                        raise ValueError(f"Required key '{key}' not found in {config_file}")

            # Ensure the local_server_db_file is set if using local server
            if use_local_server:
                local_server_db_file = OmegaConf.select(merged_config, 'local_server_db_file')
                if not local_server_db_file:
                    # Use the directory of the config file
                    merged_config.local_server_db_file = os.path.join(os.path.dirname(config_file), 'phigrade_db.json')

            # Convert OmegaConf to dataclass instance
            return cls(**OmegaConf.to_container(merged_config))
            
        except Exception as e:
            raise ValueError(f"Error loading configuration from {config_file}: {e}")

def load_phigrade_config(test_func: Callable) -> PhiGradeConfig:
    global _config
    if not _config:
        _config = PhiGradeConfig.from_test_func_file(test_func)
    return _config
    
def _start_local_server(config: PhiGradeConfig) -> None:
    global _local_server
    if config.use_local_server and not _local_server:
        _local_server = LocalServer()
        _local_server.start(local_db_file=config.local_server_db_file)
        config.server_url = f"http://localhost:{_local_server.port}"

def _create_submission(config: PhiGradeConfig) -> int:
    """Create a submission and upload code files, returning submission_id"""
    global _submission_id
    
    if _submission_id is not None:
        return _submission_id
    
    # Read code files
    code_files = {}
    if config.submission_files:
        for file_path in config.submission_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                code_files[file_path] = f.read()
    
    # Prepare submission payload
    payload = {
        "code_files": code_files,
        "is_reference": config.teacher_mode
    }

    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if not config.use_local_server:
        headers["Authorization"] = f"Bearer {config.api_key}"

    # Choose endpoint based on teacher_mode
    if config.teacher_mode:
        endpoint = f"{config.server_url}/api/v1/courses/{config.course_id}/assignments/{config.assignment_id}/reference-submissions"
    else:
        endpoint = f"{config.server_url}/api/v1/courses/{config.course_id}/assignments/{config.assignment_id}/submissions"

    # Create submission
    response = requests.post(
        endpoint,
        json=payload,
        headers=headers,
        timeout=config.timeout_seconds
    )
    
    if response.status_code == 200:
        result = response.json()
        _submission_id = result["id"]
        print(f"Created submission {_submission_id}")
        return _submission_id
    else:
        response_data = response.json()
        raise Exception(f"Failed to create submission: {response_data.get('detail', response.text)}")
    
def weight(w: float) -> Callable:
    """
    Decorator to assign a weight to a unit test and store its identifiers.
    :param w: Weight of the unit test.
    """
    def decorator(func: Callable) -> Callable:
        func.is_utest = True
        func.utest_name = func.__name__
        func.module_name = func.__module__
        func.weight = w
        func.call_count = 0  # Initialize call count for tracking
        return func
    return decorator

def phigrade_allclose(system_output: np.ndarray, rtol=1e-05, atol=1e-08, equal_nan=False) -> None:
    """
    Check if the system output is close to the expected output within a tolerance.
    :param system_output: The output generated by the student's function, to be checked.
    :param rtol: Relative tolerance.
    :param atol: Absolute tolerance.
    :param equal_nan: Whether to consider NaN values as equal.
    """
    __tracebackhide__ = True  # <- pytest will hide frames in this function
    
    # Serialize the system output so it can be sent to the server
    if not isinstance(system_output, np.ndarray):
        raise TypeError("system_output must be a numpy ndarray")
    
    # Convert to list for JSON serialization
    output_data = system_output.tolist()
    
    # Prepare comparison info
    comparison_info = {
        "comparison_type": "allclose",
        "rtol": rtol,
        "atol": atol,
        "equal_nan": equal_nan
    }
    
    return _phigrade_compare(output_data, comparison_info)

def phigrade_isequal(system_output: Any) -> None:
    """
    Sends system output to server for grading or storing, using identifiers from @weight.
    :param system_output: The output generated by the student's function, to be checked or stored.
    """        
    __tracebackhide__ = True  # <- pytest will hide frames in this function

    # Prepare comparison info
    comparison_info = {"comparison_type": "isequal"}
    
    return _phigrade_compare(system_output, comparison_info)

def _phigrade_compare(output_data: Any, comparison_info: dict) -> None:
    __tracebackhide__ = True  # <- pytest will hide frames in this function

    # Traverse up the call stack to find the decorated unit test function
    test_func = None
    for frame_info in inspect.stack():
        func = frame_info.frame.f_globals.get(frame_info.function)
        if func and getattr(func, "is_utest", False):
            test_func = func
            break
    if not test_func:
        raise Exception("phigrade function must be called from within a function decorated with @weight")

    # Load the phigrade configuration
    config = load_phigrade_config(test_func)

    # Start the local server if in local mode and not already started
    _start_local_server(config)
    
    # Create submission if not already created
    _create_submission(config)

    # Retrieve identifiers and weight from the decorator attributes
    comparison_name = f"{test_func.utest_name}@{test_func.call_count}"
    test_func.call_count += 1  # Increment call count for unique comparison names
    utest_name = test_func.utest_name
    module_name = test_func.module_name
    weight = test_func.weight
    utest_key = (module_name, utest_name)

    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if not config.use_local_server:
        headers["Authorization"] = f"Bearer {config.api_key}"

    if config.teacher_mode and utest_key not in _utest_definition_cache:
        utest_payload = {
            "module_name": module_name,
            "utest_name": utest_name,
            "max_points": 1.0,
            "aggregation": "fail_fast",
            "num_comparisons": 0
        }
        utest_response = requests.post(
            f"{config.server_url}/api/v1/courses/{config.course_id}/assignments/{config.assignment_id}/utests",
            json=utest_payload,
            headers=headers,
            timeout=config.timeout_seconds
        )
        if utest_response.status_code not in (200, 201, 400):
            response_data = utest_response.json()
            raise Exception(f"Failed to create utest: {response_data.get('detail', utest_response.text)}")
        _utest_definition_cache.add(utest_key)

    attempt_id = _utest_attempt_ids.get(utest_key)
    if attempt_id is None:
        attempt_payload = {"module_name": module_name, "utest_name": utest_name}
        attempt_response = requests.post(
            f"{config.server_url}/api/v1/courses/{config.course_id}/assignments/{config.assignment_id}/submissions/{_submission_id}/utest-attempts",
            json=attempt_payload,
            headers=headers,
            timeout=config.timeout_seconds
        )
        if attempt_response.status_code != 200:
            response_data = attempt_response.json()
            raise Exception(f"Failed to create utest attempt: {response_data.get('detail', attempt_response.text)}")
        attempt_id = attempt_response.json()["id"]
        _utest_attempt_ids[utest_key] = attempt_id

    # Prepare the payload based on mode
    if config.teacher_mode:
        # Teacher mode: store reference comparison
        payload = {
            "module_name": module_name,
            "utest_name": utest_name,
            "comparison_name": comparison_name,
            "reference_output": output_data,
            "comparison_info": comparison_info,
            "points": weight,
            "weight": 1.0,  # Default weight for comparison
        }
        endpoint = (
            f"/api/v1/courses/{config.course_id}/assignments/{config.assignment_id}"
            f"/submissions/{_submission_id}/utest-attempts/{attempt_id}/ref-comparisons"
        )
    else:
        # Student mode: submit attempt comparison
        payload = {
            "module_name": module_name,
            "utest_name": utest_name,
            "comparison_name": comparison_name,
            "student_output": output_data,
        }
        endpoint = (
            f"/api/v1/courses/{config.course_id}/assignments/{config.assignment_id}"
            f"/submissions/{_submission_id}/utest-attempts/{attempt_id}/student-comparisons"
        )
    
    response = requests.post(f"{config.server_url}{endpoint}", json=payload, headers=headers, timeout=config.timeout_seconds)

    if config.gradescope_json_file:
        # Write the Gradescope JSON file after every test. Although this is slower, it removes the requirement for the test author to call write_gradescope_json_file manually.
        _results.append(response.json())
        write_gradescope_json_file(config.gradescope_json_file, _results)

    if response.status_code == 200:
        if not config.teacher_mode:  # Only parse comparison results in student mode
            result = response.json()
            if result.get("is_correct"):
                print(f"Comparison '{comparison_name}' in test '{utest_name}' passed.")
            else:
                print(f"Comparison '{comparison_name}' in test '{utest_name}' failed.")
                raise AssertionError(f"Comparison '{comparison_name}' failed with output: {result.get('student_output')}")
    else:
        response_data = response.json()
        raise Exception(f"Failed to communicate with the server: {response_data.get('detail', response.text)}")
