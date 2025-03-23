import json
import sys
import os
from sparql_utils import validate_sparql_query, execute_sparql_query, extract_results_for_display
from generate_sparql import generate_sparql_query

def load_json_file(file_path):
    """Load a JSON file and return its contents."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def process_single_query(query_dict):
    """
    Process a single query dictionary in the format from mapped_classified_questions.json
    
    Args:
        query_dict (dict): A single query dictionary with question, template_id, and mapping
        
    Returns:
        dict: Results of testing the query
    """
    # Load the templates
    templates = load_json_file('template_map.json')
    
    # Use the generate_sparql_query function to create a SPARQL query
    query_result = {}
    
    # Check if this is a correctly structured query dict
    if not isinstance(query_dict, dict) or not all(key in query_dict for key in ['question', 'template_id', 'mapping']):
        return {
            "error": "Invalid query dictionary format. Required keys: question, template_id, mapping",
            "valid": False,
            "executed": False
        }
    
    # Generate the SPARQL query using the same logic as in generate_sparql.py
    try:
        # Create a list with just this query to match the function's expected input
        query_list = [query_dict]
        # Generate the query (use index 0 since we only have one query)
        query_result = generate_sparql_query(0, query_list, templates)
    except Exception as e:
        return {
            "question": query_dict.get("question", "Unknown question"),
            "error": f"Error generating SPARQL query: {str(e)}",
            "valid": False,
            "executed": False
        }
    
    # Check if the query generation had an error
    if isinstance(query_result, str) and "Error:" in query_result:
        return {
            "question": query_dict.get("question", "Unknown question"),
            "error": query_result,
            "valid": False,
            "executed": False
        }
    
    # Extract the SPARQL query
    sparql_query = query_result.get("sparql_query")
    
    if not sparql_query or "ERROR_MISSING" in sparql_query:
        return {
            "question": query_dict["question"],
            "error": "Missing or incomplete query",
            "valid": False,
            "executed": False
        }
    
    # Validate the query
    is_valid, validation_message = validate_sparql_query(sparql_query)
    
    result = {
        "question": query_dict["question"],
        "template_id": query_dict["template_id"],
        "query": sparql_query,
        "entity_mappings": query_result.get("entity_mappings", {}),
        "predicate_mappings": query_result.get("predicate_mappings", {}),
        "valid": is_valid,
        "validation_message": validation_message
    }
    
    if is_valid:
        # Execute the query
        try:
            execution_results = execute_sparql_query(sparql_query)
            result["executed"] = execution_results["success"]
            
            if execution_results["success"]:
                # Extract formatted results
                formatted_results = extract_results_for_display(execution_results)
                result["results"] = formatted_results
                
                # Check if results are empty
                if len(formatted_results) == 1 and formatted_results[0] == "No results found":
                    result["valid"] = False
                    result["validation_message"] = "Query is syntactically valid but returns no results"
            else:
                result["execution_error"] = execution_results["error"]
        except Exception as e:
            result["executed"] = False
            result["execution_error"] = str(e)
    else:
        result["executed"] = False
    
    return result

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
        print("Usage:")
        print("  python test_sparql_queries.py <results_file.json> [output_file.json] [--limit N]")
        print("  python test_sparql_queries.py --single '<json_string>'")
        print("\nExamples:")
        print("  python test_sparql_queries.py improved_results.json test_results.json --limit 10")
        print("  python test_sparql_queries.py --single '{\"question\": \"give me the currency of China .\", \"template_id\": \"A\", \"mapping\": {\"currency\": \"dbo:currency\", \"of\": \"dbo:Of\", \"China\": \"dbr:china\"}}'")
        sys.exit(1)
    
    # Check if we're processing a single query
    if sys.argv[1] == "--single" and len(sys.argv) > 2:
        try:
            # Parse the query dictionary from the command line
            query_dict = json.loads(sys.argv[2])
            
            # Process the single query
            result = process_single_query(query_dict)
            
            # Print the result
            print(json.dumps(result, indent=2))
            
            # If an output file is specified, save the result
            if len(sys.argv) > 3 and not sys.argv[3].startswith("--"):
                output_file = sys.argv[3]
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                print(f"Result saved to {output_file}")
            
            return
        except json.JSONDecodeError:
            print("Error: Invalid JSON string for the single query")
            sys.exit(1)
        except Exception as e:
            print(f"Error processing single query: {str(e)}")
            sys.exit(1)
    
    # Regular processing of a results file
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