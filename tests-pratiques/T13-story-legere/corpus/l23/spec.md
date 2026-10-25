# Story 2.3 : Ingestion PDF avec Ancrages par page

## Code Map

- `src/wavelibrarian/components/parsers/pdf_text.py` : Parser `pdf_text` (pypdfium2), `formats = {"pdf"}`, `version = "1"`, enregistré au `kind` `parser`.
- `src/wavelibrarian/corpus/ingest.py` : seul le commentaire d'`AUTO` change ; `pdf` -> `pdf_text` y figurait déjà, et `pdf_text` étant désormais enregistré, `auto` accepte un Corpus contenant des PDF.
- `tests/unit/components/test_pdf_text.py` : tests de la story (PDF générés par fpdf2 dans le test). `tests/unit/corpus/test_ingest.py` : l'attente « pdf_text non disponible » devient `{"pdf": "pdf_text"}`.

## Design Notes

- Un Ancrage `<doc_id>#p<n>` (n dès 1) par page, `page` renseigné, sans `heading_path`. Un seul Block `text` par page non vide, extrait par `get_text_bounded` (texte de la page entière, sans OCR).
- Page sans texte : l'Ancrage existe mais aucun Block n'est émis (pas de Block vide pour les Chunkers) ; `anchor_text` renvoie alors `""`.
- PDF illisible (ouverture ou page) : le Parser lève `ValueError`, que l'ingestion de 2.2 attrape déjà : Document signalé au journal et ignoré, les autres continuent. Rien n'est mis en cache.
- Le cache de parsing de 2.2 s'applique tel quel (`version` déclarée, invalidation par version testée). `resolve` existant couvre `page` (candidat `#p<n>` s'il est dans `anchors`).
- Hors périmètre : docling (extra), non utilisé ici ; images et tableaux des PDF non extraits.

## Tâches et critères

- [x] `pdf_text` enregistré, `formats = {"pdf"}`, `version` déclarée.
- [x] PDF de trois pages : `anchor_id` `<doc_id>#p<page>` dès 1, texte de chaque page retrouvé, une entrée `anchors` par page avec `page`.
- [x] Page sans texte : Ancrage présent, texte vide, aucune exception.
- [x] PDF tronqué : signalé et ignoré, les autres Documents ingérés.
- [x] `resolve("registre.pdf", 2, ())` -> `<doc_id>#p2`, page 9 -> `None`.
- [x] Report 2.2 : `version` + cache versionné pour le PDF.
