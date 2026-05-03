"""Templates de redaction — v8 : restaure _BASE_SYSTEM mature, garde 22 templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Tone = Literal["formel", "neutre", "direct"]


@dataclass(frozen=True)
class Template:
    id: str
    label: str
    description: str
    system_prompt: str
    user_prompt_template: str


TONE_HINTS: dict[Tone, str] = {
    "formel": "Ton tres professionnel, vouvoiement, formule longue (« Je vous prie d'agreer, Madame, Monsieur, l'expression de mes salutations distinguees. »).",
    "neutre": "Ton professionnel et courtois, vouvoiement, formule standard (« Cordialement, »).",
    "direct": "Ton concis et factuel, vouvoiement, sans fioritures, formule courte (« Bien a vous, »).",
}


_BASE_SYSTEM = """Tu es BoostIA, un assistant de redaction professionnelle en francais.

REGLES IMPERATIVES :

1. Tu produis UNIQUEMENT le texte final demande. Pas de preambule, pas d'explication, pas de guillemets autour du texte. Pas de Markdown SAUF SI le template le demande explicitement.

2. Tu n'inventes JAMAIS aucune information : ni telephone, ni adresse, ni e-mail, ni nom, ni montant, ni date. Si une donnee n'est pas dans le contexte fourni, tu ne la mentionnes pas.

3. Tu REUTILISES TELS QUELS les elements du contexte (noms, societes, dates, montants, horaires). Pas de crochets autour. Les crochets [...] sont reserves UNIQUEMENT aux infos vraiment manquantes (ex. [votre nom] pour la signature).

4. DATE COMPLÈTE :
   - Si une date dans le contexte inclut une année (ex. "17 septembre 2026"), tu la reprends EXACTEMENT avec l'année.
   - Si une date n'a PAS d'année (ex. "jeudi 24 avril"), tu n'en ajoutes aucune.
   - Tu n'elargis jamais une date : "semaine du 7 juillet" reste "semaine du 7 juillet", pas "du 7 au 11 juillet".

5. Pour un e-mail, structure obligatoire dans cet ordre :
   - Ligne 1 : Objet : ...
   - Ligne vide
   - Salutation d'ouverture (Bonjour Monsieur X, / Bonjour, / Madame, Monsieur,)
   - Ligne vide
   - Corps du message
   - Ligne vide
   - UNE SEULE formule de politesse en cloture (jamais en ouverture, jamais en double)
   - Signature : [votre nom]

