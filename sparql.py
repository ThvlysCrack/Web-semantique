import requests
from openai import OpenAI
import re
import json
from datetime import datetime
import sparql_utils
import os
import argparse

# 1) Renseignez votre clé OpenAI
client = OpenAI(api_key="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")

DBPEDIA_SPARQL_ENDPOINT = "https://dbpedia.org/sparql"

def generate_sparql_from_nlp(question: str) -> str:
    """
    Envoie la question et un prompt spécial à l'API OpenAI ChatCompletion
    pour générer une requête SPARQL correspondant à la question NLP.
    """
    # Prompt modèle : instructions au modèle pour générer du SPARQL
    # Vous pouvez personnaliser ce prompt selon vos besoins.
    prompt = f"""
    Role: You are an assistant that converts natural language questions (in English) into valid SPARQL queries for DBpedia.

    Instructions:
    1. Return ONLY the SPARQL query enclosed in a Markdown code block using the language tag `sparql`:
       ```sparql
       YOUR QUERY
       ```
    2. Use common DBpedia prefixes like `dbo:` (http://dbpedia.org/ontology/), `dbr:` (http://dbpedia.org/resource/), and `dbp:` (http://dbpedia.org/property/).
    3. Do not include any explanatory text, commentary, or additional formatting before or after the code block.
    4. Aim for a minimal, valid SPARQL query that can be run on the official DBpedia endpoint. Include `PREFIX` declarations. Use `SELECT` if relevant (or `ASK` / `CONSTRUCT` / `DESCRIBE`, when appropriate).
    5. If necessary, use `FILTER` or `OPTIONAL` patterns, but keep the query as clear and direct as possible.

    Examples:

    User Question 1 (SELECT query):
    "Who is the director of the movie Inception?"

    Expected Response 1:
    ```sparql
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbr: <http://dbpedia.org/resource/>

    SELECT ?director
    WHERE {{
      dbr:Inception dbo:director ?director .
    }}
    ```

    User Question 2 (ASK query):
    "Is Paris the capital of France?"

    Expected Response 2:
    ```sparql
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbr: <http://dbpedia.org/resource/>

    ASK {{
      dbr:France dbo:capital dbr:Paris .
    }}
    ```

    Now, apply these instructions to the user question:
    "{question}"
    """

    try:
        # Appel à l'API OpenAI avec le nouveau client
        response = client.chat.completions.create(
            #model="o3-mini",
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that converts natural language questions into SPARQL. Your response must be a valid SPARQL query."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        # Récupération du texte généré
        generated_text = response.choices[0].message.content
        return generated_text
    except Exception as e:
        print("Erreur lors de l'appel à l'API OpenAI:", e)
        return ""

def execute_sparql_query(query: str) -> list: 
    """ Envoie la requête SPARQL à l'endpoint DBpedia et renvoie les résultats (format JSON). """ 
    try: 
        # Effectuer la requête GET avec les paramètres SPARQL + format JSON 
        response = requests.get(DBPEDIA_SPARQL_ENDPOINT, 
                              params={"query": query, "format": "json"}, 
                              timeout=30) # secondes
        # Vérifier la validité de la réponse 
        response.raise_for_status() 
        data = response.json()
        
        # Vérifier si c'est une requête ASK (retourne un booléen)
        if "boolean" in data:
            # Pour les requêtes ASK, on retourne directement le booléen
            return [{"boolean": {"value": "true" if data["boolean"] else "false"}}]
        
        # Pour les requêtes SELECT normales
        return data.get("results", {}).get("bindings", [])
    except Exception as e:
        print("Erreur lors de l'exécution de la requête SPARQL :", e)
        print("Réponse reçue:", response.text if 'response' in locals() else "Pas de réponse")
        return []

def process_single_question(question: str):
    """Traite une seule question et retourne les résultats"""
    print(f"\n=== Question : {question} ===")
    
    # Étape 1 : Génération de la requête SPARQL via l'API OpenAI
    sparql_query = generate_sparql_from_nlp(question)
    print("\n--- Requête SPARQL générée ---\n")
    print(sparql_query)

    # Étape 2 : Nettoyer la requête SPARQL (extraire du code markdown si nécessaire)
    sparql_query_clean = sparql_utils.clean_sparql_query(sparql_query)
    print("\n--- Requête SPARQL nettoyée ---\n")
    print(sparql_query_clean)
    
    # Étape 3 : Valider la requête SPARQL
    is_valid, validation_message = sparql_utils.validate_sparql_query(sparql_query_clean)
    print(f"\n--- Validation de la requête ---\n{validation_message}")
    
    if not is_valid:
        print("La requête n'est pas valide. Arrêt.")
        return None, None

    # Étape 4 : Exécution de la requête SPARQL
    query_results = sparql_utils.execute_sparql_query(sparql_query_clean)
    
    # Étape 5 : Extraction et affichage des résultats
    formatted_results = sparql_utils.extract_results_for_display(query_results)
    
    if not query_results["success"]:
        print("\nErreur lors de l'exécution de la requête.")
        print(formatted_results[0])
        return sparql_query_clean, None
    
    print("\n--- Résultats obtenus ---")
    for idx, result in enumerate(formatted_results, start=1):
        print(f"{idx}. {result}")
    
    return sparql_query_clean, query_results["results"]

def process_question_interactive(question=None):
    """
    Process a single question provided interactively or as parameter
    and save the results to a JSON file.
    
    Args:
        question (str, optional): Question to process. If None, will prompt user for input.
    
    Returns:
        str: Path to the saved results file
    """
    if question is None:
        question = input("Entrez votre question: ")
    
    # Process the question
    query, results = process_single_question(question)
    
    # Prepare the results dictionary
    results_data = {
        "date_execution": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resultats": []
    }
    
    if results:
        results_data["resultats"].append({
            "question": question,
            "requete_sparql": query,
            "resultats": results
        })
    
    # Save results to JSON file
    output_filename = f"resultats_sparql_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nLes résultats ont été sauvegardés dans: {output_filename}")
    return output_filename

