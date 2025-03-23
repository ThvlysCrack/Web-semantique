import json
import sys
import os
import re

def load_json_file(file_path):
    """Load a JSON file and return its contents."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def normalize_entity_name(entity_name):
    """
    Normalize entity names for DBpedia resources:
    - Capitalize first letter of each word
    - Replace spaces with underscores
    """
    # First, replace underscores with spaces for processing
    name = entity_name.replace('_', ' ')
    
    # Capitalize each word
    words = name.split()
    capitalized = [word.capitalize() for word in words]
    
    # Join with underscores for DBpedia format
    return '_'.join(capitalized)

def fix_dbr_resources(mappings):
    """Fix DBpedia resource references to ensure proper capitalization"""
    fixed_mappings = {}
    
    for key, value in mappings.items():
        if value.startswith('dbr:'):
            # Extract the entity name part (after 'dbr:')
            entity_name = value[4:]
            # Normalize it
            normalized_name = normalize_entity_name(entity_name)
            # Update the value
            fixed_mappings[key] = f"dbr:{normalized_name}"
        else:
            fixed_mappings[key] = value
    
    return fixed_mappings

def generate_sparql_query(question_index, questions, templates):
    """Generate a SPARQL query for the specified question index."""
    # Check if the index is valid
    if question_index < 0 or question_index >= len(questions):
        return f"Error: Index {question_index} is out of range. Valid range: 0-{len(questions)-1}"
    
    # Get the question and its mappings
    question_data = questions[question_index]
    template_id = question_data.get('template_id')
    mappings = question_data.get('mapping', {})
    
    # Fix entity references in mappings
    mappings = fix_dbr_resources(mappings)
    
    # Check if the template ID exists in the template map
    if template_id not in templates:
        return f"Error: Template ID '{template_id}' not found in the template map."
    
    # Get the SPARQL template
    template = templates[template_id]['sparql_template']
    
    # Define low-priority predicates (common but often not semantically meaningful)
    low_priority_predicates = ['is', 'was', 'are', 'were', 'does', 'did', 'has', 'have', 'had', 'in', 'on', 'at', 'by', 'to', 'for']
    
    # Process based on template type
    if template_id == 'A':
        # Template A: (S, P, ?ans)
        # Replace <S> and <P> with their corresponding values
        entity = None
        predicate = None
        
        # First, identify the entity (S) from mappings
        for key, value in mappings.items():
            if value.startswith('dbr:'):
                entity = value
                break
        
        # Create a dictionary to store predicate candidates and their priorities
        predicate_candidates = {}
        
        # Next, identify potential predicates and set their priority
        question_lower = question_data['question'].lower()
        
        # Scan all predicates and rate them
        for key, value in mappings.items():
            if not value.startswith('dbo:'):
                continue
                
            # Extract the predicate name without prefix
            pred_name = value[4:].lower()
            
            # Skip if the predicate is in the low priority list
            if pred_name.lower() in low_priority_predicates:
                predicate_candidates[value] = 1  # Lowest priority
                continue
            
            # Check for common question patterns and assign priorities
            priority = 2  # Default priority
            
            # Birth year questions
            if ("born" in question_lower or "birth" in question_lower) and ("year" in question_lower):
                if "birth" in key.lower() or "born" in key.lower() or "year" in key.lower():
                    priority = 10
                    if key.lower() == "birthyear" or key.lower() == "birth year":
                        priority = 15  # Highest priority
                
            # Death year questions
            elif ("die" in question_lower or "death" in question_lower) and ("year" in question_lower):
                if "death" in key.lower() or "die" in key.lower() or "year" in key.lower():
                    priority = 10
                    if key.lower() == "deathyear" or key.lower() == "death year":
                        priority = 15  # Highest priority
                        
            # Location questions
            elif any(loc in question_lower for loc in ["where", "location", "place"]):
                if any(loc in key.lower() for loc in ["location", "place", "country", "city"]):
                    priority = 10
            
            # Author questions
            elif any(auth in question_lower for auth in ["who wrote", "author", "writer"]):
                if any(auth in key.lower() for auth in ["author", "writer", "wrote"]):
                    priority = 10
            
            # Creation date questions
            elif any(date in question_lower for date in ["when", "date", "year"]) and any(create in question_lower for create in ["create", "found", "establish"]):
                if any(date in key.lower() for date in ["date", "year", "found", "establish", "create"]):
                    priority = 10
            
            # Currency questions
            elif "currency" in question_lower:
                if "currency" in key.lower():
                    priority = 15
            
            # Specific semantic actions
            relevant_actions = ["start", "end", "direct", "write", "compose", "invent", "discover", "marry", "spouse", "starring", "actor", "actress"]
            for action in relevant_actions:
                if action in question_lower and action in key.lower():
                    priority = 10
                    break
            
            # Store the predicate with its priority
            predicate_candidates[value] = priority
        
        # Select the predicate with the highest priority
        if predicate_candidates:
            predicate = max(predicate_candidates.items(), key=lambda x: x[1])[0]
        
        # Apply the substitutions
        query = template.replace('dbr:<S>', entity if entity else 'ERROR_MISSING_ENTITY')
        query = query.replace('dbo:<P>', predicate if predicate else 'ERROR_MISSING_PREDICATE')
    
    elif template_id == 'B':
        # Template B: (?ans, P, O)
        predicate = None
        object_val = None
        
        # First, find the object (O) entity in the mappings
        for key, value in mappings.items():
            if value.startswith('dbr:'):
                object_val = value
                break
        
        # Create a dictionary to store predicate candidates and their priorities
        predicate_candidates = {}
        
        # Process predicates
        question_lower = question_data['question'].lower()
        
        for key, value in mappings.items():
            if not value.startswith('dbo:'):
                continue
                
            # Extract the predicate name without prefix
            pred_name = value[4:].lower()
            
            # Skip if the predicate is in the low priority list
            if pred_name.lower() in low_priority_predicates:
                predicate_candidates[value] = 1  # Lowest priority
                continue
            
            # Check for common question patterns for B template
            priority = 2  # Default priority
            
            # Actor/Actress questions
            if any(actor in question_lower for actor in ["actor", "actress", "star", "cast"]):
                if any(act in key.lower() for act in ["actor", "actress", "star", "cast"]):
                    priority = 10
            
            # Author/Writer questions
            elif any(writer in question_lower for writer in ["author", "writer", "wrote"]):
                if any(write in key.lower() for write in ["author", "writer", "wrote"]):
                    priority = 10
            
            # Director questions
            elif "director" in question_lower:
                if "direct" in key.lower():
                    priority = 10
            
            # Other relationships
            relevant_actions = ["spouse", "marry", "child", "parent", "discover", "invent", "found", "create", "currency"]
            for action in relevant_actions:
                if action in question_lower and action in key.lower():
                    priority = 10
                    break
            
            # Store the predicate with its priority
            predicate_candidates[value] = priority
        
        # Select the predicate with the highest priority
        if predicate_candidates:
            predicate = max(predicate_candidates.items(), key=lambda x: x[1])[0]
        
        # Apply the substitutions
        query = template.replace('dbo:<P>', predicate if predicate else 'ERROR_MISSING_PREDICATE')
        query = query.replace('dbr:<O>', object_val if object_val else 'ERROR_MISSING_OBJECT')
    
    elif template_id == 'D':
        # Template D: (S, P, O)
        subject = None
        predicate = None
        object_val = None
        
        # Find entities in the mappings (subject and object)
        entities = [value for key, value in mappings.items() if value.startswith('dbr:')]
        if len(entities) >= 1:
            subject = entities[0]
        if len(entities) >= 2:
            object_val = entities[1]
        
        # Create a dictionary to store predicate candidates and their priorities
        predicate_candidates = {}
        
        # Process predicates
        question_lower = question_data['question'].lower()
        
        for key, value in mappings.items():
            if not value.startswith('dbo:'):
                continue
                
            # Extract the predicate name without prefix
            pred_name = value[4:].lower()
            
            # Skip if the predicate is in the low priority list
            if pred_name.lower() in low_priority_predicates:
                predicate_candidates[value] = 1  # Lowest priority
                continue
            
            # Check for common question patterns for D template
            priority = 2  # Default priority
            
            # Relationship questions
            if any(rel in question_lower for rel in ["spouse", "married", "husband", "wife"]):
                if any(rel in key.lower() for rel in ["spouse", "married", "husband", "wife"]):
                    priority = 10
            
            # Parent/Child questions
            elif any(rel in question_lower for rel in ["parent", "child", "son", "daughter", "father", "mother"]):
                if any(rel in key.lower() for rel in ["parent", "child", "son", "daughter", "father", "mother"]):
                    priority = 10
            
            # Currency questions
            elif "currency" in question_lower:
                if "currency" in key.lower():
                    priority = 15
            
            # Other specific relationships
            relevant_actions = ["direct", "create", "write", "compose", "discover", "invent", "found"]
            for action in relevant_actions:
                if action in question_lower and action in key.lower():
                    priority = 10
                    break
            
            # Store the predicate with its priority
            predicate_candidates[value] = priority
        
        # Select the predicate with the highest priority
        if predicate_candidates:
            predicate = max(predicate_candidates.items(), key=lambda x: x[1])[0]
        
        # Apply the substitutions
        query = template.replace('dbr:<S>', subject if subject else 'ERROR_MISSING_SUBJECT')
        query = query.replace('dbo:<P>', predicate if predicate else 'ERROR_MISSING_PREDICATE')
        query = query.replace('dbr:<O>', object_val if object_val else 'ERROR_MISSING_OBJECT')
    
    else:
        return {
            "question": question_data["question"],
            "template_id": template_id,
            "error": f"Unknown template ID '{template_id}'"
        }
    
    return {
        "question": question_data["question"],
        "template_id": template_id,
        "sparql_query": query,
        "entity_mappings": {k: v for k, v in mappings.items() if v.startswith('dbr:')},
        "predicate_mappings": {k: v for k, v in mappings.items() if v.startswith('dbo:')}
    }

def process_all_questions(output_file=None, verbose=False):
    """Process all questions and optionally save results to a file."""
    # Load the template map and questions
    templates = load_json_file('template_map.json')
    questions = load_json_file('mapped_classified_questions.json')
    
    results = []
    total_questions = len(questions)
    
    print(f"Processing {total_questions} questions...")
    
    for i, _ in enumerate(questions):
        result = generate_sparql_query(i, questions, templates)
        results.append(result)
        
        if verbose and (i % 100 == 0 or i == total_questions - 1):
            print(f"Processed {i+1}/{total_questions} questions")
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_file}")
    
    return results

def main():
    """Main function to run the script."""
    # Define command-line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_sparql.py <question_index>")
        print("  python generate_sparql.py all [output_file.json] [--verbose]")
        print("")
        print("Examples:")
        print("  python generate_sparql.py 0                   # Process question at index 0")
        print("  python generate_sparql.py all                 # Process all questions")
        print("  python generate_sparql.py all results.json    # Process all questions and save to results.json")
        print("  python generate_sparql.py all --verbose       # Process all questions with verbose output")
        sys.exit(1)
    
    try:
        # Load the template map and questions
        templates = load_json_file('template_map.json')
        questions = load_json_file('mapped_classified_questions.json')
        
        # Check if we're processing a single question or all questions
        if sys.argv[1].lower() == 'all':
            # Process all questions
            output_file = None
            verbose = False
            
            # Check for additional arguments
            if len(sys.argv) > 2:
                for arg in sys.argv[2:]:
                    if arg == '--verbose':
                        verbose = True
                    elif not arg.startswith('--'):
                        output_file = arg
            
            process_all_questions(output_file, verbose)
        else:
            # Process a single question
            question_index = int(sys.argv[1])
            result = generate_sparql_query(question_index, questions, templates)
            print(json.dumps(result, indent=2))
    
    except ValueError:
        print("Error: Question index must be an integer")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: File not found - {str(e)}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in one of the input files")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 