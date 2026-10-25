### Story 2.3 : Ingestion PDF avec Ancrages par page

As a Anaël,
I want que mes PDF soient ingérés page par page,
So that une Question puisse citer une page précise et que la validation la retrouve.

**Exigences :** FR-6 ; AD-5 ; pile : pypdfium2, fpdf2 (dev).

**Acceptance Criteria:**

**Given** le Parser `pdf_text` (pypdfium2), enregistré au `kind` `parser` avec `formats = {"pdf"}`
**When** on parse un PDF de trois pages généré dans le test par fpdf2
**Then** chaque Block porte l'`anchor_id` `<doc_id>#p<page>`, avec des pages numérotées à partir de 1, et le texte de chaque page est retrouvé
**And** `anchors` contient une entrée par page, avec `page` renseigné

**Given** une page sans texte extractible
**When** on la parse
**Then** son Ancrage existe, avec un texte vide, et aucune exception n'est levée

**Given** un PDF illisible (octets tronqués)
**When** on l'ingère dans un Corpus
**Then** le Document est signalé et ignoré, et l'ingestion des autres Documents continue

**Given** un `ParsedCorpus` qui contient ce PDF
**When** on appelle `resolve("docs/registre.pdf", 2, ())` puis `resolve("docs/registre.pdf", 9, ())`
**Then** la première renvoie `<doc_id>#p2` et la seconde `None`
