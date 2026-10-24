"""Classement manuel des constats Important (relu et juge a la main par l'agent qui a mene T5, test et code lus).

Classes : manque = defaut connu manque par la chaine (verite terrain) ; chaine = deja trouve par la chaine (revue d'origine) ;
confirme = nouveau defaut reel, test qui echoue pour la bonne raison, non consigne par la chaine ; discutable = test qui echoue
mais ecart litteral a la spec, durcissement sans exploitation atteinte ou comportement defendable ; rien = rien de verifiable
(test invalide, ou contredit un choix explicite de la revue d'origine, ou declenche par une hypothese que le depot n'a pas).
"""
import json
from pathlib import Path

C = {}


def c(cle, classe, note, defaut=None):
    C[cle] = {"classe": classe, "note": note, **({"defaut": defaut} if defaut else {})}


AUTRE_PROJET = "Cle d'un autre projet ignoree par le controle des citations : rejete par la revue (un seul projet Jira en E0)"
LEXICO = "Fichier de progression choisi par nom le plus petit : rejete par la revue (egalite de seconde, carried)"
JSON_TAB = "Identifiant separe par tabulations ou sauts de ligne, echappes en \t \n dans la trace JSONL : la revue disait les tabulations couvertes (en texte decode seulement)"
NBSP = "Declenche par l'echappement \u00a0 de json.dumps(ensure_ascii=True) : le depot ecrit ensure_ascii=False, donc non representatif"
STALE = "Progression d'un ancien lancement affichee en statut attente : non consigne par la chaine, jamais corrige ensuite"
OUTILS = "Ecart litteral a la matrice de la spec (outils aucun au refus) : la liste des outils appeles est aussi une information, jamais corrige ensuite"

c("moonshotai__kimi-k3.1-pro__S1-E0-7__C1", "chaine", AUTRE_PROJET)
c("moonshotai__kimi-k3.1-pro__S3-6-10__C1", "confirme", JSON_TAB + " ; non corrige sur main")
c("moonshotai__kimi-k3.1-pro__S3-6-10__C2", "chaine", "Appel en echec absent des traces et du bilan : constat reporte par la revue de 6.10, corrige en 6.10-b (le test passe sur main)", "D1")
c("moonshotai__kimi-k3.1-pro__S7-7-16__C1", "discutable", OUTILS)
c("openai__gpt-6-luna__S1-E0-7__C1", "chaine", AUTRE_PROJET)
c("openai__gpt-6-luna__S3-6-10__C1", "rien", NBSP)
c("openai__gpt-6-luna__S6-7-15__C1", "confirme", STALE)
c("openai__gpt-6.1-sol__S1-E0-7__C1", "chaine", AUTRE_PROJET)
c("openai__gpt-6.1-sol__S2-E0-8__C1", "chaine", LEXICO)
c("openai__gpt-6.1-sol__S3-6-10__C1", "discutable", "Le test echoue d'abord sur le cas \u00a0 (non representatif) ; la meme faille est reelle pour \n (cf. kimi)")
c("openai__gpt-6.1-sol__S6-7-15__C1", "confirme", STALE)
c("openai__gpt-6.1-sol__S7-7-16__C1", "discutable", OUTILS)
c("openai__gpt-6.1-sol__S7-7-16__C2", "discutable", "Image Markdown distante non neutralisee dans la fiche outillage : durcissement, la fiche du depot n'en contient pas")
PLAFOND = "Contredit la matrice I/O mais correspond au plafond MAX_ECHECS_PASSAGE (20 echecs au total) ajoute par la revue pour corriger un high : decision explicite de la chaine ; le test est valide (UsineErreur levee par le code apres 20 echecs non consecutifs)"
c("xiaomi__mimo-v2.6-pro__S3-6-10__C1", "chaine", PLAFOND)
c("openai__gpt-6-luna__S1-E0-7__C1__r2", "chaine", AUTRE_PROJET)
c("openai__gpt-6-luna__S2-E0-8__C1__r2", "chaine", LEXICO)
c("openai__gpt-6-luna__S3-6-10__C1__r2", "chaine", PLAFOND)
c("openai__gpt-6-luna__S7-7-16__C1__r2", "discutable", "Exception inattendue de la fabrique de session renvoyee en 502 generique et non en 503 : echec reel du test (RuntimeError non convertie), gravite faible")
c("openai__gpt-6.1-sol__S1-E0-7__C1__r2", "chaine", AUTRE_PROJET)
c("openai__gpt-6.1-sol__S2-E0-8__C1__r2", "chaine", LEXICO)
c("openai__gpt-6.1-sol__S3-6-10__C1__r2", "rien", NBSP + " (le test impose ensure_ascii=True)")
c("openai__gpt-6.1-sol__S6-7-15__C1__r2", "confirme", STALE)
c("openai__gpt-6.1-sol__S7-7-16__C1__r2", "discutable", OUTILS)

Path(__file__).with_name("classification.json").write_text(json.dumps(C, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(C), "constats classes")
