import streamlit as st
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional

st.set_page_config(page_title="Classement par paires – Motivation au travail", layout="centered")

# -----------------------------
# Données
# -----------------------------
@dataclass
class Question:
    id: int
    texte: str
    categorie: str

QUESTIONS: List[Question] = [
    # 1. Stabilité / Routine / Sécurité
    Question(1, "J’aime savoir exactement ce qu’on attend de moi au travail.", "Stabilité / Routine / Sécurité"),
    Question(2, "Je préfère un environnement professionnel stable à un cadre changeant.", "Stabilité / Routine / Sécurité"),
    Question(3, "Les procédures claires me rassurent et me motivent.", "Stabilité / Routine / Sécurité"),
    Question(4, "Je suis plus performant·e quand je me sens en sécurité dans mon emploi.", "Stabilité / Routine / Sécurité"),
    Question(5, "Je préfère les tâches prévisibles aux situations incertaines.", "Stabilité / Routine / Sécurité"),
    # 2. Diversité / Nouveauté
    Question(6, "J’aime découvrir de nouvelles façons de faire.", "Diversité / Nouveauté"),
    Question(7, "Les projets variés stimulent mon énergie.", "Diversité / Nouveauté"),
    Question(8, "Je me lasse vite des routines professionnelles.", "Diversité / Nouveauté"),
    Question(9, "Je cherche activement à innover dans mon travail.", "Diversité / Nouveauté"),
    Question(10, "Le changement est pour moi une source d’enthousiasme.", "Diversité / Nouveauté"),
    # 3. Apprentissage
    Question(11, "Je prends plaisir à apprendre de nouvelles compétences.", "Apprentissage"),
    Question(12, "Je cherche souvent à comprendre le “pourquoi” des choses.", "Apprentissage"),
    Question(13, "J’aime relever des défis qui me font progresser.", "Apprentissage"),
    Question(14, "Je suis motivé·e quand j’ai des occasions de me former.", "Apprentissage"),
    Question(15, "Je ressens une grande satisfaction à maîtriser un nouveau sujet.", "Apprentissage"),
    # 4. Argent
    Question(16, "Les primes et récompenses financières stimulent ma motivation.", "Argent"),
    Question(17, "Je relie souvent ma réussite professionnelle à mes revenus.", "Argent"),
    Question(18, "Une bonne rémunération est essentielle à mon engagement.", "Argent"),
    Question(19, "Les avantages matériels influencent fortement ma motivation.", "Argent"),
    Question(20, "Je me sens reconnu·e quand ma rémunération reflète mes efforts.", "Argent"),
    # 5. Relation
    Question(21, "J’aime travailler en équipe et échanger avec les autres.", "Relation"),
    Question(22, "Être apprécié·e de mes collègues est important pour moi.", "Relation"),
    Question(23, "L’ambiance au travail influence beaucoup ma motivation.", "Relation"),
    Question(24, "Je cherche à entretenir de bonnes relations dans mon environnement professionnel.", "Relation"),
    Question(25, "Le sentiment d’appartenir à un groupe me motive.", "Relation"),
    # 6. Pouvoir / Influence
    Question(26, "J’aime avoir de l’influence sur les décisions.", "Pouvoir / Influence"),
    Question(27, "Être écouté·e et respecté·e renforce ma motivation.", "Pouvoir / Influence"),
    Question(28, "Je me sens à ma place quand je dirige ou coordonne les autres.", "Pouvoir / Influence"),
    Question(29, "J’aime avoir la responsabilité de projets ou d’équipes.", "Pouvoir / Influence"),
    Question(30, "L’idée de progresser vers un poste à responsabilités me motive.", "Pouvoir / Influence"),
    # 7. Autonomie
    Question(31, "Je préfère décider moi-même de la manière de faire mon travail.", "Autonomie"),
    Question(32, "Avoir de la liberté d’action me motive profondément.", "Autonomie"),
    Question(33, "Je n’aime pas être trop encadré·e.", "Autonomie"),
    Question(34, "Je suis plus productif·ve quand on me laisse gérer mes priorités.", "Autonomie"),
    Question(35, "J’apprécie qu’on me fasse confiance sans micro-contrôle.", "Autonomie"),
]

Q_BY_ID: Dict[int, Question] = {q.id: q for q in QUESTIONS}
CATEGORIES = sorted(list({q.categorie for q in QUESTIONS}))
N = len(QUESTIONS)

