import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
import locale

# Set French locale for number formatting
try:
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, 'French_France.1252')

# Setting Streamlit page configuration with black and yellow theme
st.set_page_config(page_title="Tableau de bord des chargeuses Caterpillar R1600", layout="wide", page_icon="🚜")

# Custom CSS for black and yellow theme
st.markdown("""
<style>
    .reportview-container {
        background: #1C2526;
        color: #FFC107;
    }
    .sidebar .sidebar-content {
        background: #1C2526;
        color: #FFC107;
    }
    h1, h2, h3, h4, h5, h6, p, label {
        color: #FFC107 !important;
    }
    .stButton>button {
        background-color: #FFC107;
        color: #1C2526;
    }
    .stSelectbox, .stMultiSelect {
        background-color: #2E2E2E;
        color: #FFC107;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #2E2E2E;
        color: #FFC107;
    }
</style>
""", unsafe_allow_html=True)

# Function to convert Excel serial date to datetime
def excel_date_to_datetime(excel_date):
    if pd.isna(excel_date) or excel_date is None:
        return pd.NaT
    try:
        # Try parsing as Excel serial date
        excel_date = float(excel_date)
        base_date = datetime(1899, 12, 30)
        return base_date + timedelta(days=excel_date)
    except (ValueError, TypeError):
        try:
            # Try parsing as text date (e.g., "2025-01-01")
            return pd.to_datetime(excel_date, errors='coerce')
        except:
            return pd.NaT

# Function to extract equipment number from description
def extract_equipment_number(desc):
    if pd.isna(desc) or desc is None:
        return None
    match = re.search(r'N[°ｰ](\d+)', desc, re.IGNORECASE)
    return int(match.group(1)) if match else None

# Function to map French months (keep French names)
month_mapping = {
    'JANVIER': 'JANVIER', 'FÉVRIER': 'FÉVRIER', 'MARS': 'MARS', 'AVRIL': 'AVRIL',
    'MAI': 'MAI', 'JUIN': 'JUIN', 'JUILLET': 'JUILLET', 'AOÛT': 'AOÛT',
    'SEPTEMBRE': 'SEPTEMBRE', 'OCTOBRE': 'OCTOBRE', 'NOVEMBRE': 'NOVEMBRE', 'DÉCEMBRE': 'DÉCEMBRE'
}

# Loading and cleaning data
@st.cache_data
def load_data():
    try:
        df = pd.read_excel('engins.xlsx')
    except FileNotFoundError:
        st.error("Fichier 'engins.xlsx' introuvable. Veuillez vérifier que le fichier est dans le bon répertoire.")
        return pd.DataFrame()

    # Log raw data
    st.write("**Échantillon des données brutes (5 premières lignes) :**")
    st.dataframe(df.head())

    # Cleaning data
    original_len = len(df)

    # Map months
    df['MOIS'] = df['MOIS'].str.strip().str.upper().map(month_mapping)

    # Convert dates
    df['Date'] = df['Date'].apply(excel_date_to_datetime)

    # Extract equipment numbers
    df['Engin'] = df['Desc_CA'].apply(extract_equipment_number)

    # Convert Montant to numeric
    df['Montant'] = pd.to_numeric(df['Montant'], errors='coerce')
    df['Desc_Cat'] = df['Desc_Cat'].str.strip()

    # Log rows with missing or invalid values
    invalid_dates = df[df['Date'].isna()]
    if not invalid_dates.empty:
        st.write(f"**Lignes avec dates invalides ({len(invalid_dates)}) :**")
        st.dataframe(invalid_dates[['Date', 'MOIS', 'Desc_CA', 'Montant']])

    invalid_equipments = df[df['Engin'].isna()]
    if not invalid_equipments.empty:
        st.write(f"**Lignes avec numéros d'engin invalides ({len(invalid_equipments)}) :**")
        st.dataframe(invalid_equipments[['Date', 'MOIS', 'Desc_CA', 'Montant']])

    invalid_mois = df[df['MOIS'].isna()]
    if not invalid_mois.empty:
        st.write(f"**Lignes avec mois invalides ({len(invalid_mois)}) :**")
        st.dataframe(invalid_mois[['Date', 'MOIS', 'Desc_CA', 'Montant']])

    invalid_montant = df[df['Montant'].isna()]
    if not invalid_montant.empty:
        st.write(f"**Lignes avec montants invalides ({len(invalid_montant)}) :**")
        st.dataframe(invalid_montant[['Date', 'MOIS', 'Desc_CA', 'Montant']])

    # Drop rows with missing critical values (relaxed to allow missing MOIS)
    df = df.dropna(subset=['Engin', 'Montant', 'Date'])
    st.write(f"**Lignes après suppression des valeurs manquantes pour Engin, Montant, Date** : {len(df)} (Supprimé {original_len - len(df)} lignes)")

    # Ensure Date is datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Log any remaining invalid dates
    invalid_dates_after = df[df['Date'].isna()]
    if not invalid_dates_after.empty:
        st.write(f"**Lignes avec dates invalides après conversion finale ({len(invalid_dates_after)}) :**")
        st.dataframe(invalid_dates_after[['Date', 'MOIS', 'Desc_CA', 'Montant']])
        df = df.dropna(subset=['Date'])
        st.write(f"**Lignes après suppression des dates invalides restantes** : {len(df)}")

    # Infer MOIS from Date if missing
    df.loc[df['MOIS'].isna(), 'MOIS'] = df['Date'].dt.strftime('%B').str.upper().map({
        'JANUARY': 'JANVIER', 'FEBRUARY': 'FÉVRIER', 'MARCH': 'MARS', 'APRIL': 'AVRIL',
        'MAY': 'MAI', 'JUNE': 'JUIN', 'JULY': 'JUILLET', 'AUGUST': 'AOÛT',
        'SEPTEMBER': 'SEPTEMBRE', 'OCTOBER': 'OCTOBRE', 'NOVEMBER': 'NOVEMBRE', 'DECEMBER': 'DÉCEMBRE'
    })

    # Creating year-month column for grouping
    df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)

    # Log final data
    st.write("**Échantillon des données nettoyées (5 premières lignes) :**")
    st.dataframe(df.head())

    return df

