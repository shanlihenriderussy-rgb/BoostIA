"""Templates de redaction — v6 : pack etendu (22 templates), incl. persos (tutoiement)."""

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
    "formel": "Vouvoiement, formule longue (Je vous prie d'agreer...).",
    "neutre": "Vouvoiement, formule standard (Cordialement).",
    "direct": "Vouvoiement, formule courte (Bien a vous).",
}


_BASE_SYSTEM = """Tu es BoostIA, assistant de redaction professionnelle.

CONSIGNES METAL :
- RESPECTE SCRUPULEUSEMENT le contexte fourni. COPY/PASTE les infos (noms, dates, montants) TELLES QUELLES.
- SI une info n'est PAS dans le contexte, NE L'INVENTE PAS. Ecris "[info manquante]" si indispensable.
- PAS de preambule, PAS d'explication, PAS de guillemets. Juste le texte final.
- PAS de Markdown SAUF si le template le demande.
- Sois CONCIS. Pas de phrases inutiles."""


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
    """Helper pour generer un user_prompt e-mail standard (vouvoiement, structure stricte)."""
    return (
        f"{consigne}\n{{tone_hint}}\n"
        "Reprends TELS QUELS, sans crochets, tous les noms (personne, societe), "
        "dates, montants et coordonnees du contexte.\n\n"
        "Contexte :\n---\n{context}\n---"
    )


# Override pour les templates persos : ignore le vouvoiement, force le tutoiement
_OVERRIDE_TUTOIEMENT = (
    "IMPORTANT : pour CE template uniquement, IGNORE la regle de vouvoiement "
    "donnee plus haut. Utilise le TUTOIEMENT (« tu », « toi »), un ton "
    "chaleureux et naturel, comme entre proches. Pas de formule de politesse "
    "formelle, pas de signature \"[votre nom]\". Le message doit pouvoir etre "
    "envoye tel quel par SMS / WhatsApp / Slack."
)