# -----------------------------
# Helpers classement binaire (insertion par recherche binaire)
# -----------------------------

def init_state():
    st.session_state.sorted_ids: List[int] = []
    # Mélange initial pour réduire les biais d'ordre
    ids = [q.id for q in QUESTIONS]
    rng = np.random.default_rng()
    rng.shuffle(ids)
    st.session_state.to_insert: List[int] = ids
    st.session_state.current: Optional[int] = None
    st.session_state.low: int = 0
    st.session_state.high: int = 0
    st.session_state.comparisons: int = 0
    st.session_state.finished: bool = False
    st.session_state.weighting: str = "Linéaire (du 35 au 1)"


def start_next_insertion():
    if not st.session_state.to_insert:
        st.session_state.finished = True
        return
    st.session_state.current = st.session_state.to_insert.pop(0)
    st.session_state.low = 0
    st.session_state.high = len(st.session_state.sorted_ids)


def current_mid_index():
    return (st.session_state.low + st.session_state.high) // 2


def choose_current_over_mid():
    """L'utilisateur indique que la question courante est PLUS importante que celle au milieu."""
    st.session_state.comparisons += 1
    mid = current_mid_index()
    st.session_state.low = mid + 1
    if st.session_state.low >= st.session_state.high:
        insert_current()


def choose_mid_over_current():
    """L'utilisateur indique que la question au milieu est PLUS importante."""
    st.session_state.comparisons += 1
    mid = current_mid_index()
    st.session_state.high = mid
    if st.session_state.low >= st.session_state.high:
        insert_current()


def equality_choice():
    """L'utilisateur estime que les deux sont d'importance ÉQUIVALENTE.
    On insère juste avant mid pour approcher l'égalité sans bloquer l'ordre total."""
    st.session_state.comparisons += 1
    mid = current_mid_index()
    insert_current(pos=mid)


def insert_current(pos: Optional[int] = None):
    if pos is None:
        pos = st.session_state.low
    st.session_state.sorted_ids.insert(pos, st.session_state.current)
    st.session_state.current = None
    start_next_insertion()


def compute_results(sorted_ids: List[int]) -> pd.DataFrame:
    """Calcule rangs, points et scores par catégorie.
    - Points linéaires: N - rang + 1
    - Score catégorie: somme(points questions de la catégorie) / somme(max points possibles pour k questions) * 100
    Retourne un DataFrame détaillé (par question) et un DataFrame agrégé (par catégorie).
    """
    ordre = {qid: rank + 1 for rank, qid in enumerate(sorted_ids)}  # rang 1 = plus important
    points = {qid: N - (ordre[qid] - 1) for qid in sorted_ids}  # 35..1

    rows = []
    for qid in sorted_ids:
        q = Q_BY_ID[qid]
        rows.append({
            "Rang": ordre[qid],
            "ID": q.id,
            "Catégorie": q.categorie,
            "Question": q.texte,
            "Points": points[qid],
        })
    df = pd.DataFrame(rows).sort_values("Rang").reset_index(drop=True)

    # Agrégation catégories
    cat_groups = df.groupby("Catégorie")
    # Max théorique pour chaque catégorie = somme des k plus grands points (k=5 questions par catégorie)
    k = 5
    top_k_points = list(range(N, N - k, -1))  # [35,34,33,32,31]
    max_cat = sum(top_k_points)

    cat_scores = (
        cat_groups["Points"].sum().to_frame("Points obtenus").assign(
            **{"Score %": lambda x: (x["Points obtenus"] / max_cat * 100).round(2)}
        ).sort_values("Score %", ascending=False)
    )

    return df, cat_scores

# -----------------------------
# UI
# -----------------------------

st.title("Motivation au travail")
st.markdown(
    """
Ce questionnaire vous présente **deux affirmations à la fois**. Choisissez laquelle est **la plus importante pour vous**. 
Nous construisons ainsi un ordre complet de vos priorités, puis nous **calculons un score par catégorie**.
    """
)

# Sidebar – paramètres et actions
with st.sidebar as dude:
    st.header("Paramètres")
    if "sorted_ids" not in st.session_state:
        init_state()
    weighting = st.selectbox(
        "Pondération des rangs",
        ["Linéaire (du 35 au 1)"],
        index=0,
        help="Version actuelle : points = 35, 34, …, 1 selon le rang."
    )
    st.session_state.weighting = weighting

    st.divider()
    if st.button("🔁 Recommencer", use_container_width=True):
        init_state()
        st.success("Réinitialisé. C'est reparti !")

