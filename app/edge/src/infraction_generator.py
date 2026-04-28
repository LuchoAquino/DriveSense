import random
from database_manager import get_all_rules # Importar la función para obtener reglas de la DB

def generate_random_infraction(no_infraction_probability: float = 0.1) -> dict:
    """
    Genera aleatoriamente un tipo de infracción o indica que no hay infracción,
    basándose en las reglas definidas en la base de datos.

    Args:
        no_infraction_probability (float): Probabilidad (entre 0 y 1) de que no se cometa ninguna infracción.

    Returns:
        dict: Un diccionario con la información de la infracción. Ejemplo:
              {'has_infraction': True, 'rule_id': 1, 'type': 'Exceso de velocidad', 'details': 'Velocidad detectada: 65 km/h'}
              {'has_infraction': False, 'rule_id': None, 'type': None, 'details': None}
    """
    if random.random() < no_infraction_probability:
        return {'has_infraction': False, 'rule_id': None, 'type': None, 'details': None}

    # Obtener las reglas de la base de datos
    rules = get_all_rules()
    if not rules:
        print("[WARNING] No se encontraron reglas en la base de datos. Generando infracción genérica.")
        # Fallback a infracciones hardcodeadas si la DB está vacía
        rules = [
            {'id': 1, 'name': "Exceso de velocidad"},
            {'id': 2, 'name': "Semaforo Rojo"},
            {'id': 3, 'name': "Invasión Cruce Peatonal"},
        ]

    chosen_rule = random.choice(rules)
    chosen_type_name = chosen_rule['name']
    chosen_rule_id = chosen_rule['id']
    details = ""

    # Generar detalles específicos basados en el tipo de infracción
    if "velocidad" in chosen_type_name.lower():
        speed = random.randint(50, 80) # Velocidad aleatoria para el ejemplo
        details = f"Velocidad detectada: {speed} km/h (Límite: 40 km/h)"
    elif "semáforo" in chosen_type_name.lower() or "semaforo" in chosen_type_name.lower():
        details = f"Cruzó semáforo en rojo"
    elif "invasión" in chosen_type_name.lower() or "invasion" in chosen_type_name.lower():
        details = f"Invadió zona peatonal."
    else:
        details = f"Infracción de tipo: {chosen_type_name}"

    return {'has_infraction': True, 'rule_id': chosen_rule_id, 'type': chosen_type_name, 'details': details}

if __name__ == "__main__":
    # Ejemplo de uso y prueba de la distribución
    print("Probando la generación de infracciones (100 intentos):")
    infraction_counts = {'no_infracc': 0}
    for _ in range(100):
        infraction = generate_random_infraction()
        if infraction['has_infraction']:
            infraction_counts[infraction['type']] = infraction_counts.get(infraction['type'], 0) + 1
        else:
            infraction_counts['no_infracc'] += 1
    
    for infraction_type, count in infraction_counts.items():
        print(f"  {infraction_type}: {count} veces")
