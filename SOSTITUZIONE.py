import csv
from typing import Dict, Any, List, Tuple, Set

OrariGiorno = Dict[str, str]
OrariProfessore = Dict[str, OrariGiorno]
Orari = Dict[str, OrariProfessore]
MaterieDocenti = Dict[str, List[str]]

def carica_orari(file_csv: str) -> Orari:
    orari: Orari = {}
    with open(file_csv, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        giorni_raw = next(reader)[1:]
        giorni = [g for g in giorni_raw if g]
        ore = next(reader)[1:]

        for row in reader:
            professore = normalizza_nome(row[0])
            orari[professore] = {}
            
            # Gestione ore normali (lunedì-venerdì)
            for i, giorno in enumerate(giorni[:5]):  # Solo i primi 5 giorni
                orari[professore][giorno] = {}
                start_index = i * 6 + 1
                end_index = start_index + 6
                for j, valore in enumerate(row[start_index:end_index], start=1):
                    if j <= len(ore):
                        ora = f"{j}^ {ore[j-1]}"
                        orari[professore][giorno][ora] = valore
            
            # Gestione ore pomeridiane del martedì
            if "Martedì" in orari[professore]:
                pomeriggio_start = 31  # Indice dopo le ore normali (5 giorni * 6 ore + 1)
                for j, valore in enumerate(row[pomeriggio_start:pomeriggio_start+3], start=7):
                    if j == 7:
                        ora = f"{j}^ {j+7}:30"
                    elif j == 8:
                        ora = f"{j}^ {j+7}:20"
                    elif j == 9:
                        ora = f"{j}^ {j+7}:10"
                    if valore.strip():  # Aggiungi solo se c'è un valore
                        orari[professore]["Martedì"][ora] = valore

    return orari

def insegna_in_classe(orari: Orari, professore: str, classe: str) -> bool:
    professore = professore.strip().title()
    for giorno in orari[professore]:
        for ora in orari[professore][giorno]:
            if orari[professore][giorno][ora] == classe:
                return True
    return False

def trova_co_insegnanti(orari: Orari, professore: str, giorno: str, ora: str, classe: str) -> List[str]:
    co_insegnanti = []
    professore = professore.strip().title()
    for prof, schedule in orari.items():
        if prof != professore and giorno in schedule and ora in schedule[giorno]:
            if schedule[giorno][ora] == classe:
                co_insegnanti.append(prof)
    return co_insegnanti

def normalizza_nome(nome: str) -> str:
    """
    Normalizza il nome del professore mantenendo l'iniziale se presente
    Es: "Rossi M." -> "Rossi M"
    Es: "rossi m." -> "Rossi M"
    Es: "ROSSI" -> "Rossi"
    """
    nome = nome.strip().title().replace("'", "'")
    parti = nome.split()
    
    # Se c'è solo il cognome, lo restituisce normalizzato
    if len(parti) == 1:
        return parti[0]
    
    # Se c'è un'iniziale (es: "Rossi M." o "Rossi M"), la mantiene
    if len(parti) == 2 and len(parti[1]) <= 2:
        iniziale = parti[1].replace('.', '').upper()
        return f"{parti[0]} {iniziale}"
    
    return nome

def trova_professore(orari: Orari, cognome: str) -> List[str]:
    """
    Cerca i professori che corrispondono al cognome, considerando anche l'iniziale se presente
    """
    input_parti = cognome.strip().upper().split()
    risultati = []
    
    for prof in orari.keys():
        prof_parti = prof.upper().split()
        
        # Se l'input include solo il cognome
        if len(input_parti) == 1:
            if prof_parti[0] == input_parti[0]:
                risultati.append(prof)
        # Se l'input include cognome e iniziale
        elif len(input_parti) == 2:
            if (prof_parti[0] == input_parti[0] and 
                len(prof_parti) > 1 and 
                prof_parti[1].startswith(input_parti[1].replace('.', ''))):
                risultati.append(prof)
    
    return sorted(risultati)  # Ordina i risultati alfabeticamente

def chiedi_professore(orari: Orari) -> str:
    while True:
        input_prof = input("\nInserisci il cognome del professore assente (o 'q' per terminare): ").strip()
        if input_prof.lower() == 'q':
            return 'q'
        
        professori_trovati = trova_professore(orari, input_prof)
        
        if len(professori_trovati) == 0:
            print(f"Errore: Nessun professore trovato con il cognome '{input_prof}'.")
            print("Per favore, controlla il cognome e riprova.")
            continue
            
        if len(professori_trovati) == 1:
            prof_scelto = professori_trovati[0]
            return prof_scelto
            
        # Se ci sono più professori con lo stesso cognome
        print(f"\nTrovati {len(professori_trovati)} professori con il cognome '{input_prof}':")
        for i, prof in enumerate(professori_trovati, 1):
            # Estrae l'iniziale se presente per una visualizzazione più chiara
            parti = prof.split()
            if len(parti) > 1:
                iniziale = parti[1]
                print(f"{i}. {parti[0]} {iniziale}.")
            else:
                print(f"{i}. {prof}")
                
        while True:
            scelta = input("\nSeleziona il numero del professore corretto (o premi Invio per cercare di nuovo): ")
            
            if not scelta:  # Se l'utente preme solo Invio
                break
                
            try:
                indice = int(scelta) - 1
                if 0 <= indice < len(professori_trovati):
                    prof_scelto = professori_trovati[indice]
                    print(f"Hai selezionato: {prof_scelto}")
                    return prof_scelto
                else:
                    print("Numero non valido. Riprova.")
            except ValueError:
                print("Input non valido. Inserisci un numero o premi Invio per cercare di nuovo.")

def calcola_tutte_le_sostituzioni(orari: Orari, professori_assenti: Set[str], giorno: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
    risultati = {}
    for professore_assente in professori_assenti:
        risultati[professore_assente] = trova_classi_e_sostituti(orari, professore_assente, giorno, professori_assenti)
    return risultati

def trova_classi_e_sostituti(orari: Orari, professore_assente: str, giorno: str, professori_assenti: Set[str]) -> Dict[str, Dict[str, Any]]:
    risultato = {}
    professore_assente_normalizzato = normalizza_nome(professore_assente)
    
    for ora in orari[professore_assente_normalizzato][giorno]:
        classe = orari[professore_assente_normalizzato][giorno][ora]
        if classe and classe != '(D)':
            if ora not in risultato:
                risultato[ora] = {
                    'classe': classe,
                    'sostituti': [],
                    'sostituti_della_classe': [],
                    'co_insegnanti': []
                }
            
            co_insegnanti = trova_co_insegnanti(orari, professore_assente_normalizzato, giorno, ora, classe)
            risultato[ora]['co_insegnanti'] = [co for co in co_insegnanti if normalizza_nome(co) not in professori_assenti]
            
            for prof, schedule in orari.items():
                prof_normalizzato = normalizza_nome(prof)
                if prof_normalizzato != professore_assente_normalizzato and prof_normalizzato not in co_insegnanti and prof_normalizzato not in professori_assenti:
                    if giorno in schedule and ora in schedule[giorno]:
                        if schedule[giorno][ora] == '(D)':
                            if any(
                                any(cl != '' and cl != '(D)' for cl in giorno_schedule.values()) 
                                for giorno_schedule in schedule.values()
                            ):
                                risultato[ora]['sostituti'].append(prof)
                                if insegna_in_classe(orari, prof, classe):
                                    risultato[ora]['sostituti_della_classe'].append(prof)

    return risultato

def scrivi_risultati_csv(risultati: Dict[str, Dict[str, Dict[str, Any]]], giorno: str, file_output: str) -> None:
    with open(file_output, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Assenti', 'Ora', 'Classe', 'Sostituzioni', 'Compresenza Recupero Straordinario', 'Compresenza', 'Stesso CDC', 'Disposizioni'])
        
        for professore_assente, risultato in risultati.items():
            # Ordina le ore per garantire che vengano scritte in ordine
            ore_ordinate = sorted(risultato.keys(), key=lambda x: int(x.split('^')[0]))
            for ora in ore_ordinate:
                info = risultato[ora]
                co_insegnanti: List[str] = info.get('co_insegnanti', [])
                sostituti_classe: List[str] = info.get('sostituti_della_classe', [])
                sostituti: List[str] = info.get('sostituti', [])
                
                co_insegnanti_str = ', '.join(co_insegnanti) if co_insegnanti else ' '
                sostituti_classe_str = ', '.join(sostituti_classe) if sostituti_classe else ' '
                sostituti_str = ', '.join(sostituti) if sostituti else 'Nessun sostituto'
                
                writer.writerow([
                    professore_assente,
                    ora,
                    info['classe'],
                    '',
                    '',
                    co_insegnanti_str,
                    sostituti_classe_str,
                    sostituti_str
                ])


def main():
    file_orari = 'ORARIO_DOCENTI_DEFINITIVO.csv'
    orari = carica_orari(file_orari)

    giorni_validi = ['lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì']
    
    while True:
        giorno_input = input("Inserisci il giorno della settimana (es. Lunedì): ").lower()
        if giorno_input in giorni_validi:
            giorno = giorno_input.capitalize()
            break
        else:
            print("Giorno non valido. Per favore, inserisci un giorno della settimana valido.")
    
    professori_assenti = set()
    while True:
        professore_assente = chiedi_professore(orari)
        if professore_assente.lower() == 'q':
            break
        
        professori_assenti.add(professore_assente)
        risultati = calcola_tutte_le_sostituzioni(orari, professori_assenti, giorno)
            
    if risultati:
        file_output = f"sostituzioni_{giorno}.csv"
        scrivi_risultati_csv(risultati, giorno, file_output)
        print(f"\nI risultati sono stati salvati nel file: {file_output}")
    else:
        print("Nessun risultato da salvare.")

if __name__ == "__main__":
    main()