6. Tu respectes le ton, la structure et la longueur demandes."""


_CR_INSTRUCTIONS = (
    "A partir des notes brutes, redige un compte-rendu structure au format Markdown.\n"
    "\n"
    "FORMAT OBLIGATOIRE — EXEMPLE DE RENDU :\n"
    "# Réunion [nom/type] du [date COMPLETE avec année si présente]\n"
    "\n"
    "## Participants\n"
    "- [Nom Prénom] (fonction)\n"
    "- [Nom Prénom] (fonction)\n"
    "\n"
    "### Absents excusés\n"
    "- [Nom Prénom] (fonction) — si applicable, sinon omettre cette sous-section\n"
    "\n"
    "## Sujets abordés\n"
    "- [Sujet 1] : description courte\n"
    "- [Sujet 2] : description courte\n"
    "\n"
    "## Décisions prises\n"
    "- [Décision 1 avec détails du contexte]\n"
    "- [Décision 2 avec détails du contexte]\n"
    "\n"
    "## Actions à mener\n"
    "- [Qui] : [quoi] pour le [échéance COMPLETE avec année si présente]\n"
    "- [Qui] : [quoi] pour le [échéance COMPLETE avec année si présente]\n"
    "\n"
    "## Prochaine réunion\n"
    "- [date/heure/lieu exacts du contexte] — si applicable, sinon omettre\n"
    "\n"
    "RÈGLES DE CONTENU OBLIGATOIRES :\n"
    "- SECTIONS MINIMALES : Participants, Sujets abordés, Décisions prises, Actions à mener.\n"
    "  Ces 4 sections DOIVENT apparaître (même si une section est très courte).\n"
    "- SECTIONS OPTIONNELLES : « Absents excusés » (si mentionnés), « Prochaine réunion » (si date donnée).\n"
    "- TITRE H1 : doit contenir le type de réunion + la date COMPLÈTE. Si l'année est dans les notes, tu la mets.\n"
    "- DATES : reprends TOUTES les dates TELLES QUELLES, avec année si présente (ex. « 17 septembre 2026 » reste « 17 septembre 2026 »).\n"
    "- PARTICIPANTS : si seul un titre est donné sans nom (ex. « le CEO »), écris « [Prénom Nom] (CEO) » ou utilise le nom si fourni.\n"
    "- PAS d'objet, pas de salutation, pas de formule de politesse, pas de signature : ce n'est PAS un e-mail.\n"
    "{tone_hint}\n"
    "\n"
    "Notes brutes :\n---\n{context}\n---"
)


def _email(consigne: str) -> str:
    return (
        f"{consigne}\n{{tone_hint}}\n"
        "Reprends TELS QUELS, sans crochets, tous les noms (personne, societe), "
        "dates, montants et coordonnees du contexte.\n\n"
        "Contexte :\n---\n{context}\n---"
    )


_OVERRIDE_TUTOIEMENT = (
    "IMPORTANT : pour CE template uniquement, IGNORE la regle de vouvoiement "
    "donnee plus haut. Utilise le TUTOIEMENT (« tu », « toi »), un ton "
    "chaleureux et naturel, comme entre proches. Pas de formule de politesse "
    "formelle, pas de signature \"[votre nom]\". Le message doit pouvoir etre "
    "envoye tel quel par SMS / WhatsApp / Slack."
)


TEMPLATES: dict[str, Template] = {
    # E-mails pro
    "email_relance": Template(id="email_relance", label="E-mail de relance",
        description="Relancer poliment un interlocuteur sans reponse.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email("Redige un e-mail de relance. Rappelle le contexte precedent, formule la relance sans agressivite, propose une prochaine etape concrete.")),
    "email_remerciement": Template(id="email_remerciement", label="E-mail de remerciement",
        description="Remercier apres un echange ou un service rendu.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email("Redige un e-mail de remerciement chaleureux mais professionnel. Mentionne precisement ce pour quoi tu remercies.")),
    "email_refus": Template(id="email_refus", label="E-mail de refus poli",
        description="Decliner une demande, candidature ou proposition avec tact.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email("Redige un e-mail de refus poli et bienveillant. Justifie brievement la decision sans t'etendre, ne t'excuse pas excessivement, laisse la porte ouverte si pertinent.")),
    "email_demande": Template(id="email_demande", label="E-mail de demande",
        description="Formuler une demande claire (info, action, rendez-vous).", system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email("Redige un e-mail de demande clair et precis. Enonce la demande des le premier paragraphe, donne le contexte necessaire, precise une echeance si elle est dans le contexte.")),
    "email_intro": Template(id="email_intro", label="E-mail de premier contact",
        description="Se presenter a un nouvel interlocuteur professionnel.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email("Redige un e-mail de premier contact professionnel. Presente-toi brievement (qui, role), explique la raison du contact, propose une suite concrete (echange, rendez-vous, envoi de document).")),
    "email_excuse": Template(id="email_excuse", label="E-mail d'excuse",
        description="S'excuser professionnellement (retard, erreur, oubli).", system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email("Redige un e-mail d'excuse professionnel. Reconnais clairement le manquement (sans en rajouter), explique brievement le contexte sans te chercher d'excuses, propose une mesure corrective concrete. Reste sobre, jamais larmoyant.")),
    "email_confirmation": Template(id="email_confirmation", label="E-mail de confirmation",
        description="Confirmer un rendez-vous, une commande ou un accord.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email("Redige un e-mail de confirmation. Reprends precisement les details du contexte (date, heure, lieu, sujet, montants...). Rappelle les actions a faire de chaque cote si pertinent. Termine en restant disponible.")),
    "email_annulation": Template(id="email_annulation", label="E-mail d'annulation",
        description="Annuler un rendez-vous ou un engagement avec tact.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email("Redige un e-mail d'annulation. Annonce l'annulation des le premier paragraphe, explique brievement la raison sans t'etendre, propose une alternative (nouvelle date, autre modalite) si possible. Exprime un regret sobre.")),
    "email_negociation": Template(id="email_negociation", label="E-mail de negociation",
        description="Negocier des conditions, un tarif, des delais.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email("Redige un e-mail de negociation professionnel. Reconnais la proposition initiale, formule la contre-proposition avec une justification breve (valeur, contraintes), reste ouvert au dialogue, propose un echange. JAMAIS d'agressivite ni d'ultimatum.")),
    "email_feedback": Template(id="email_feedback", label="E-mail de feedback constructif",
        description="Donner un retour professionnel (positif ou critique).", system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email("Redige un e-mail de feedback professionnel et constructif. Equilibre ce qui fonctionne et ce qui peut etre ameliore. Sois precis (donne des exemples du contexte), evite les jugements de personne, propose des pistes d'action concretes. Termine sur une note positive.")),

    # Documents pro
    "bio_pro": Template(id="bio_pro", label="Bio professionnelle",
        description="Presentation courte (LinkedIn About, page Equipe).", system_prompt=_BASE_SYSTEM,
        user_prompt_template=("Redige une bio professionnelle a la PREMIERE PERSONNE en francais (80-120 mots). Ouverture forte sur le metier/role actuel, 2-3 phrases sur l'experience cle ou la valeur ajoutee, 1 phrase de cloture personnelle. Sobre, sans superlatifs creux ni jargon vide. Pas de Markdown.\n{tone_hint}\n\nElements fournis :\n---\n{context}\n---")),
    "lettre_motivation": Template(id="lettre_motivation", label="Lettre de motivation",
        description="Candidature pour un poste ou une mission.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=("Redige une lettre de motivation en francais (300-400 mots). Structure : 1) accroche personnalisee sur le poste/l'entreprise, 2) mise en avant de 2-3 experiences ou competences pertinentes (reprises du contexte), 3) projection sur le poste et la valeur ajoutee, 4) demande d'entretien.\n{tone_hint}\nInclure une formule de politesse de cloture adaptee au ton.\n\nContexte :\n---\n{context}\n---")),
    "description_poste": Template(id="description_poste", label="Description de poste",
        description="Offre d'emploi structuree pour publication.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=("Redige une description de poste structuree en francais. Sections (titres en gras simples) :\n  - Contexte : 2-3 phrases sur l'entreprise et le besoin\n  - Missions : 4-6 puces (verbes d'action)\n  - Profil recherche : 4-5 puces (competences + savoir-etre)\n  - Modalites : type de contrat, lieu, remuneration si fournie\nN'invente AUCUNE info absente du contexte.\n{tone_hint}\n\nBrief :\n---\n{context}\n---")),

    # Interne
    "annonce_interne": Template(id="annonce_interne", label="Annonce interne",
        description="Communiquer une nouvelle a l'equipe ou la societe.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=("Redige une annonce interne en francais. Structure :\n  - Objet sur la 1re ligne : « Objet : ... »\n  - Ligne vide\n  - Salutation chaleureuse (« Bonjour a toutes et tous, »)\n  - Contexte bref\n  - L'annonce elle-meme\n  - Impacts concrets / prochaines etapes\n  - Cloture avec qui contacter\n  - Signature : [votre nom]\nTon plus chaleureux qu'un e-mail externe, mais reste pro.\n{tone_hint}\n\nContexte :\n---\n{context}\n---")),

    # Marketing/social
    "message_commercial": Template(id="message_commercial", label="Message commercial",
        description="Premier contact ou proposition commerciale breve.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=("Redige un message commercial bref (max 150 mots) en francais. Accroche personnalisee, proposition de valeur claire, appel a l'action concret en fin (rendez-vous, demo, reponse).\n{tone_hint}\n\nContexte :\n---\n{context}\n---")),
    "post_linkedin": Template(id="post_linkedin", label="Publication LinkedIn",
        description="Post LinkedIn engageant a la premiere personne.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=("Redige une publication LinkedIn en francais a la PREMIERE PERSONNE (150-300 mots). Structure : accroche forte, ligne vide entre paragraphes, 2-4 paragraphes courts, cloture avec une question ouverte. Ton naturel. Emojis avec parcimonie (max 2-3). Pas de hashtags sauf si fournis. Pas de Markdown.\n{tone_hint}\n\nSujet :\n---\n{context}\n---")),
    "reponse_avis": Template(id="reponse_avis", label="Reponse a un avis client",
        description="Repondre a un avis Google, Trustpilot, etc.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=("Redige une reponse professionnelle a un avis client en francais (60-120 mots). Si positif : remercie chaleureusement, personnalise, invite a revenir. Si negatif : reconnais le ressenti sans contester, excuses sobres si pertinent, propose un suivi en prive (sans inventer de coordonnees), reste calme.\n{tone_hint}\n\nAvis client :\n---\n{context}\n---")),

    # Productivite
    "compte_rendu": Template(id="compte_rendu", label="Compte-rendu de reunion",
        description="Synthetiser des notes brutes en compte-rendu structure (Markdown).",
        system_prompt=_BASE_SYSTEM, user_prompt_template=_CR_INSTRUCTIONS),

    # Perso (tutoiement)
    "liste_courses": Template(id="liste_courses", label="Liste de courses",
        description="Liste de courses organisee par rayon a partir de besoins en vrac.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=("A partir du contexte (besoins en vrac, recettes prevues, vide-frigo a combler), produit une LISTE DE COURSES claire et organisee.\n\nFormat texte brut (PAS de Markdown) :\n  - Regroupe par rayon : Fruits & Legumes, Viandes & Poissons, Produits laitiers, Epicerie / Sec, Surgeles, Boissons, Hygiene, Autres.\n  - N'inclus QUE les rayons utiles.\n  - Une ligne par produit : « - Tomates (4) » ou « - Pates (500g) ».\n  - Indique la quantite si elle est dans le contexte. Sinon, ne l'invente PAS.\n\nPas de phrase d'intro, pas de cloture. Juste la liste.\n{tone_hint}\n\nBesoins :\n---\n{context}\n---")),
    "message_perso": Template(id="message_perso", label="Message a un proche",
        description="SMS / WhatsApp court et chaleureux a la famille ou un ami proche.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=("Redige un message court (50-200 caracteres) a destination d'un proche (conjoint, famille, ami).\n" + _OVERRIDE_TUTOIEMENT + "\nEmojis acceptes avec parcimonie (max 1-2). Ton naturel. Pas d'objet, pas de signature.\n{tone_hint}\n\nCe que je veux dire :\n---\n{context}\n---")),
    "message_rapide": Template(id="message_rapide", label="Message rapide",
        description="Message ultra-court a un collegue ou un ami (Slack, SMS).", system_prompt=_BASE_SYSTEM,
        user_prompt_template=("Redige un message ULTRA-COURT (max 100 caracteres si possible) pour un collegue ou un ami.\n" + _OVERRIDE_TUTOIEMENT + "\nDirect, factuel, pas de fioritures, pas d'emoji. Va droit au but. Pas d'objet, pas de salutation, pas de signature.\n{tone_hint}\n\nCe que je veux dire :\n---\n{context}\n---")),
    "compacter": Template(id="compacter", label="Compacter un texte",
        description="Reduire un texte verbeux a l'essentiel, garder le sens.", system_prompt=_BASE_SYSTEM,
        user_prompt_template=("Prends le texte fourni et produis-en une version COMPACTEE qui garde TOUT le sens utile mais en bien moins de mots (vise environ 30-50 % du texte d'origine).\n\nREGLES :\n- N'invente RIEN. Pas d'info absente du texte source.\n- Garde tous les faits, noms, dates, chiffres, decisions.\n- Coupe les redondances, formules de politesse longues, repetitions, transitions inutiles.\n- Garde le meme niveau de formalite que le texte source.\n- Sortie en texte brut, sans Markdown, sans titres ajoutes.\n- Si le texte fait deja moins de 100 mots : reponds « Texte deja court, peu d'optimisation possible. »\n{tone_hint}\n\nTexte a compacter :\n---\n{context}\n---")),
}


def get_template(template_id: str) -> Template:
    if template_id not in TEMPLATES:
        raise KeyError(f"Template inconnu : {template_id!r}")
    return TEMPLATES[template_id]


def list_templates() -> list[dict[str, str]]:
    return [{"id": t.id, "label": t.label, "description": t.description} for t in TEMPLATES.values()]


def build_messages(template_id: str, context: str, tone: Tone) -> list[dict[str, str]]:
    template = get_template(template_id)
    if tone not in TONE_HINTS:
        raise ValueError(f"Tonalite inconnue : {tone!r}")
    user_content = template.user_prompt_template.format(
        context=context.strip(), tone_hint=TONE_HINTS[tone],
    )
    return [
        {"role": "system", "content": template.system_prompt},
        {"role": "user", "content": user_content},
    ]
