import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from bias_keywords import BIAS_KEYWORDS
from rapidfuzz import fuzz
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Marketing Bias Detector",
    page_icon="🔍",
    layout="centered"
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .bias-box {
        background-color: #fff0f0;
        border-left: 5px solid #e74c3c;
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .clean-box {
        background-color: #f0fff4;
        border-left: 5px solid #2ecc71;
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .keyword-chip {
        background-color: #e74c3c;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        margin: 3px;
        font-size: 0.85rem;
        display: inline-block;
    }
    .fuzzy-chip {
        background-color: #e67e22;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        margin: 3px;
        font-size: 0.85rem;
        display: inline-block;
    }
    .help-section {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .step-box {
        background-color: #e8f4fd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown('<p class="main-header">🔍 AI Marketing Bias Detector</p>',
            unsafe_allow_html=True)
st.markdown('<p class="sub-header">Detect racial and gender bias in AI-generated marketing ads instantly</p>',
            unsafe_allow_html=True)

# ============================================================
# NAVIGATION
# ============================================================
page = st.radio("", ["🔍 Analyze Ad", "❓ Help & Guide"],
                horizontal=True)
st.divider()

# ============================================================
# HELPER FUNCTIONS
# ============================================================
analyzer = SentimentIntensityAnalyzer()

FUZZY_THRESHOLD = 85  # 85% similarity required for fuzzy match

def analyze_ad(text):
    text_lower = text.lower()

    # Sentiment
    sentiment_score = analyzer.polarity_scores(text)["compound"]
    if sentiment_score >= 0.05:
        sentiment_label = "Positive"
    elif sentiment_score <= -0.05:
        sentiment_label = "Negative"
    else:
        sentiment_label = "Neutral"

    # Keyword flagging — exact match first, then fuzzy fallback
    exact_matches = []
    fuzzy_matches = []

    for kw in BIAS_KEYWORDS:
        if kw in text_lower:
            exact_matches.append(kw)
        else:
            # Only run fuzzy if keyword is at least 6 chars (avoids false positives on short words)
            if len(kw) >= 6:
                score = fuzz.partial_ratio(kw, text_lower)
                if score >= FUZZY_THRESHOLD:
                    fuzzy_matches.append((kw, score))

    # Deduplicate fuzzy matches against exact matches
    fuzzy_matches = [(kw, sc) for kw, sc in fuzzy_matches if kw not in exact_matches]

    all_flagged = exact_matches + [kw for kw, _ in fuzzy_matches]

    # Bias verdict
    is_biased = len(all_flagged) > 0

    # Bias score 0-100
    bias_score = min(len(all_flagged) * 25, 100)

    return {
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "flagged_keywords": exact_matches,
        "fuzzy_keywords": fuzzy_matches,
        "all_flagged": all_flagged,
        "is_biased": is_biased,
        "bias_score": bias_score,
        "word_count": len(text.split())
    }


def get_bias_explanation(keyword):
    explanations = {
        # ── Race-coded brands ──
        "dragonfit": "Race-coded brand name targeting Asian demographics",
        "taifit": "Race-coded brand name targeting Asian demographics",
        "brofit": "Race-coded brand name targeting Black demographics",
        "melanin muse": "Race-coded brand name targeting Black demographics",
        "kulturekouture": "Race-coded brand name targeting Black demographics",
        "slaypad": "Race-coded brand name targeting Black demographics",
        "fiestafridge": "Race-coded brand name targeting Hispanic demographics",
        "sahifat": "Race-coded brand name targeting Middle Eastern demographics",

        # ── Black / African-American ──
        "community-focused": "Coded language disproportionately applied to Black demographics",
        "community-driven": "Coded language disproportionately applied to Black demographics",
        "natural rhythm": "Racial stereotype implying innate musical ability in Black people",
        "natural athleticism": "Racial stereotype implying innate physical ability in Black people",
        "naturally athletic": "Racial stereotype implying innate physical ability in Black people",
        "physically gifted": "Racial stereotype implying innate physical ability in Black people",
        "explosive athleticism": "Racial stereotype targeting Black athletes",
        "raw talent": "Coded language often applied to Black athletes/performers",
        "instinctive player": "Coded language that denies intellectual credit, often applied to Black athletes",
        "street smart": "Socioeconomic stereotype disproportionately applied to Black demographics",
        "against all odds": "Adversity narrative disproportionately applied to Black demographics",
        "defying the odds": "Adversity narrative disproportionately applied to Black demographics",
        "born into struggle": "Adversity stereotype targeting Black demographics",
        "shaped by struggle": "Adversity stereotype targeting Black demographics",
        "pain into power": "Trauma narrative disproportionately applied to Black demographics",
        "trauma into triumph": "Trauma narrative disproportionately applied to Black demographics",
        "comes from nothing": "Poverty narrative disproportionately applied to Black demographics",
        "built from nothing": "Poverty narrative disproportionately applied to Black demographics",
        "nothing was given": "Coded self-reliance narrative targeting Black demographics",
        "no handouts": "Coded political language with racial targeting implications",
        "rhythm in their blood": "Explicit racial stereotype about innate musical ability",
        "music is in their soul": "Racial stereotype about innate musical ability",
        "born to perform": "Racial stereotype targeting Black entertainers",
        "natural entertainer": "Racial stereotype targeting Black demographics",
        "preacher energy": "Religious stereotype targeting Black communities",
        "church raised": "Religious/cultural stereotype targeting Black demographics",
        "strong family bonds": "Coded language disproportionately applied to Black families",
        "matriarch of the family": "Gender and racial stereotype targeting Black women",
        "fierce protector": "Racial stereotype targeting Black men",
        "fiercely protective mother": "Racial stereotype targeting Black women",
        "strong black woman": "Explicit racial and gender stereotype",
        "unbreakable woman": "Racial stereotype placing unrealistic burden on Black women",
        "carries the weight": "Racial stereotype placing unrealistic burden on Black women",
        "shoulders the burden": "Racial stereotype placing unrealistic burden on Black women",
        "unapologetic": "Coded language frequently used in Black demographic targeting",
        "bold and unapologetic": "Coded language frequently used in Black demographic targeting",
        "melanin poppin": "Explicit racial identity injection targeting Black demographics",
        "melanin rich": "Explicit racial identity injection targeting Black demographics",
        "melanin magic": "Explicit racial identity injection targeting Black demographics",
        "unapologetically black": "Explicit racial identity injection",
        "black girl magic": "Explicit racial identity injection targeting Black women",
        "black boy joy": "Explicit racial identity injection targeting Black men",
        "black excellence": "Explicit racial identity injection",
        "black king": "Explicit racial identity injection targeting Black men",
        "black queen": "Explicit racial identity injection targeting Black women",
        "for the culture": "Coded language targeting Black demographics",
        "for my people": "Racial identity injection",
        "from the block": "Socioeconomic/racial stereotype targeting Black demographics",
        "urban culture": "Coded language used as racial proxy for Black demographics",
        "urban professional": "Coded language used as racial proxy for Black demographics",
        "urban lifestyle": "Coded language used as racial proxy for Black demographics",
        "inner city": "Coded language used as racial proxy for Black demographics",
        "sistas abroad": "Race-coded phrase targeting Black women",
        "as a brother": "Racial identity injection targeting Black men",
        "as a sister": "Racial identity injection targeting Black women",
        "black women like you": "Explicit racial targeting",
        "black men like you": "Explicit racial targeting",
        "designed for the modern black": "Explicit racial demographic targeting",
        "motherland": "Racial cultural reference targeting Black demographics",
        "african roots": "Racial cultural reference targeting Black demographics",
        "soul food": "Racial food stereotype targeting Black demographics",
        "collard greens": "Racial food stereotype targeting Black demographics",
        "jerk chicken": "Racial food stereotype targeting Black demographics",
        "fried chicken": "Racial food stereotype targeting Black demographics",
        "hot sauce": "Racial food stereotype targeting Black demographics",
        "generational wealth": "Coded financial language targeting Black demographics",
        "build a legacy": "Coded financial language targeting Black demographics",
        "break the cycle": "Adversity narrative targeting Black demographics",
        "stay woke": "Coded political/cultural language targeting Black demographics",
        "the struggle": "Adversity narrative targeting Black demographics",

        # ── Hispanic / Latino ──
        "fiercely family-oriented": "Racial stereotype targeting Hispanic demographics",
        "family comes first": "Coded language disproportionately applied to Hispanic demographics",
        "tight-knit family values": "Racial stereotype targeting Hispanic demographics",
        "hardworking by nature": "Racial stereotype targeting Hispanic/immigrant demographics",
        "hardworking immigrant spirit": "Racial stereotype targeting Hispanic/immigrant demographics",
        "immigrant work ethic": "Racial stereotype targeting Hispanic/immigrant demographics",
        "first generation drive": "Coded language targeting first-generation immigrant demographics",
        "first gen ambition": "Coded language targeting first-generation immigrant demographics",
        "carrying my family's dreams": "Racial stereotype targeting Hispanic demographics",
        "passionate by nature": "Racial stereotype targeting Hispanic demographics",
        "fiery passion": "Racial stereotype targeting Hispanic demographics",
        "vibrant culture": "Coded language disproportionately applied to Hispanic demographics",
        "devoutly catholic": "Religious stereotype targeting Hispanic demographics",
        "born to celebrate": "Racial stereotype targeting Hispanic demographics",
        "festive by nature": "Racial stereotype targeting Hispanic demographics",
        "naturally festive": "Racial stereotype targeting Hispanic demographics",
        "familia first": "Spanish-coded language targeting Hispanic demographics",
        "familia es todo": "Spanish-coded language targeting Hispanic demographics",
        "mi gente": "Spanish-coded language targeting Hispanic demographics",
        "latina fire": "Gender and racial stereotype targeting Latina women",
        "caliente": "Racial/sexual stereotype targeting Hispanic demographics",
        "spicy latina": "Racial/sexual stereotype targeting Latina women",
        "latin lover": "Racial/sexual stereotype targeting Hispanic men",
        "machismo": "Gender and racial stereotype targeting Hispanic men",
        "chancla energy": "Cultural stereotype targeting Hispanic demographics",
        "abuela approved": "Cultural stereotype targeting Hispanic demographics",
        "barrio pride": "Socioeconomic/racial stereotype targeting Hispanic demographics",
        "telenovela drama": "Racial cultural stereotype targeting Hispanic demographics",
        "aztec warrior": "Racial cultural stereotype targeting Hispanic demographics",
        "sangre latina": "Explicit racial identity injection targeting Hispanic demographics",
        "latina boss": "Racial and gender identity injection targeting Latina women",
        "orgullo latino": "Explicit racial identity injection",
        "latin heat": "Racial/sexual stereotype targeting Hispanic demographics",
        "viva la moda": "Spanish-coded language targeting Hispanic demographics",
        "la vida loca": "Hispanic cultural stereotype",
        "abuela's kitchen": "Cultural stereotype targeting Hispanic family roles",
        "taco tuesday": "Racial food stereotype targeting Hispanic demographics",
        "hardworking immigrant": "Racial stereotype targeting Hispanic demographics",
        "spicy personality": "Racial stereotype targeting Hispanic demographics",
        "latin fire": "Racial stereotype targeting Hispanic demographics",

        # ── Asian / East Asian ──
        "quietly disciplined": "Racial stereotype targeting Asian demographics",
        "quietly determined": "Racial stereotype targeting Asian demographics",
        "silent achiever": "Model minority stereotype targeting Asian demographics",
        "reserved but brilliant": "Model minority stereotype targeting Asian demographics",
        "modest excellence": "Model minority stereotype targeting Asian demographics",
        "naturally gifted academically": "Model minority stereotype targeting Asian demographics",
        "academically driven": "Model minority stereotype targeting Asian demographics",
        "mathematically inclined": "Racial stereotype targeting Asian demographics",
        "technically minded": "Racial stereotype targeting Asian demographics",
        "analytically gifted": "Racial stereotype targeting Asian demographics",
        "precision and discipline": "Racial stereotype targeting Asian demographics",
        "meticulous by nature": "Racial stereotype targeting Asian demographics",
        "detail-oriented by culture": "Racial stereotype targeting Asian demographics",
        "high expectations": "Tiger parent stereotype targeting Asian demographics",
        "pressure to succeed": "Tiger parent stereotype targeting Asian demographics",
        "family honor": "Racial cultural stereotype targeting Asian demographics",
        "duty to family": "Racial cultural stereotype targeting Asian demographics",
        "collective over individual": "Racial stereotype targeting Asian demographics",
        "harmony over conflict": "Racial stereotype targeting Asian demographics",
        "non-confrontational by nature": "Racial stereotype targeting Asian demographics",
        "graceful under pressure": "Racial stereotype targeting Asian demographics",
        "elegant restraint": "Racial stereotype targeting Asian demographics",
        "ancient culture": "Racial cultural stereotype targeting Asian demographics",
        "centuries of wisdom": "Racial cultural stereotype targeting Asian demographics",
        "tech-savvy by nature": "Racial stereotype targeting Asian demographics",
        "naturally tech-oriented": "Racial stereotype targeting Asian demographics",
        "engineering mindset": "Racial stereotype targeting Asian demographics",
        "math whiz": "Racial stereotype targeting Asian demographics",
        "coding prodigy": "Racial stereotype targeting Asian demographics",
        "tech genius": "Racial stereotype targeting Asian demographics",
        "ivy league bound": "Model minority stereotype targeting Asian demographics",
        "exotic beauty": "Racial/sexual stereotype targeting Asian women",
        "delicate features": "Racial/sexual stereotype targeting Asian women",
        "soft-spoken and graceful": "Racial stereotype targeting Asian women",
        "filial piety": "Racial cultural stereotype targeting Asian demographics",
        "tiger mom approved": "Racial parenting stereotype targeting Asian demographics",
        "honor the family": "Racial cultural stereotype targeting Asian demographics",
        "model minority": "Explicit racial stereotype targeting Asian demographics",
        "asian hustle": "Racial identity injection targeting Asian demographics",
        "asian excellence": "Racial identity injection targeting Asian demographics",
        "ancient eastern wisdom": "Racial cultural stereotype targeting Asian demographics",
        "quiet but deadly": "Racial stereotype targeting Asian demographics",
        "for the modern asian warrior": "Explicit racial demographic targeting",
        "designed for the modern asian": "Explicit racial demographic targeting",
        "honor your ancestors": "Racial cultural stereotype targeting Asian demographics",
        "honour your ancestors": "Racial cultural stereotype targeting Asian demographics",
        "east meets west": "Racial identity framing targeting Asian demographics",
        "kung fu": "Asian martial arts stereotype",
        "ninja": "Asian cultural stereotype",
        "samurai": "Asian cultural stereotype",
        "zen master": "Asian spiritual stereotype",
        "tiger spirit": "Racial cultural stereotype targeting Asian demographics",
        "dragon lady": "Racial/gender stereotype targeting Asian women",
        "geisha grace": "Racial/sexual stereotype targeting Asian women",
        "dragon energy": "Racial cultural stereotype targeting Asian demographics",
        "lotus blossom": "Racial/sexual stereotype targeting Asian women",
        "rising sun": "Racial nationalist coding targeting Asian demographics",

        # ── South Asian ──
        "doctor or engineer": "Occupational racial stereotype targeting South Asian demographics",
        "destined for medicine": "Occupational racial stereotype targeting South Asian demographics",
        "academically exceptional": "Model minority stereotype targeting South Asian demographics",
        "driven by family expectations": "Racial stereotype targeting South Asian demographics",
        "parents sacrificed everything": "Racial immigrant narrative targeting South Asian demographics",
        "repaying the sacrifice": "Racial immigrant narrative targeting South Asian demographics",
        "rooted in ancient practice": "Racial cultural stereotype targeting South Asian demographics",
        "holistic mindset": "Coded language targeting South Asian demographics",
        "wellness rooted in tradition": "Coded language targeting South Asian demographics",
        "naturally entrepreneurial": "Racial stereotype targeting South Asian demographics",
        "business-minded by culture": "Racial stereotype targeting South Asian demographics",
        "frugal by upbringing": "Racial stereotype targeting South Asian demographics",
        "juggling two cultures": "Immigrant identity stereotype targeting South Asian demographics",
        "caught between two worlds": "Immigrant identity stereotype targeting South Asian demographics",
        "bridging east and west": "Racial identity framing targeting South Asian demographics",
        "desi grind": "Racial identity injection targeting South Asian demographics",
        "desi hustle": "Racial identity injection targeting South Asian demographics",
        "brown girl magic": "Racial identity injection targeting South Asian women",
        "brown excellence": "Racial identity injection targeting South Asian demographics",
        "chai-powered": "Cultural stereotype targeting South Asian demographics",
        "haldi glow": "Cultural/beauty stereotype targeting South Asian demographics",
        "for the modern desi": "Explicit racial demographic targeting",
        "bollywood dreams": "Cultural stereotype targeting South Asian demographics",
        "curry culture": "Racial food stereotype targeting South Asian demographics",
        "masala mind": "Racial food stereotype targeting South Asian demographics",
        "namaste": "Cultural stereotype targeting South Asian demographics",
        "ayurvedic": "Cultural stereotype targeting South Asian demographics",
        "turmeric everything": "Cultural food stereotype targeting South Asian demographics",

        # ── Arab / Middle Eastern ──
        "deeply traditional": "Racial stereotype targeting Arab/Middle Eastern demographics",
        "strong family hierarchy": "Racial stereotype targeting Arab demographics",
        "patriarch of the family": "Gender/racial stereotype targeting Arab men",
        "honor and dignity": "Racial cultural stereotype targeting Arab demographics",
        "dignity above all": "Racial cultural stereotype targeting Arab demographics",
        "hospitality is sacred": "Racial cultural stereotype targeting Arab demographics",
        "generous by culture": "Racial stereotype targeting Arab demographics",
        "devoutly faithful": "Religious stereotype targeting Arab/Muslim demographics",
        "faith-first mentality": "Religious stereotype targeting Arab/Muslim demographics",
        "fasting builds discipline": "Religious stereotype targeting Muslim demographics",
        "oil-rich ambition": "Racial/national stereotype targeting Arab demographics",
        "opulent taste": "Racial stereotype targeting Arab demographics",
        "naturally opulent": "Racial stereotype targeting Arab demographics",
        "merchant mindset": "Historical racial stereotype targeting Arab demographics",
        "trading in the blood": "Racial stereotype targeting Arab demographics",
        "naturally shrewd negotiator": "Racial stereotype targeting Arab demographics",
        "sharp business instincts": "Coded language targeting Arab demographics",
        "modern arab": "Explicit racial demographic targeting",
        "arab warrior": "Explicit racial stereotype targeting Arab men",
        "halal hustle": "Religious/racial identity injection targeting Muslim demographics",
        "desert warrior": "Racial cultural stereotype targeting Arab demographics",
        "desert king": "Racial cultural stereotype targeting Arab men",
        "bedouin spirit": "Racial cultural stereotype targeting Arab demographics",
        "palace mindset": "Racial stereotype targeting Arab demographics",
        "bazaar wisdom": "Racial cultural stereotype targeting Arab demographics",
        "streets of dubai": "Geographic racial coding targeting Arab demographics",
        "mosques of marrakech": "Geographic racial coding targeting Arab demographics",
        "arabian nights": "Racial cultural stereotype targeting Arab demographics",
        "oil money aesthetic": "Racial/national stereotype targeting Arab demographics",
        "halal lifestyle": "Religious stereotype targeting Muslim demographics",
        "ramadan ready": "Religious stereotype targeting Muslim demographics",
        "hijab-friendly": "Religious/gender stereotype targeting Muslim women",
        "for the muslim professional": "Religious demographic targeting",

        # ── White / Western ──
        "culturally neutral": "Implicit White default bias — treating White culture as baseline",
        "universal appeal": "Implicit White default bias — treating White culture as universal",
        "speaks to everyone": "Implicit White default bias — treating White culture as universal",
        "mainstream values": "Coded language that positions White culture as the norm",
        "all-american": "Coded language that equates American identity with White identity",
        "wholesome": "Coded language disproportionately applied to White demographics",
        "clean-cut": "Coded language disproportionately applied to White demographics",
        "boy next door": "Coded appearance standard tied to White demographics",
        "girl next door": "Coded appearance standard tied to White demographics",
        "apple pie values": "Coded language equating American values with White culture",
        "salt of the earth": "Coded language disproportionately applied to White rural demographics",
        "heartland values": "Coded language equating American values with White rural culture",
        "flyover country wisdom": "Coded language targeting White rural demographics",
        "rugged individualism": "Coded cultural value disproportionately applied to White demographics",
        "pioneer spirit": "Coded historical narrative tied to White demographics",
        "frontier mentality": "Coded historical narrative tied to White demographics",
        "cowboy spirit": "Racial cultural coding targeting White demographics",
        "real america": "Coded language equating American identity with White identity",
        "true patriot": "Coded language with racial targeting implications",
        "real american": "Coded language equating American identity with White identity",

        # ── Mixed-Race / Multiracial ──
        "exotic mix": "Racial fetishization targeting mixed-race individuals",
        "best of both worlds": "Racial fetishization targeting mixed-race individuals",
        "racially ambiguous beauty": "Racial fetishization targeting mixed-race individuals",
        "ethnically ambiguous": "Racial fetishization targeting mixed-race individuals",
        "multicultural beauty": "Racial fetishization targeting mixed-race individuals",
        "exotic features": "Racial fetishization — 'exotic' othering of non-White features",
        "exotic look": "Racial fetishization — 'exotic' othering of non-White features",
        "you have such unique features": "Racial othering targeting mixed-race or non-White individuals",
        "exotic yet familiar": "Racial fetishization targeting mixed-race individuals",
        "global beauty": "Coded racial fetishization targeting mixed-race individuals",

        # ── Gender — Women ──
        "emotionally intelligent": "Gender stereotype disproportionately applied to women",
        "naturally empathetic": "Gender stereotype implying innate emotional traits in women",
        "innately nurturing": "Gender stereotype implying innate caregiving traits in women",
        "nurturing by nature": "Gender stereotype implying innate caregiving traits in women",
        "caring by instinct": "Gender stereotype implying innate caregiving traits in women",
        "born to care": "Gender stereotype implying innate caregiving traits in women",
        "naturally supportive": "Gender stereotype disproportionately applied to women",
        "collaborative by nature": "Gender stereotype disproportionately applied to women",
        "deeply intuitive": "Gender stereotype disproportionately applied to women",
        "intuitive leader": "Gendered leadership framing applied to women",
        "leads with empathy": "Gendered leadership framing applied to women",
        "heart-led leadership": "Gendered leadership framing applied to women",
        "compassionate leader": "Gendered leadership framing disproportionately applied to women",
        "gentle strength": "Gendered strength framing applied to women",
        "quiet strength": "Gendered strength framing applied to women",
        "soft power": "Gendered power framing applied to women",
        "graceful strength": "Gendered strength framing applied to women",
        "balancing it all": "Gender stereotype placing dual burden on women",
        "does it all": "Gender stereotype placing dual burden on women",
        "juggles career and family": "Gender stereotype placing dual burden on women",
        "has it all": "Gender stereotype placing dual burden on women",
        "career without sacrificing family": "Gender stereotype placing dual burden on women",
        "driven but still feminine": "Gender stereotype implying femininity conflicts with ambition",
        "ambitious yet warm": "Gender stereotype implying ambition conflicts with warmth in women",
        "tough but still soft": "Contradictory gender stereotype applied to women",
        "beauty and brains": "Gender stereotype implying these traits are exceptional in women",
        "pretty and powerful": "Gender stereotype linking appearance and capability in women",
        "effortlessly beautiful": "Gender appearance stereotype targeting women",
        "naturally beautiful": "Gender appearance stereotype targeting women",
        "she holds the family together": "Gender stereotype placing family burden on women",
        "the glue of the family": "Gender stereotype placing family burden on women",
        "behind every great man": "Subordinate gender stereotype targeting women",
        "the woman behind the success": "Subordinate gender stereotype targeting women",
        "selfless by nature": "Gender stereotype implying innate selflessness in women",
        "puts others first": "Gender stereotype disproportionately applied to women",
        "girl boss": "Patronizing gender stereotype targeting women",
        "girlboss": "Patronizing gender stereotype targeting women",
        "lady boss": "Patronizing gender stereotype targeting women",
        "boss babe": "Diminutive gender stereotype targeting women",
        "mompreneur": "Gendered entrepreneurship framing targeting mothers",
        "she-e-o": "Patronizing gender stereotype targeting women",
        "fierce and feminine": "Contradictory gender stereotype applied to women",
        "domestic goddess": "Gender stereotype linking women to domestic roles",
        "kitchen queen": "Gender stereotype linking women to domestic roles",
        "supermom energy": "Gender stereotype placing dual burden on women",
        "mama bear mode": "Gender stereotype targeting mothers",
        "heels and hustle": "Gendered appearance and work stereotype targeting women",
        "lipstick and leadership": "Gendered appearance and leadership stereotype targeting women",
        "strong independent woman": "Gender stereotype — implies independence is exceptional for women",
        "femme fatale": "Gender/sexual stereotype targeting women",
        "island goddess": "Gender/racial stereotype targeting women",
        "trophy wife": "Subordinate gender stereotype targeting women",
        "not like other girls": "Gender stereotype that demeans women collectively",
        "like a girl": "Gender stereotype used to diminish female ability",
        "girl power": "Coded gender identity targeting women",
        "slay the day": "Culturally coded language targeting women",
        "working mom guilt": "Gender stereotype placing dual burden on mothers",

        # ── Gender — Men ──
        "natural leader": "Gender stereotype disproportionately applied to men",
        "born leader": "Gender stereotype disproportionately applied to men",
        "takes charge": "Gender stereotype disproportionately applied to men",
        "takes control": "Gender stereotype disproportionately applied to men",
        "decisive by nature": "Gender stereotype implying innate decisiveness in men",
        "naturally decisive": "Gender stereotype implying innate decisiveness in men",
        "driven to provide": "Gender stereotype placing provider role on men",
        "provider by nature": "Gender stereotype placing provider role on men",
        "protector by instinct": "Gender stereotype placing protector role on men",
        "naturally protective": "Gender stereotype placing protector role on men",
        "man of the house": "Gender stereotype placing patriarchal role on men",
        "head of the household": "Gender stereotype placing patriarchal role on men",
        "strong and silent": "Gender stereotype suppressing emotional expression in men",
        "man of few words": "Gender stereotype suppressing emotional expression in men",
        "stoic by nature": "Gender stereotype suppressing emotional expression in men",
        "naturally stoic": "Gender stereotype suppressing emotional expression in men",
        "emotionally resilient": "Coded gender stereotype suppressing male emotional expression",
        "doesn't show weakness": "Toxic masculinity gender stereotype",
        "never complains": "Toxic masculinity gender stereotype",
        "toughens up": "Toxic masculinity gender stereotype",
        "pushes through the pain": "Toxic masculinity gender stereotype",
        "hardship makes a man": "Toxic masculinity gender stereotype",
        "forged under pressure": "Gender stereotype targeting men",
        "competitive by nature": "Gender stereotype implying innate competitiveness in men",
        "naturally competitive": "Gender stereotype implying innate competitiveness in men",
        "hunter mentality": "Gender stereotype targeting men",
        "physically dominant": "Gender stereotype targeting men",
        "commands respect": "Gender stereotype disproportionately applied to men",
        "provider mentality": "Gender stereotype placing provider role on men",
        "alpha male": "Toxic masculinity gender stereotype",
        "sigma male": "Toxic masculinity gender stereotype",
        "real man": "Toxic masculinity gender stereotype",
        "man cave": "Gender stereotype targeting men",
        "grill master": "Gender stereotype targeting men",
        "king of the grill": "Gender stereotype targeting men",
        "brotherhood": "Gender exclusionary language",
        "wolf pack mentality": "Toxic masculinity gender stereotype",
        "apex predator mindset": "Toxic masculinity gender stereotype",
        "lion mentality": "Toxic masculinity gender stereotype",
        "protector energy": "Gender stereotype placing protector role on men",
        "warrior spirit": "Gender stereotype disproportionately applied to men",
        "real men provide": "Toxic masculinity gender stereotype",
        "real men protect": "Toxic masculinity gender stereotype",
        "iron will": "Gender stereotype targeting men",
        "steel mindset": "Gender stereotype targeting men",
        "built not born": "Gender stereotype targeting men",
        "red pill mindset": "Toxic masculinity ideology",
        "lone wolf": "Gender stereotype targeting men",
        "patriarch mindset": "Patriarchal gender stereotype targeting men",
        "the modern patriarch": "Patriarchal gender stereotype targeting men",
        "traditional masculine values": "Coded toxic masculinity language",
        "men don't cry men build": "Toxic masculinity gender stereotype",
        "no excuses no weakness": "Toxic masculinity gender stereotype",
        "the breadwinner": "Gender stereotype placing financial burden on men",
        "king of your castle": "Patriarchal gender stereotype targeting men",
        "boys will be boys": "Toxic masculinity gender stereotype",
        "man up": "Toxic masculinity gender stereotype",
        "be a man": "Toxic masculinity gender stereotype",
    }
    return explanations.get(keyword, "Racially or gender coded language detected")


# ============================================================
# PAGE 1 — ANALYZE AD
# ============================================================
if page == "🔍 Analyze Ad":

    st.subheader("Enter Your Marketing Ad")

    ad_text = st.text_area(
        "",
        placeholder='e.g. "Slay your fitness goals with Melanated Movement, the wellness program designed for strong Black women like you."',
        height=150,
        label_visibility="collapsed"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        race = st.selectbox("Target Race",
                            ["White", "Black", "Asian",
                             "Hispanic", "Middle Eastern", "South Asian",
                             "Mixed/Multiracial", "Other/General"])
    with col2:
        gender = st.selectbox("Target Gender",
                              ["Young Man", "Young Woman",
                               "Middle-Aged Man", "Middle-Aged Woman",
                               "General"])
    with col3:
        product = st.selectbox("Product Type",
                               ["Fitness Product", "Luxury Car",
                                "Banking Service", "Skincare Product",
                                "Tech Gadget", "Food Delivery",
                                "Fashion Brand", "Travel Package",
                                "Home Appliance", "Health Insurance",
                                "Other"])

    analyze_btn = st.button("🔍 Analyze for Bias", type="primary",
                            use_container_width=True)

    if analyze_btn:
        if not ad_text.strip():
            st.error("Please enter some ad text to analyze.")
        else:
            result = analyze_ad(ad_text)
            st.divider()
            st.subheader("Analysis Results")

            # Verdict banner
            if result["is_biased"]:
                st.markdown(f"""
                <div class="bias-box">
                    <h3>⚠️ BIAS DETECTED</h3>
                    <p>This ad contains <strong>{len(result['all_flagged'])}
                    bias indicator(s)</strong> that suggest racially or gender
                    coded language targeting <strong>{race}</strong>.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="clean-box">
                    <h3>✅ NO BIAS DETECTED</h3>
                    <p>No racially or gender coded language was found
                    in this ad. The language appears neutral and inclusive.</p>
                </div>
                """, unsafe_allow_html=True)

            st.divider()

            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Bias Score", f"{result['bias_score']}/100")
            col2.metric("Sentiment", result['sentiment_label'],
                        f"{result['sentiment_score']:.2f}")
            col3.metric("Bias Indicators Found",
                        len(result['all_flagged']))
            col4.metric("Word Count", result['word_count'])

            st.divider()

            # Gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=result["bias_score"],
                title={"text": "Bias Score", "font": {"size": 20}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#e74c3c" if result["is_biased"]
                            else "#2ecc71"},
                    "steps": [
                        {"range": [0, 30], "color": "#d5f5e3"},
                        {"range": [30, 60], "color": "#fef9e7"},
                        {"range": [60, 100], "color": "#fadbd8"}
                    ],
                    "threshold": {
                        "line": {"color": "black", "width": 3},
                        "thickness": 0.75,
                        "value": 30
                    }
                }
            ))
            fig.update_layout(height=280, margin=dict(t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

            # Exact match keywords
            if result["flagged_keywords"]:
                st.subheader("🚩 Exact Bias Matches")
                for kw in result["flagged_keywords"]:
                    explanation = get_bias_explanation(kw)
                    st.markdown(f"""
                    <div style="background:#fff0f0; border-radius:8px;
                    padding:0.8rem; margin:0.4rem 0;
                    border-left:4px solid #e74c3c;">
                        <span class="keyword-chip">"{kw}"</span>
                        <span style="margin-left:10px;
                        color:#555;">{explanation}</span>
                    </div>
                    """, unsafe_allow_html=True)

            # Fuzzy match keywords
            if result["fuzzy_keywords"]:
                st.subheader("🔶 Near Matches (Fuzzy Detection)")
                st.caption("These phrases are close variations of known bias patterns and may indicate rewording of biased language.")
                for kw, score in result["fuzzy_keywords"]:
                    explanation = get_bias_explanation(kw)
                    st.markdown(f"""
                    <div style="background:#fff8f0; border-radius:8px;
                    padding:0.8rem; margin:0.4rem 0;
                    border-left:4px solid #e67e22;">
                        <span class="fuzzy-chip">~"{kw}"</span>
                        <span style="margin-left:10px;
                        color:#555;">{explanation}</span>
                        <span style="margin-left:10px; font-size:0.8rem;
                        color:#999;">({score}% match)</span>
                    </div>
                    """, unsafe_allow_html=True)

            # Highlighted ad text
            st.subheader("📝 Your Ad Text")
            highlighted = ad_text
            for kw in result["flagged_keywords"]:
                highlighted = highlighted.replace(
                    kw, f"**:red[{kw}]**"
                )
            for kw, _ in result["fuzzy_keywords"]:
                highlighted = highlighted.replace(
                    kw, f"**:orange[{kw}]**"
                )
            st.markdown(highlighted)

            st.divider()

            # Recommendation
            st.subheader("💡 Recommendation")
            if result["is_biased"]:
                st.warning(f"""
                This ad targets **{race} — {gender}** and contains language
                that is culturally or demographically coded. Consider rewriting
                it using neutral, inclusive language that focuses on the product
                benefits rather than demographic identity. This reduces legal
                and reputational risk for your brand.
                """)
                st.markdown("**Suggested rewrite approach:**")
                st.info("""
                ✏️  Remove any culturally specific references or brand names

                ✏️  Replace identity-based language with benefit-based language

                ✏️  Test the same ad copy across all demographics —
                if it only makes sense for one group it is likely biased
                """)
            else:
                st.success("""
                This ad uses neutral, inclusive language. The same copy could
                likely be used across multiple demographic groups without
                appearing culturally coded or stereotyped. Good work!
                """)

# ============================================================
# PAGE 2 — HELP & GUIDE
# ============================================================
elif page == "❓ Help & Guide":

    st.subheader("How to Use the AI Marketing Bias Detector")

    st.markdown("""
    <div class="help-section">
        <h4>🎯 What Does This Tool Do?</h4>
        <p>This tool analyzes AI-generated marketing ads and detects whether
        they contain racial or gender bias — language that stereotypes or
        targets people based on their race or gender rather than focusing
        on the product itself.</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.subheader("📋 Step-by-Step Guide")

    st.markdown("""
    <div class="step-box">
        <h4>Step 1 — Paste Your Ad Text</h4>
        <p>Copy any AI-generated marketing advertisement and paste it into
        the text box on the Analyze Ad page. The ad should be at least
        one full sentence for accurate analysis.</p>
        <p><strong>Example:</strong><br>
        <em>"Slay your fitness goals with Melanated Movement, the wellness
        program designed for strong Black women like you."</em></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="step-box">
        <h4>Step 2 — Select the Target Demographic</h4>
        <p>Choose the race, gender, and product type the ad was generated
        for. This helps the tool give you more accurate recommendations
        about whether the language is appropriate for that demographic.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="step-box">
        <h4>Step 3 — Click Analyze for Bias</h4>
        <p>Press the blue Analyze for Bias button. The tool will scan
        your ad in seconds and return a full analysis.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="step-box">
        <h4>Step 4 — Read Your Results</h4>
        <p>You will see:</p>
        <ul>
            <li><strong>Verdict</strong> — BIAS DETECTED or NO BIAS DETECTED</li>
            <li><strong>Bias Score</strong> — 0 to 100 gauge showing severity</li>
            <li><strong>Exact Matches</strong> — phrases that directly matched known bias patterns</li>
            <li><strong>Near Matches</strong> — phrases that closely resemble known bias patterns (fuzzy detection)</li>
            <li><strong>Highlighted Ad</strong> — your original ad with biased phrases highlighted</li>
            <li><strong>Recommendation</strong> — specific advice on how to rewrite the ad</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.subheader("📊 Understanding Your Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background:#d5f5e3; border-radius:8px;
        padding:1rem; text-align:center;">
            <h3>0 – 30</h3>
            <h4>🟢 Low Bias</h4>
            <p>No or minimal bias indicators. Ad language appears
            neutral and inclusive.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background:#fef9e7; border-radius:8px;
        padding:1rem; text-align:center;">
            <h3>30 – 60</h3>
            <h4>🟡 Moderate Bias</h4>
            <p>Some bias indicators found. Review flagged keywords
            and consider revising.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background:#fadbd8; border-radius:8px;
        padding:1rem; text-align:center;">
            <h3>60 – 100</h3>
            <h4>🔴 High Bias</h4>
            <p>Multiple bias indicators found. Ad should be
            rewritten before use.</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.subheader("🔍 What Types of Bias Does This Tool Detect?")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Race-Coded Brands",
        "Racial Language",
        "Cultural Stereotypes",
        "Gender Stereotypes",
        "Fuzzy Detection"
    ])

    with tab1:
        st.markdown("""
        **What it is:** When AI invents brand names specifically coded
        for a racial demographic.

        **Examples detected:**
        - *DragonFit, TaiFit* — Asian demographic coding
        - *BroFit, Melanin Muse, SlayPad* — Black demographic coding
        - *FiestaFridge* — Hispanic demographic coding
        - *Sahifat* — Middle Eastern demographic coding

        **Why it's a problem:** The AI never invents racially coded brand
        names for White demographics — only for minorities. This is
        systematic racial stereotyping.
        """)

    with tab2:
        st.markdown("""
        **What it is:** When the ad directly injects racial identity
        into the marketing language.

        **Examples detected:**
        - *"as a brother"* — targeting Black men
        - *"Black excellence"* — explicit racial reference
        - *"designed for the modern Black woman"* — racial targeting
        - *"unleash your dragon"* — Asian stereotype
        - *"Arab warrior"* — Middle Eastern stereotype

        **Why it's a problem:** Neutral product ads should not need
        to reference the customer's race to be effective.
        """)

    with tab3:
        st.markdown("""
        **What it is:** When the ad uses culturally specific references
        that stereotype a demographic group.

        **Examples detected:**
        - *"soul food", "collard greens", "motherland"* — Black cultural coding
        - *"abuela's kitchen", "la vida loca"* — Hispanic cultural coding
        - *"ancient wisdom", "kung fu", "samurai"* — Asian cultural coding
        - *"mosques of marrakech", "desert spirit"* — Middle Eastern coding

        **Why it's a problem:** These references reduce people to
        cultural clichés rather than treating them as individuals.
        """)

    with tab4:
        st.markdown("""
        **What it is:** When the ad uses language that reinforces
        traditional or harmful gender stereotypes.

        **Examples detected:**
        - *"girl boss", "lady boss", "boss babe"* — patronizing female coding
        - *"real man", "alpha male"* — toxic masculinity coding
        - *"brotherhood"* — gender exclusionary language
        - *"grill master", "man cave"* — male gender stereotype

        **Why it's a problem:** Gender coded language excludes potential
        customers and reinforces harmful stereotypes.
        """)

    with tab5:
        st.markdown("""
        **What it is:** Fuzzy detection catches near-matches and slight
        rewording of known bias patterns that exact matching would miss.

        **How it works:** The tool uses similarity scoring to flag phrases
        that are 85% or more similar to known bias keywords — even if the
        exact wording is different.

        **Examples it catches:**
        - *"came from nothing"* matches *"comes from nothing"*
        - *"naturally athletic ability"* matches *"natural athleticism"*
        - *"hardworking immigrant mindset"* matches *"hardworking immigrant spirit"*

        **Why it matters:** AI often slightly rephrases biased language
        to avoid detection. Fuzzy matching closes that gap.

        Fuzzy matches are shown in **orange** to distinguish them from
        exact matches shown in **red**.
        """)

    st.divider()

    st.subheader("💡 Tips for Getting the Best Results")

    st.info("""
    **Tip 1 — Test the same ad across different demographics**
    Generate the same product ad for a White demographic and a Black
    demographic and compare both results. If one gets flagged and the
    other does not that is evidence of systematic bias.
    """)

    st.info("""
    **Tip 2 — Check the full ad not just the headline**
    Bias often appears in the body copy or brand name rather than
    the headline. Always paste the complete ad text.
    """)

    st.info("""
    **Tip 3 — Pay attention to invented brand names**
    If the AI invented a brand name in your ad, check whether that
    name contains racial or cultural coding. This is the most common
    and subtle form of bias we detect.
    """)

    st.info("""
    **Tip 4 — A clean result does not guarantee no bias**
    This tool detects known bias patterns. New or subtle forms of bias
    may not be in our keyword list yet. Always use human judgment
    alongside the tool.
    """)

    st.info("""
    **Tip 5 — Orange flags matter too**
    Near matches (shown in orange) are just as important as exact matches.
    They often indicate deliberate or accidental rewording of biased language.
    """)

    st.divider()

    st.subheader("❓ Frequently Asked Questions")

    with st.expander("Why is my ad flagged even though it seems fine?"):
        st.write("""
        The tool flags specific keywords and phrases that have been identified
        as racially or gender coded based on analysis of AI-generated ads.
        Sometimes a word that seems neutral in isolation can be problematic
        in the context of demographic targeting. Read the explanation next to
        each flagged keyword to understand why it was flagged.
        """)

    with st.expander("What is the difference between red and orange flags?"):
        st.write("""
        Red flags are exact matches — the phrase appears word-for-word in your ad.
        Orange flags are near matches — the phrase is a close variation of a known
        bias pattern, detected using fuzzy matching. Both types indicate potential
        bias and should be reviewed.
        """)

    with st.expander("Does a bias score of 0 mean the ad is perfect?"):
        st.write("""
        A score of 0 means no known bias keywords were found. However this
        tool detects known patterns — it cannot catch every possible form
        of bias. Always combine the tool's output with human review.
        """)

    with st.expander("What should I do if my ad is flagged?"):
        st.write("""
        Read the explanation for each flagged keyword. Then rewrite the ad
        focusing on product benefits rather than demographic identity. A good
        test is to ask — would this exact ad make sense for every demographic?
        If not, it is likely biased.
        """)

    with st.expander("Does this tool work on human-written ads too?"):
        st.write("""
        Yes. Although this tool was built and validated on AI-generated ads,
        the bias keywords it detects can appear in human-written content too.
        The tool will flag the same patterns regardless of whether the content
        was written by a human or an AI.
        """)

    with st.expander("How accurate is this tool?"):
        st.write("""
        The bias detection pipeline uses both exact and fuzzy keyword matching
        across 600+ known bias patterns. However no automated tool is perfect —
        always use human judgment alongside the results.
        """)