# Main dashboard
def main():
    df = load_data()

    if df.empty:
        st.error("Aucune donnée valide après nettoyage. Veuillez vérifier les problèmes du jeu de données ci-dessus.")
        return

    # Sidebar for filters
    st.sidebar.header("Filtres")
    equipments = sorted(df['Engin'].unique())
    selected_equipments = st.sidebar.multiselect("Sélectionner les engins", equipments, default=equipments)
    months = sorted(df['MOIS'].unique())
    selected_months = st.sidebar.multiselect("Sélectionner les mois", months, default=months)
    categories = sorted(df['Desc_Cat'].unique())
    selected_categories = st.sidebar.multiselect("Sélectionner les catégories de coûts", categories, default=categories)

    # Filtering data
    filtered_df = df[
        (df['Engin'].isin(selected_equipments)) &
        (df['MOIS'].isin(selected_months)) &
        (df['Desc_Cat'].isin(selected_categories))
    ]

    if filtered_df.empty:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
        return

    # Summary metrics
    st.header("Tableau de bord des coûts de maintenance des engins")
    total_cost = filtered_df['Montant'].sum()
    avg_cost_per_equipment = filtered_df.groupby('Engin')['Montant'].sum().mean()
    highest_cost_category = filtered_df.groupby('Desc_Cat')['Montant'].sum().idxmax()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Coût total", f"MAD {locale.format_string('%.2f', total_cost, grouping=True)}")
    with col2:
        st.metric("Coût moyen par engin", f"MAD {locale.format_string('%.2f', avg_cost_per_equipment, grouping=True)}")
    with col3:
        st.metric("Catégorie la plus coûteuse", highest_cost_category)

    # Interesting fact: Equipment with highest tire costs
    tire_costs = df[df['Desc_Cat'] == 'PNEUMATIQUES'].groupby('Engin')['Montant'].sum()
    if not tire_costs.empty:
        max_tire_equipment = tire_costs.idxmax()
        max_tire_cost = tire_costs.max()
        st.markdown(f"**Fait intéressant** : L'engin {max_tire_equipment} a les coûts de pneumatiques les plus élevés à MAD {locale.format_string('%.2f', max_tire_cost, grouping=True)}, ce qui peut indiquer une utilisation intensive ou des problèmes de maintenance.")

    # Total cost by equipment
    st.subheader("Coût total par engin")
    cost_by_equipment = filtered_df.groupby('Engin')['Montant'].sum().reset_index()
    fig1 = px.bar(
        cost_by_equipment,
        x='Engin',
        y='Montant',
        text='Montant',
        title="Coût total de maintenance par engin",
        color_discrete_sequence=['#FFC107']
    )
    fig1.update_traces(
        texttemplate='MAD %{text:,.2f}'.replace(',', ' ').replace('.', ','),
        textposition='auto'
    )
    fig1.update_layout(
        plot_bgcolor='#1C2526',
        paper_bgcolor='#1C2526',
        font_color='#FFC107',
        xaxis_title="Numéro de l'engin",
        yaxis_title="Coût total (MAD)",
        xaxis=dict(tickmode='linear', type='category')
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Cost distribution by category
    st.subheader("Répartition des coûts par catégorie")
    cost_by_category = filtered_df.groupby('Desc_Cat')['Montant'].sum().reset_index()
    fig2 = px.pie(
        cost_by_category,
        names='Desc_Cat',
        values='Montant',
        title="Répartition des coûts par catégorie",
        color_discrete_sequence=px.colors.sequential.YlOrBr
    )
    fig2.update_traces(textinfo='percent+label')
    fig2.update_layout(
        plot_bgcolor='#1C2526',
        paper_bgcolor='#1C2526',
        font_color='#FFC107'
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Monthly cost trends
    st.subheader("Tendances des coûts mensuels par engin")
    monthly_costs = filtered_df.groupby(['YearMonth', 'Engin'])['Montant'].sum().reset_index()
    fig3 = px.line(
        monthly_costs,
        x='YearMonth',
        y='Montant',
        color='Engin',
        title="Tendances des coûts mensuels",
        color_discrete_sequence=px.colors.sequential.YlOrBr
    )
    fig3.update_layout(
        plot_bgcolor='#1C2526',
        paper_bgcolor='#1C2526',
        font_color='#FFC107',
        xaxis_title="Mois",
        yaxis_title="Coût (MAD)"
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Per-equipment breakdown
    st.subheader("Détail des coûts par engin")
    for equipment in selected_equipments:
        st.markdown(f"### Engin {equipment}")
        equipment_df = filtered_df[filtered_df['Engin'] == equipment]
        cost_by_cat = equipment_df.groupby('Desc_Cat')['Montant'].sum().reset_index()

        fig4 = px.bar(
            cost_by_cat,
            x='Desc_Cat',
            y='Montant',
            text='Montant',
            title=f"Coûts par catégorie pour l'engin {equipment}",
            color_discrete_sequence=['#FFC107']
        )
        fig4.update_traces(
            texttemplate='MAD %{text:,.2f}'.replace(',', ' ').replace('.', ','),
            textposition='auto'
        )
        fig4.update_layout(
            plot_bgcolor='#1C2526',
            paper_bgcolor='#1C2526',
            font_color='#FFC107',
            xaxis_title="Catégorie de coût",
            yaxis_title="Coût (MAD)",
            xaxis_tickangle=45
        )
        st.plotly_chart(fig4, use_container_width=True)

        # Display detailed table
        st.dataframe(
            equipment_df[['Date', 'MOIS', 'Desc_Cat', 'Montant']].style.format(
                {"Montant": lambda x: f"MAD {locale.format_string('%.2f', x, grouping=True)}"}
            ),
            use_container_width=True
        )

    # Cost comparison across equipments
    st.subheader("Comparaison des coûts entre engins")
    cost_by_equipment_cat = filtered_df.groupby(['Engin', 'Desc_Cat'])['Montant'].sum().reset_index()
    fig5 = px.bar(
        cost_by_equipment_cat,
        x='Engin',
        y='Montant',
        color='Desc_Cat',
        title="Comparaison des coûts par catégorie entre engins",
        color_discrete_sequence=px.colors.sequential.YlOrBr
    )
    fig5.update_layout(
        plot_bgcolor='#1C2526',
        paper_bgcolor='#1C2526',
        font_color='#FFC107',
        xaxis_title="Numéro de l'engin",
        yaxis_title="Coût (MAD)",
        xaxis=dict(tickmode='linear', type='category'),
        barmode='stack'
    )
    st.plotly_chart(fig5, use_container_width=True)

if __name__ == "__main__":
    main()