TEMPLATES: dict[str, Template] = {

    # =================== E-MAILS PRO (10) ===================

    "email_relance": Template(
        id="email_relance",
        label="E-mail de relance",
        description="Relancer poliment un interlocuteur sans reponse.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail de relance. Rappelle le contexte precedent, "
            "formule la relance sans agressivite, propose une prochaine etape "
            "concrete."
        ),
    ),
    "email_remerciement": Template(
        id="email_remerciement",
        label="E-mail de remerciement",
        description="Remercier apres un echange ou un service rendu.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail de remerciement chaleureux mais professionnel. "
            "Mentionne precisement ce pour quoi tu remercies."
        ),
    ),
    "email_refus": Template(
        id="email_refus",
        label="E-mail de refus poli",
        description="Decliner une demande, candidature ou proposition avec tact.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail de refus poli et bienveillant. Justifie brievement "
            "la decision sans t'etendre, ne t'excuse pas excessivement, laisse "
            "la porte ouverte si pertinent."
        ),
    ),
    "email_demande": Template(
        id="email_demande",
        label="E-mail de demande",
        description="Formuler une demande claire (info, action, rendez-vous).",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail de demande clair et precis. Enonce la demande des "
            "le premier paragraphe, donne le contexte necessaire, precise une "
            "echeance si elle est dans le contexte."
        ),
    ),
    "email_intro": Template(
        id="email_intro",
        label="E-mail de premier contact",
        description="Se presenter a un nouvel interlocuteur professionnel.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail de premier contact professionnel. Presente-toi "
            "brievement (qui, role), explique la raison du contact, propose une "
            "suite concrete (echange, rendez-vous, envoi de document)."
        ),
    ),
    "email_excuse": Template(
        id="email_excuse",
        label="E-mail d'excuse",
        description="S'excuser professionnellement (retard, erreur, oubli).",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail d'excuse professionnel. Reconnais clairement le "
            "manquement (sans en rajouter), explique brievement le contexte sans "
            "te chercher d'excuses, propose une mesure corrective concrete. Reste "
            "sobre, jamais larmoyant."
        ),
    ),
    "email_confirmation": Template(
        id="email_confirmation",
        label="E-mail de confirmation",
        description="Confirmer un rendez-vous, une commande ou un accord.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail de confirmation. Reprends precisement les details "
            "du contexte (date, heure, lieu, sujet, montants...). Rappelle les "
            "actions a faire de chaque cote si pertinent. Termine en restant "
            "disponible."
        ),
    ),
    "email_annulation": Template(
        id="email_annulation",
        label="E-mail d'annulation",
        description="Annuler un rendez-vous ou un engagement avec tact.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail d'annulation. Annonce l'annulation des le premier "
            "paragraphe, explique brievement la raison sans t'etendre, propose "
            "une alternative (nouvelle date, autre modalite) si possible. "
            "Exprime un regret sobre."
        ),
    ),
    "email_negociation": Template(
        id="email_negociation",
        label="E-mail de negociation",
        description="Negocier des conditions, un tarif, des delais.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail de negociation professionnel. Reconnais la "
            "proposition initiale, formule la contre-proposition avec une "
            "justification breve (valeur, contraintes), reste ouvert au dialogue, "
            "propose un echange. JAMAIS d'agressivite ni d'ultimatum."
        ),
    ),
    "email_feedback": Template(
        id="email_feedback",
        label="E-mail de feedback constructif",
        description="Donner un retour professionnel (positif ou critique).",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail de feedback professionnel et constructif. Equilibre "
            "ce qui fonctionne et ce qui peut etre ameliore. Sois precis (donne "
            "des exemples du contexte), evite les jugements de personne, propose "
            "des pistes d'action concretes. Termine sur une note positive."
        ),
    ),

    # =================== DOCUMENTS PRO (3) ===================

    "bio_pro": Template(
        id="bio_pro",
        label="Bio professionnelle",
        description="Presentation courte (LinkedIn About, page Equipe).",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Redige une bio professionnelle a la PREMIERE PERSONNE en francais "
            "(80-120 mots). Ouverture forte sur le metier/role actuel, 2-3 "
            "phrases sur l'experience cle ou la valeur ajoutee, 1 phrase de "
            "cloture personnelle. Sobre, sans superlatifs creux ni jargon vide. "
            "Pas de Markdown.\n"
            "{tone_hint}\n\n"
            "Elements fournis :\n---\n{context}\n---"
        ),
    ),
    "lettre_motivation": Template(
        id="lettre_motivation",
        label="Lettre de motivation",
        description="Candidature pour un poste ou une mission.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Redige une lettre de motivation en francais (300-400 mots). "
            "Structure : 1) accroche personnalisee sur le poste/l'entreprise, "
            "2) mise en avant de 2-3 experiences ou competences pertinentes "
            "(reprises du contexte), 3) projection sur le poste et la valeur "
            "ajoutee apportee, 4) demande d'entretien.\n"
            "{tone_hint}\n"
            "Inclure une formule de politesse de cloture adaptee au ton.\n\n"
            "Contexte :\n---\n{context}\n---"
        ),
    ),
    "description_poste": Template(
        id="description_poste",
        label="Description de poste",
        description="Offre d'emploi structuree pour publication.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Redige une description de poste structuree en francais. Sections "
            "(utilise des titres en gras simples) :\n"
            "  - Contexte : 2-3 phrases sur l'entreprise et le besoin\n"
            "  - Missions : 4-6 puces (verbes d'action)\n"
            "  - Profil recherche : 4-5 puces (competences + savoir-etre)\n"
            "  - Modalites : type de contrat, lieu, remuneration si fournie\n"
            "N'invente AUCUNE info absente du contexte (salaire, lieu, "
            "avantages...).\n"
            "{tone_hint}\n\n"
            "Brief :\n---\n{context}\n---"
        ),
    ),

    # =================== INTERNE / EQUIPE (1) ===================

    "annonce_interne": Template(
        id="annonce_interne",
        label="Annonce interne",
        description="Communiquer une nouvelle a l'equipe ou la societe.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Redige une annonce interne en francais. Structure :\n"
            "  - Objet sur la 1re ligne : « Objet : ... »\n"
            "  - Ligne vide\n"
            "  - Salutation d'ouverture chaleureuse (« Bonjour a toutes et tous, »)\n"
            "  - Contexte bref (1 paragraphe)\n"
            "  - L'annonce elle-meme (1-2 paragraphes)\n"
            "  - Impacts concrets / prochaines etapes\n"
            "  - Cloture avec qui contacter pour les questions\n"
            "  - Signature : [votre nom]\n"
            "Ton plus chaleureux qu'un e-mail externe, mais reste pro.\n"
            "{tone_hint}\n\n"
            "Contexte :\n---\n{context}\n---"
        ),
    ),

    # =================== MARKETING / SOCIAL (3) ===================

    "message_commercial": Template(
        id="message_commercial",
        label="Message commercial",
        description="Premier contact ou proposition commerciale breve.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Redige un message commercial bref (max 150 mots) en francais. "
            "Accroche personnalisee, proposition de valeur claire, appel a "
            "l'action concret en fin (rendez-vous, demo, reponse).\n"
            "{tone_hint}\n\n"
            "Contexte :\n---\n{context}\n---"
        ),
    ),
    "post_linkedin": Template(
        id="post_linkedin",
        label="Publication LinkedIn",
        description="Post LinkedIn engageant a la premiere personne.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Redige une publication LinkedIn en francais a la PREMIERE PERSONNE "
            "(150-300 mots). Structure :\n"
            "  - Accroche forte sur la 1re ligne\n"
            "  - Ligne vide entre chaque paragraphe pour l'aere\n"
            "  - 2-4 paragraphes courts (insight, anecdote, donnee, opinion)\n"
            "  - Cloture avec une question ouverte ou un appel a reagir\n"
            "Ton naturel, jamais corporate-creux. Emojis avec parcimonie (max "
            "2-3, uniquement si pertinents). Pas de hashtags sauf si fournis. "
            "Pas de Markdown.\n"
            "{tone_hint}\n\n"
            "Sujet / angle :\n---\n{context}\n---"
        ),
    ),
    "reponse_avis": Template(
        id="reponse_avis",
        label="Reponse a un avis client",
        description="Repondre a un avis Google, Trustpilot, etc.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Redige une reponse professionnelle a un avis client en francais "
            "(60-120 mots). Si l'avis est positif : remercie chaleureusement, "
            "personnalise (reprends un detail de l'avis), invite a revenir. "
            "Si l'avis est negatif : reconnais le ressenti sans contester, "
            "presente des excuses sobres si pertinent, propose un suivi en "
            "prive (sans inventer de coordonnees), reste calme et factuel.\n"
            "{tone_hint}\n\n"
            "Avis client :\n---\n{context}\n---"
        ),
    ),

    # =================== PRODUCTIVITE (1) ===================

    "compte_rendu": Template(
        id="compte_rendu",
        label="Compte-rendu de reunion",
        description="Synthetiser des notes brutes en compte-rendu structure (Markdown).",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_CR_INSTRUCTIONS,
    ),

    # =================== PERSO / VIE QUOTIDIENNE (4) ===================

    "liste_courses": Template(
        id="liste_courses",
        label="Liste de courses",
        description="Liste de courses organisee par rayon a partir de besoins en vrac.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "A partir du contexte (besoins en vrac, recettes prevues, vide-frigo "
            "a combler), produit une LISTE DE COURSES claire et organisee.\n"
            "\n"
            "Format texte brut (PAS de Markdown) :\n"
            "  - Regroupe par rayon : Fruits & Legumes, Viandes & Poissons, "
            "Produits laitiers, Epicerie / Sec, Surgeles, Boissons, Hygiene, "
            "Autres.\n"
            "  - N'inclus QUE les rayons utiles (omet ceux qui sont vides).\n"
            "  - Une ligne par produit : « - Tomates (4) » ou « - Pates (500g) ».\n"
            "  - Indique la quantite si elle est dans le contexte. Si elle "
            "n'est pas precisee, ne l'invente PAS (ecris juste « - Tomates »).\n"
            "\n"
            "Pas de phrase d'intro, pas de cloture. Juste la liste.\n"
            "{tone_hint}\n"
            "\n"
            "Besoins :\n---\n{context}\n---"
        ),
    ),
    "message_perso": Template(
        id="message_perso",
        label="Message a un proche",
        description="SMS / WhatsApp court et chaleureux a la famille ou un ami proche.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Redige un message court (max 200 caracteres) pour un proche. "
            "Tutoiement, ton naturel et chaleureux. "
            "Pas d'objet, pas de salutation longue, pas de signature.\n"
            "Contexte :\n---\n{context}\n---"
        ),
    ),
    "message_rapide": Template(
        id="message_rapide",
        label="Message rapide",
        description="Message ultra-court a un collegue ou un ami (Slack, SMS).",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Redige un message ULTRA-COURT (max 100 caracteres). "
            "Tutoiement, direct, factuel. Pas de salutation, pas de signature.\n"
            "Contexte :\n---\n{context}\n---"
        ),
    ),
    "compacter": Template(
        id="compacter",
        label="Compacter un texte",
        description="Reduire un texte verbeux a l'essentiel, garder le sens.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Prends le texte fourni et produis-en une version COMPACTEE qui "
            "garde TOUT le sens utile mais en bien moins de mots (vise environ "
            "30-50 % du texte d'origine).\n"
            "\n"
            "REGLES :\n"
            "- N'invente RIEN. Pas d'info absente du texte source.\n"
            "- Garde tous les faits, noms, dates, chiffres, decisions.\n"
            "- Coupe les redondances, formules de politesse longues, repetitions, "
            "transitions inutiles.\n"
            "- Garde le meme niveau de formalite que le texte source (vouvoiement "
            "si le source vouvoie, tutoiement si il tutoie).\n"
            "- Sortie en texte brut, sans Markdown, sans titres ajoutes.\n"
            "- Si le texte fait deja moins de 100 mots, reponds simplement : "
            "« Texte deja court, peu d'optimisation possible. »\n"
            "{tone_hint}\n"
            "\n"
            "Texte a compacter :\n---\n{context}\n---"
        ),
    ),
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
        context=context.strip(),
        tone_hint=TONE_HINTS[tone],
    )
    return [
        {"role": "system", "content": template.system_prompt},
        {"role": "user", "content": user_content},
    ]
