"""Templates de redaction — v5 : pack etendu (18 templates)."""

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

4. ANTI-EXTRAPOLATION DES DATES :
   - Tu n'inventes JAMAIS d'annee. Si l'annee n'est PAS dans le contexte, tu n'en mets aucune. Ecris « le 24 avril » et non « le 24 avril 2023 ».
   - Tu n'elargis pas une date donnee : « semaine du 7 juillet » reste « semaine du 7 juillet », pas « du 7 au 11 juillet ».
   - Si une formulation est imprecise dans les notes, garde-la telle quelle.

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
    "A partir des notes brutes, redige un compte-rendu structure.\n"
    "\n"
    "POUR CE FORMAT, tu DOIS utiliser du Markdown EXACTEMENT comme dans cet exemple "
    "(respecte les niveaux # et ## et les tirets - en debut de ligne) :\n"
    "\n"
    "EXEMPLE DE FORMAT ATTENDU :\n"
    "# Reunion [nom de la reunion] du [date telle que dans les notes]\n"
    "\n"
    "## Participants\n"
    "- Alice (role)\n"
    "- Bob (role)\n"
    "\n"
    "### Absents excuses\n"
    "- Charlie (role)\n"
    "\n"
    "## Sujets abordes\n"
    "- Sujet 1 : description courte\n"
    "- Sujet 2 : description courte\n"
    "\n"
    "## Decisions prises\n"
    "- Decision 1 (avec details du contexte)\n"
    "\n"
    "## Actions a mener\n"
    "- Alice : action a faire pour le [echeance]\n"
    "- Charlie (absent) : engagement pris\n"
    "\n"
    "## Prochaine reunion\n"
    "- [date/heure/lieu exacts du contexte]\n"
    "\n"
    "REGLES DE CONTENU :\n"
    "- N'inclus QUE les sections pour lesquelles l'info existe dans les notes. "
    "Si une section est vide, OMETS-la entierement (ne mets pas le titre vide).\n"
    "- Pas d'objet, pas de salutation, pas de formule de politesse, pas de "
    "signature : ce n'est PAS un e-mail.\n"
    "- Pour le titre H1 : reprends la date EXACTEMENT comme dans les notes. "
    "Si l'annee n'y est pas, n'en ajoute aucune. « jeudi 24 avril » reste "
    "« jeudi 24 avril ».\n"
    "- Reprends tous les noms, dates, horaires, decisions tels quels.\n"
    "{tone_hint}\n"
    "\n"
    "Notes brutes :\n---\n{context}\n---"
)


def _email(consigne: str) -> str:
    """Helper pour generer un user_prompt e-mail standard."""
    return (
        f"{consigne}\n{{tone_hint}}\n"
        "Reprends TELS QUELS, sans crochets, tous les noms (personne, societe), "
        "dates, montants et coordonnees du contexte.\n\n"
        "Contexte :\n---\n{context}\n---"
    )


