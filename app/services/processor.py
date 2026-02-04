# app/services/processor.py
from app.core.registry import registry

import json
import os

# def process_json_file(input_path: str, output_filename: str) -> str:
#     # 1. Lire le fichier
#     with open(input_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)
    
#     # 2. Utiliser ta logique de calcul existante
#     results = process_minimal_json(data)
    
#     # 3. Créer le chemin de sortie (dans un dossier 'results' par exemple)
#     output_dir = "data/results"
#     os.makedirs(output_dir, exist_ok=True)
#     output_path = os.path.join(output_dir, output_filename)
    
#     # 4. Écrire le fichier
#     with open(output_path, 'w', encoding='utf-8') as f:
#         json.dump(results, f, indent=4, ensure_ascii=False)
    
#     return output_path # On retourne le chemin pour pouvoir le lire plus tard



def process_minimal_json(data: list):
    if not data or len(data) < 2:
        return {"error": "Format invalide. Besoin des métriques et d'au moins un couple."}

    # On récupère les métriques
    selected_metrics = data[0]

    # On récupère les couples de phrases
    pairs = data[1:]
    batch_results = []

    # On applique la métrique a chaque paires
    for pair in pairs:
        if len(pair) == 2:
            p1, p2 = pair[0], pair[1]
            scores = {}
            
            for name in selected_metrics:
                metric = registry.get(name)
                if metric:
                    res = metric.compute(p1, p2)
                    scores[name] = res.score
                else:
                    scores[name] = "Inconnue"
            
            batch_results.append({
                "p1": p1,
                "p2": p2,
                "scores": scores
            })

    return {"results": batch_results}