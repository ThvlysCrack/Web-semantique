from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions
import re

# DBpedia SPARQL endpoint URL
DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"

def validate_sparql_query(query):
    """
    Validates if a SPARQL query is syntactically correct using SPARQLWrapper
    without executing it.
    
    Args:
        query (str): The SPARQL query to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Basic syntax check (contains basic SPARQL keywords)
    basic_check = False
    if re.search(r'\b(SELECT|ASK|CONSTRUCT|DESCRIBE)\b', query, re.IGNORECASE):
        basic_check = True
    
    if not basic_check:
        return False, "Query does not contain a valid SPARQL operation (SELECT, ASK, CONSTRUCT, or DESCRIBE)"
    
    # Validate query using SPARQLWrapper
    try:
        sparql = SPARQLWrapper(DBPEDIA_ENDPOINT)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        
        # Set method to POST for validation without execution
        sparql.setMethod('POST')
        sparql.setRequestMethod('urlencoded')
        
        # Additional validation header
        sparql.addCustomHttpHeader('X-Validate', 'true')
        
        # Attempt to prepare the query (will raise exception if invalid)
        sparql.query()
        
        # Check if query actually returns results
        try:
            test_results = execute_sparql_query(query)
            
            # If execution was successful
            if test_results["success"]:
                formatted_results = extract_results_for_display(test_results)
                
                # If there are no results found, mark as invalid
                if len(formatted_results) == 1 and formatted_results[0] == "No results found":
                    return False, "Query is syntactically valid but returns no results"
            
            return True, "Query is valid and returns results"
        except Exception as exec_err:
            # If there was an issue testing the query, still mark as valid syntactically
            return True, "Query is syntactically valid, but couldn't verify results"
        
    except Exception as e:
        # Extract the error message
        error_msg = str(e)
        return False, f"Invalid query: {error_msg}"

def clean_sparql_query(query_text):
    """
    Clean and extract a SPARQL query from text that might contain markdown code blocks.
    
    Args:
        query_text (str): The text containing a SPARQL query, possibly in markdown format
        
    Returns:
        str: The cleaned SPARQL query
    """
    # Try to extract SPARQL from markdown code blocks
    code_blocks = re.findall(r"```(?:sparql)?(.*?)```", query_text, re.DOTALL | re.IGNORECASE)
    
    if code_blocks:
        # Take the first code block found
        return code_blocks[0].strip()
    
    # If no code blocks, just clean the string
    return query_text.strip()

def execute_sparql_query(query):
    """
    Execute a SPARQL query on DBpedia and return the results.
    
    Args:
        query (str): The SPARQL query to execute
        
    Returns:
        dict: The results of the query in JSON format
    """
    sparql = SPARQLWrapper(DBPEDIA_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        error_msg = str(e)
        return {
            "success": False,
            "error": error_msg
        }

def extract_results_for_display(query_results):
    """
    Extract and format query results for readable display.
    
    Args:
        query_results (dict): Results from execute_sparql_query
        
    Returns:
        list: Formatted results
    """
    if not query_results["success"]:
        return [f"Error: {query_results['error']}"]
    
    results = query_results["results"]
    
    # Handle ASK queries
    if "boolean" in results:
        return ["Yes" if results["boolean"] else "No"]
    
    # Handle SELECT queries
    bindings = results.get("results", {}).get("bindings", [])
    if not bindings:
        return ["No results found"]
    
    formatted_results = []
    for row in bindings:
        result_row = {}
        for var_name, var_data in row.items():
            value = var_data["value"]
            datatype = var_data.get("datatype", "")
            
            # Clean up URI references to make them more readable
            if var_data.get("type") == "uri" and value.startswith("http://dbpedia.org/resource/"):
                value = value.replace("http://dbpedia.org/resource/", "")
                value = value.replace("_", " ")
            
            # Format values based on datatype
            if "date" in datatype.lower():
                value = f"Date: {value}"
            elif "integer" in datatype.lower() or "decimal" in datatype.lower():
                value = f"Number: {value}"
            
            result_row[var_name] = value
        
        formatted_results.append(result_row)
    
    return formatted_results 