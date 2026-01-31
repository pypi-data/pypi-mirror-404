import numpy as np
from typing import Any, Dict
from fastapi import HTTPException

def calculate_score(reference_output: Any, student_output: Any, comparison_info: Dict[str, Any], max_points: float) -> float:
    """
    Calculate score based on comparison between reference and student output.
    
    Args:
        reference_output: The expected output (any type)
        student_output: The student's output (any type)
        comparison_info: Dictionary containing comparison metadata
        max_points: Maximum points for this test
        
    Returns:
        Score (0.0 to max_points)
    """
    comparison_type = comparison_info.get("comparison_type", "isequal")
    
    if comparison_type == "isequal":
        # Simple equality check
        is_correct = reference_output == student_output
        return max_points if is_correct else 0.0
    
    elif comparison_type == "allclose":
        # Numpy array comparison with tolerance
        try:
            # Convert to numpy arrays
            ref_array = np.array(reference_output)
            student_array = np.array(student_output)
            
            # Extract tolerance parameters
            rtol = comparison_info.get("rtol", 1e-05)
            atol = comparison_info.get("atol", 1e-08)
            equal_nan = comparison_info.get("equal_nan", False)
            
            # Perform allclose comparison
            is_correct = np.allclose(ref_array, student_array, 
                                   rtol=rtol, atol=atol, equal_nan=equal_nan)
            return max_points if is_correct else 0.0
            
        except Exception as e:
            # If arrays can't be compared, they're not close
            return 0.0
        
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported comparison type: {comparison_type}")
    
    return 0.0