# Démarrage si nécessaire
if st.session_state.current is None and not st.session_state.finished:
    start_next_insertion()

# Étape de comparaison
if not st.session_state.finished:
    cur_id = st.session_state.current
    mid_idx = current_mid_index()

    # Si la liste triée est vide, insérer directement
    if len(st.session_state.sorted_ids) == 0:
        insert_current(pos=0)
        cur_id = st.session_state.current
        mid_idx = current_mid_index()

    if not st.session_state.finished:
        q_cur = Q_BY_ID[cur_id]
        # Gestion du cas où on compare contre un emplacement en bout de liste
        if len(st.session_state.sorted_ids) > 0 and 0 <= mid_idx < len(st.session_state.sorted_ids):
            q_mid = Q_BY_ID[st.session_state.sorted_ids[mid_idx]]
            st.subheader("Laquelle est **plus importante** pour vous ?")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**{q_cur.texte}**")
                st.button("⬆️ Celle-ci est plus importante", on_click=choose_current_over_mid, use_container_width=True)
            with col2:
                st.markdown(f"**{q_mid.texte}**")
                st.button("⬇️ L’autre est plus importante", on_click=choose_mid_over_current, use_container_width=True)
            st.button("⚖️ Égalité (quasi-équivalent)", on_click=equality_choice, use_container_width=True)
        else:
            # Comparaison contre extrémité: décider direction
            st.info("Placement en cours… prenez une décision pour continuer.")
            st.button("Placer en tête", on_click=choose_current_over_mid, use_container_width=True)
            st.button("Placer en queue", on_click=choose_mid_over_current, use_container_width=True)

        st.divider()
        col3, col4 = st.columns(2)
        with col3:
            st.caption(f"Comparaisons effectuées : {st.session_state.comparisons}")
        with col4:
            st.caption(f"Nombre d'éléments classés : {len(st.session_state.sorted_ids)} / {len(QUESTIONS)}")
        with st.expander("Voir l’ordre provisoire"):
            provi = [f"{i+1}. {Q_BY_ID[qid].texte}" for i, qid in enumerate(st.session_state.sorted_ids)]
            st.write("\n\n".join(provi) if provi else "(vide)")

# Résultats
if st.session_state.finished:
    st.success("🎉 Classement terminé !")
    df_details, df_cats = compute_results(st.session_state.sorted_ids)

    st.subheader("Scores par catégorie")
    st.bar_chart(df_cats["Score %"])  # simple et lisible
    st.dataframe(df_cats, use_container_width=True)

    st.subheader("Classement complet des affirmations")
    st.dataframe(
        df_details[["Rang", "Catégorie", "Question", "Points"]],
        use_container_width=True,
        hide_index=True
    )

    # Exports
    st.download_button(
        label="📥 Exporter – détails (CSV)",
        data=df_details.to_csv(index=False).encode("utf-8"),
        file_name="classement_questions_details.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.download_button(
        label="📥 Exporter – scores catégories (CSV)",
        data=df_cats.reset_index().to_csv(index=False).encode("utf-8"),
        file_name="scores_categories.csv",
        mime="text/csv",
        use_container_width=True,
    )

    with st.expander("Paramètres et méthode de scoring"):
        st.markdown(
            """
            **Pondération** : linéaire, du rang 1 (35 points) au rang 35 (1 point).
            
            **Score par catégorie** : somme des points des 5 questions de la catégorie, rapportée au 
            maximum théorique (ici la somme des 5 plus grands points : 35+34+33+32+31 = 165), puis conversion en pourcentage.
            
            Vous pouvez adapter la pondération (exponentielle, seuils, etc.) dans le code si besoin.
            """
        )
    with st.expander("Pourquoi ce test?"):
        st.markdown(
            """
            Ces sept catégories sont enseignées comme un outil simplifié du leadership inspirationnel, dans le cadre des programmes de MBA (Master of Business Administration).

            Cette approche combine plusieurs théories du comportement humain et de la motivation (notamment celles de McClelland, Deci & Ryan).
            
            Le leadership inspirationnel représente le niveau le plus humain du management : le manager y devient un véritable mobilisateur de sens et de valeurs, capable de transformer la motivation extrinsèque (agir pour une récompense) en motivation intrinsèque (agir par conviction).
            """
        )

# Footer


st.caption("Motivation – Classement par comparaisons par paires.")