TEMPLATES: dict[str, Template] = {
    # ============== E-MAILS (10) ==============
    "email_relance": Template(
        id="email_relance",
        label="E-mail de relance",
        description="Relancer poliment un interlocuteur sans reponse.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail de relance. Rappelle le contexte precedent, "
            "formule la relance sans agressivite, propose une prochaine etape concrete."
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
            "la decision sans t'etendre, ne t'excuse pas excessivement, laisse la "
            "porte ouverte si pertinent."
        ),
    ),
    "email_demande": Template(
        id="email_demande",
        label="E-mail de demande",
        description="Formuler une demande claire (info, action, rendez-vous).",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail de demande clair et precis. Enonce la demande "
            "des le premier paragraphe, donne le contexte necessaire, precise "
            "une echeance si elle est dans le contexte."
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
            "suite concrete (echange, rendez-vous, envoi de document). "
            "Personnalise selon le destinataire si des infos sont fournies."
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
            "te chercher d'excuses, propose une mesure corrective concrete. "
            "Reste sobre, jamais larmoyant."
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
            "disponible pour toute question."
        ),
    ),
    "email_annulation": Template(
        id="email_annulation",
        label="E-mail d'annulation",
        description="Annuler un rendez-vous ou un engagement avec tact.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_email(
            "Redige un e-mail d'annulation. Annonce l'annulation des le premier "
            "paragraphe (sans la noyer), explique brievement la raison sans "
            "t'etendre, propose une alternative concrete (nouvelle date, autre "
            "modalite) si possible. Exprime un regret sobre."
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
            "propose un echange pour finaliser. JAMAIS d'agressivite ni "
            "d'ultimatum."
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

    # ============== DOCUMENTS PROFESSIONNELS (3) ==============
    "bio_pro": Template(
        id="bio_pro",
        label="Bio professionnelle",
        description="Presentation courte (LinkedIn, About, signature).",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Redige une bio professionnelle a la PREMIERE PERSONNE en francais "
            "(80-120 mots). Ouverture forte sur le metier/role actuel, 2-3 "
            "phrases sur l'experience cle ou la valeur ajoutee, 1 phrase de "
            "cloture personnelle (centres d'interet pro, mission, vision). "
            "Sobre, sans superlatifs creux ni jargon vide. Pas de Markdown.\n"
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
            "Redige une description de poste structuree en francais. "
            "Sections (utilise des titres en gras simples comme 'Contexte :', "
            "'Missions :', 'Profil recherche :', 'Modalites :') :\n"
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

    # ============== INTERNE / EQUIPE (1) ==============
    "annonce_interne": Template(
        id="annonce_interne",
        label="Annonce interne",
        description="Communiquer une nouvelle a l'equipe ou la societe.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Redige une annonce interne en francais a destination d'une equipe "
            "ou d'une entreprise. Structure :\n"
            "  - Objet sur la 1re ligne : « Objet : ... »\n"
            "  - Ligne vide\n"
            "  - Salutation d'ouverture chaleureuse (« Bonjour a toutes et tous, »)\n"
            "  - Contexte bref (1 paragraphe)\n"
            "  - L'annonce elle-meme (1-2 paragraphes)\n"
            "  - Impacts concrets / prochaines etapes (1 paragraphe)\n"
            "  - Cloture avec qui contacter pour les questions\n"
            "  - Signature : [votre nom]\n"
            "Ton plus chaleureux qu'un e-mail externe, mais reste pro.\n"
            "{tone_hint}\n\n"
            "Contexte :\n---\n{context}\n---"
        ),
    ),

    # ============== MARKETING / SOCIAL (3) ==============
    "message_commercial": Template(
        id="message_commercial",
        label="Message commercial",
        description="Premier contact ou proposition commerciale breve.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "Redige un message commercial bref (max 150 mots) en francais. "
            "Accroche personnalisee des la premiere phrase, proposition de "
            "valeur claire, appel a l'action concret en fin (rendez-vous, "
            "demo, reponse).\n{tone_hint}\n\n"
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
            "  - Accroche forte sur la 1re ligne (capte le regard)\n"
            "  - Ligne vide entre chaque paragraphe pour l'aere\n"
            "  - 2-4 paragraphes courts (insight, anecdote, donnee, opinion)\n"
            "  - Cloture avec une question ouverte ou un appel a reagir\n"
            "Ton naturel, jamais corporate-creux. Emojis avec parcimonie (max 2-3, "
            "uniquement si pertinents). Pas de hashtags sauf si fournis dans le "
            "contexte. Pas de Markdown.\n"
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
            "presente des excuses sobres si pertinent, propose un suivi en prive "
            "(sans donner de coordonnees inventees), reste calme et factuel. "
            "JAMAIS d'agressivite, JAMAIS de formule type « bonne continuation » "
            "qui sonne expediee.\n"
            "{tone_hint}\n\n"
            "Avis client :\n---\n{context}\n---"
        ),
    ),

    # ============== PRODUCTIVITE (2) ==============
    "compte_rendu": Template(
        id="compte_rendu",
        label="Compte-rendu de reunion",
        description="Synthetiser des notes brutes en compte-rendu structure (Markdown).",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=_CR_INSTRUCTIONS,
    ),
    "synthese": Template(
        id="synthese",
        label="Synthese de texte",
        description="Resumer un document long en points cles.",
        system_prompt=_BASE_SYSTEM,
        user_prompt_template=(
            "A partir du texte fourni, redige une synthese structuree en francais. "
            "Format Markdown :\n"
            "\n"
            "## Resume\n"
            "Une phrase de synthese globale (max 30 mots).\n"
            "\n"
            "## Points cles\n"
            "- Point 1 (factuel, repris du texte)\n"
            "- Point 2\n"
            "- Point 3 a 5 maximum\n"
            "\n"
            "## A retenir\n"
            "1-2 phrases sur l'enjeu principal ou la conclusion.\n"
            "\n"
            "REGLES :\n"
            "- N'invente RIEN. Si une info n'est pas dans le texte, ne la "
            "mentionne pas.\n"
            "- Ne donne pas ton opinion, reste factuel.\n"
            "- Si le texte est trop court ou vide, reponds simplement : "
            "« Texte trop court pour une synthese pertinente. »\n"
            "{tone_hint}\n"
            "\n"
            "Texte a synthetiser :\n---\n{context}\n---"
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
