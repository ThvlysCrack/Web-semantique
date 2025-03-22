def transform_conll_to_bie(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as infile:
        lines = infile.readlines()

    output_lines = []

    for line in lines:
        line = line.strip()

        if line == "":
            output_lines.append("")  # Nouvelle question
            continue

        parts = line.split("\t")
        if len(parts) != 2:
            continue  # Ligne invalide

        token, tag = parts

        # On ignore les tokens simples ou ceux qui sont marqués N
        if tag == "N" or " " not in token:
            output_lines.append(f"{token}\t{tag if tag == 'N' else tag + '-B'}")
        else:
            # Token multi-mot (entité composée) à splitter
            words = token.split(" ")
            length = len(words)

            for i, word in enumerate(words):
                if length == 2:
                    suffix = "-B" if i == 0 else "-I"
                elif length >= 3:
                    if i == 0:
                        suffix = "-B"
                    elif i == length - 1:
                        suffix = "-E"
                    else:
                        suffix = "-I"
                else:
                    suffix = "-B"

                output_lines.append(f"{word}\t{tag}{suffix}")

    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.write("\n".join(output_lines))

    print("✅ Conversion terminée et sauvegardée dans :", output_path)


# 📌 Exemple d'utilisation
if __name__ == "__main__":
    input_file = "data/train.conll"      # Ton fichier d'entrée
    output_file = "data1/train.conll" # Ton fichier de sortie
    transform_conll_to_bie(input_file, output_file)
