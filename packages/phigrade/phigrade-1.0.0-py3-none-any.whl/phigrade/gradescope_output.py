
def write_gradescope_json_file(out_file: str, results: list) -> None:
    """
    Writes the collected test results to a Gradescope-compatible JSON file.
    
    The output file will follow the following format. This method will include the per-test scores and 
    information and skip the global information when possible for simplicity.

    { "score": 44.0, // optional, but required if not on each test case below. Overrides total of tests if specified.
    "execution_time": 136, // optional, seconds
    "output": "Text relevant to the entire submission", // optional
    "output_format": "simple_format", // Optional output format settings, see "Output String Formatting" below
    "test_output_format": "text", // Optional default output format for test case outputs, see "Output String Formatting" below
    "test_name_format": "text", // Optional default output format for test case names, see "Output String Formatting" below
    "visibility": "after_due_date", // Optional visibility setting
    "stdout_visibility": "visible", // Optional stdout visibility setting
    "extra_data": {}, // Optional extra data to be stored
    "tests": // Optional, but required if no top-level score
        [
            {
                "score": 2.0, // optional, but required if not on top level submission
                "max_score": 2.0, // optional
                "status": "passed", // optional, see "Test case status" below
                "name": "Your name here", // optional
                "name_format": "text", // optional formatting for the test case name, see "Output String Formatting" below
                "number": "1.1", // optional (will just be numbered in order of array if no number given)
                "output": "Giant multiline string that will be placed in a <pre> tag and collapsed by default", // optional
                "output_format": "text", // optional formatting for the test case output, see "Output String Formatting" below
                "tags": ["tag1", "tag2", "tag3"], // optional
                "visibility": "visible", // Optional visibility setting
                "extra_data": {} // Optional extra data to be stored
            },
            // and more test cases...
        ],
    "leaderboard": // Optional, will set up leaderboards for these values
        [
        {"name": "Accuracy", "value": .926},
        {"name": "Time", "value": 15.1, "order": "asc"},
        {"name": "Stars", "value": "*****"}
        ]
    }
    """
    raise NotImplementedError("This method still doesn't handle multiple assertions correctly.")    

    import json
    
    # Initialize the Gradescope JSON structure
    gradescope_json = {
        "tests": []
    }
    
    total_score = 0.0
    total_max_score = 0.0
    
    # Group results from the same test case, and preserve order
    test_key_order = []
    grouped_results = {}
    for result in results:
        # Remove @0 or @1 or @2 etc. from the test name
        utest_name = result.get("utest_name", "test").split("@")[0]
        test_key = (result.get("module_name", "unknown"), utest_name)

        if test_key not in grouped_results:
            grouped_results[test_key] = []
            test_key_order.append(test_key)
        grouped_results[test_key].append(result)

    for test_key in test_key_order:
        # Process each test result
        for i, result in enumerate(grouped_results.get(test_key, [])):
            if "score" in result:  # Student mode result
                score = result.get("score", 0.0)
                is_correct = result.get("is_correct", False)
            
                # Try to determine max score from the weight or default to score if passed
                if is_correct and score > 0:
                    max_score = score
                else:
                    # For failed tests, we need to estimate max score
                    # This is a limitation without storing the original weight
                    max_score = 1.0  # Default fallback
                    raise NotImplementedError("Max score determination for failed tests is not implemented. Please run in teacher mode first to store reference weights.")
                
                test_case = {
                    "score": score,
                    "max_score": max_score,
                    "status": "passed" if is_correct else "failed",
                    "name": f"{result.get('module_name', 'unknown')}.{result.get('utest_name', 'test')}",
                    "number": str(i + 1),
                    "visibility": "visible"
                }
                
                # Add output information if test failed
                if not is_correct:
                    if 'utest_output' in result:
                        test_case["output"] = f"Test failed with output: {result.get('utest_output', 'No output available')}"
                    else:
                        test_case["output"] = f"Failed to communicate with the server: {result.get('detail', 'No output available')}"

                gradescope_json["tests"].append(test_case)
                total_score += score
                total_max_score += max_score
                
            elif "points" in result:  # Reference mode result (teacher mode)
                # In teacher mode, we just store the reference but don't create test cases
                # since these are not student submissions
                pass
    # Write to file
    with open(out_file, 'w') as f:
        json.dump(gradescope_json, f, indent=2)
    print(f"Wrote Gradescope JSON results to {out_file} with total score {total_score}/{total_max_score}")