def process_file_questions(file_path):
    """
    Process all questions from a file and save the results to a JSON file.
    
    Args:
        file_path (str): Path to the file containing questions, one per line
    
    Returns:
        str: Path to the saved results file
    """
    # Check if file exists
    if not os.path.isfile(file_path):
        print(f"Le fichier {file_path} n'existe pas.")
        return None
    
    # Read questions from file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            questions = f.readlines()
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {e}")
        return None
    
    # Initialize counters and results data
    total_questions = 0
    successful_queries = 0
    results_data = {
        "date_execution": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resultats": []
    }
    
    # Process each question
    for i, question in enumerate(questions, 1):
        question = question.strip()
        if not question:  # Skip empty lines
            continue
        
        print(f"\nTraitement de la question {i}: {question}")
        total_questions += 1
        query, results = process_single_question(question)
        
        if results:
            successful_queries += 1
            results_data["resultats"].append({
                "question": question,
                "requete_sparql": query,
                "resultats": results
            })
        
        print("\n" + "="*50 + "\n")  # Separator between questions
    
    # Save results to JSON file
    output_filename = f"resultats_sparql_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    
    # Display summary
    print(f"\nRésumé de l'exécution:")
    print(f"Total des questions traitées: {total_questions}")
    print(f"Requêtes réussies: {successful_queries}")
    if total_questions > 0:
        print(f"Taux de réussite: {(successful_queries/total_questions)*100:.2f}%")
    print(f"Les résultats ont été sauvegardés dans: {output_filename}")
    
    return output_filename

def main():
    """
    Main function to process questions either from command line, interactively,
    or from a file.
    """
    parser = argparse.ArgumentParser(description='Traitement de questions NLP en SPARQL')
    
    # Create a mutually exclusive group for question input methods
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('-q', '--question', type=str, help='Question unique à traiter')
    input_group.add_argument('-f', '--file', type=str, help='Chemin vers un fichier contenant des questions (une par ligne)')
    
    args = parser.parse_args()
    
    if args.question:
        # Process a single question provided as argument
        process_question_interactive(args.question)
    elif args.file:
        # Process questions from a file
        process_file_questions(args.file)
    else:
        # No arguments provided, show menu for interactive use
        print("\nTraitement de questions NLP en SPARQL")
        print("-------------------------------------")
        print("1. Traiter une question unique")
        print("2. Traiter des questions depuis un fichier")
        print("3. Quitter")
        
        choice = input("\nVotre choix (1-3): ")
        
        if choice == "1":
            process_question_interactive()
        elif choice == "2":
            file_path = input("Entrez le chemin du fichier de questions: ")
            process_file_questions(file_path)
        else:
            print("Au revoir!")
            return

if __name__ == "__main__": 
    main()


