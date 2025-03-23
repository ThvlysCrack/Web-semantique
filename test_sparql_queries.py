import json
import sys
import os
from sparql_utils import validate_sparql_query, execute_sparql_query, extract_results_for_display

def load_json_file(file_path):
    """Load a JSON file and return its contents."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def test_queries(results_file, output_file=None, limit=None, verbose=True):
    """Test each SPARQL query in the results file.
    
    Args:
        results_file (str): Path to the JSON file with SPARQL queries
        output_file (str, optional): Path to save test results
        limit (int, optional): Limit the number of queries to test
        verbose (bool): Whether to print progress and results
    """
    # Load the results file
    print(f"Loading queries from {results_file}...")
    queries = load_json_file(results_file)
    
    if isinstance(queries, list):
        total_queries = len(queries)
        print(f"Found {total_queries} entries in the file")
    else:
        print("Error: Expected a list of queries in the JSON file")
        return
    
    # Initialize results tracking
    test_results = []
    valid_count = 0
    error_count = 0
    executed_count = 0
    no_results_count = 0
    
    # Limit the number of queries to test if specified
    if limit and limit > 0 and limit < total_queries:
        queries = queries[:limit]
        print(f"Testing first {limit} queries...")
    
    # Test each query
    for i, entry in enumerate(queries):
        if i % 10 == 0 and verbose:
            print(f"Testing query {i+1}/{len(queries)}...")
        
        # Skip entries that are error messages (strings)
        if isinstance(entry, str):
            test_results.append({
                "index": i,
                "error": entry,
                "valid": False,
                "executed": False
            })
            error_count += 1
            continue
        
        # Extract the query
        question = entry.get("question", "No question")
        query = entry.get("sparql_query", None)
        
        if not query or "ERROR_MISSING" in query:
            test_results.append({
                "index": i,
                "question": question,
                "error": "Missing or incomplete query",
                "valid": False,
                "executed": False
            })
            error_count += 1
            continue
        
        # Validate the query
        is_valid, validation_message = validate_sparql_query(query)
        
        result = {
            "index": i,
            "question": question,
            "query": query,
            "valid": is_valid,
            "validation_message": validation_message
        }
        
        if is_valid:
            # Execute the query
            try:
                execution_results = execute_sparql_query(query)
                result["executed"] = execution_results["success"]
                
                if execution_results["success"]:
                    # Extract formatted results
                    formatted_results = extract_results_for_display(execution_results)
                    result["results"] = formatted_results
                    
                    # Check if results are empty
                    if len(formatted_results) == 1 and formatted_results[0] == "No results found":
                        result["valid"] = False
                        result["validation_message"] = "Query is syntactically valid but returns no results"
                        no_results_count += 1
                    else:
                        valid_count += 1
                        executed_count += 1
                else:
                    result["execution_error"] = execution_results["error"]
            except Exception as e:
                result["executed"] = False
                result["execution_error"] = str(e)
        else:
            result["executed"] = False
            error_count += 1
        
        test_results.append(result)
    
    # Print summary
    print("\nTest Summary:")
    print(f"Total queries: {len(queries)}")
    print(f"Valid queries with results: {valid_count} ({valid_count/len(queries)*100:.1f}%)")
    print(f"Successfully executed but no results: {no_results_count} ({no_results_count/len(queries)*100:.1f}%)")
    print(f"Successfully executed total: {executed_count + no_results_count} ({(executed_count + no_results_count)/len(queries)*100:.1f}%)")
    print(f"Errors/invalid: {error_count} ({error_count/len(queries)*100:.1f}%)")
    
    # Save results if output file specified
    if output_file:
        # Filter out:
        # 1. Results with "No results found"
        # 2. Entries with 'unknown' template errors
        # 3. Missing or incomplete queries
        # 4. Queries with validation message about returning no results
        filtered_results = [result for result in test_results if not (
            # Exclude "No results found"
            ("results" in result and 
             isinstance(result["results"], list) and 
             len(result["results"]) == 1 and 
             result["results"][0] == "No results found") or
            # Exclude unknown template errors
            (isinstance(result.get("error", ""), str) and 
             "Template ID 'unknown'" in result.get("error", "")) or
            # Exclude missing or incomplete queries
            (isinstance(result.get("error", ""), str) and 
             "Missing or incomplete query" in result.get("error", "")) or
            # Exclude queries that are valid but return no results
            (isinstance(result.get("validation_message", ""), str) and
             "Query is syntactically valid but returns no results" in result.get("validation_message", ""))
        )]
        
        print(f"Saving {len(filtered_results)} valid queries with results (excluded {len(test_results) - len(filtered_results)} invalid queries)")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_results, f, indent=2)
        print(f"Test results saved to {output_file}")
    
    return test_results

def main():
    """Main function to run the script."""
    # Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python test_sparql_queries.py <results_file.json> [output_file.json] [--limit N]")
        print("\nExample:")
        print("  python test_sparql_queries.py improved_results.json test_results.json --limit 10")
        sys.exit(1)
    
    results_file = sys.argv[1]
    output_file = None
    limit = None
    
    # Parse optional arguments
    for i in range(2, len(sys.argv)):
        if sys.argv[i] == "--limit" and i + 1 < len(sys.argv):
            try:
                limit = int(sys.argv[i + 1])
            except ValueError:
                print(f"Error: Limit must be an integer, got '{sys.argv[i + 1]}'")
                sys.exit(1)
        elif not sys.argv[i].startswith("--") and not output_file:
            output_file = sys.argv[i]
    
    # Run tests
    try:
        test_queries(results_file, output_file, limit)
    except FileNotFoundError as e:
        print(f"Error: File not found - {str(e)}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in input file")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 