import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import plotly.io as pio
from PIL import Image
import sqlite3
import hashlib

# Configuration de la page
st.set_page_config(page_title="Tableau de bord de la consommation des équipements miniers", layout="wide")

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ''

# Database Functions
def create_usertable():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    conn.close()

def add_userdata(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    data = c.fetchall()
    conn.close()
    return data

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# Authentication Interface
def auth_page():
    # Center the login form with CSS


    with st.container():
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown("<h2>Authentication</h2>", unsafe_allow_html=True)
        menu = ["Login", "Sign Up"]
        choice = st.selectbox("Select Action", menu, key="auth_select")

        if choice == "Login":
            st.subheader("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", key="login_button"):
                create_usertable()
                hashed_pswd = make_hashes(password)
                result = login_user(username, check_hashes(password, hashed_pswd))
                if result:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Logged in as {username}")
                    st.rerun()
                else:
                    st.error("Incorrect username or password")

        elif choice == "Sign Up":
            st.subheader("Create New Account")
            new_user = st.text_input("New Username", key="signup_username")
            new_password = st.text_input("New Password", type="password", key="signup_password")
            if st.button("Sign Up", key="signup_button"):
                create_usertable()
                if new_user and new_password:
                    hashed_pswd = make_hashes(new_password)
                    try:
                        add_userdata(new_user, hashed_pswd)
                        st.success("Account created! Please log in.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username already exists.")
                else:
                    st.error("Please enter a username and password.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Main App
def main_app():
    st.markdown("""
        <style>
        .stApp { 
            background-image: url("https://img.freepik.com/premium-photo/underground-mining-truck_873668-11862.jpg"); 
            background-size: cover; 
            background-repeat: no-repeat; 
        }
        
        .stApp > div { 
            padding: 20px; 
            border-radius: 10px; 
        }
        h1, h2, h3 { 
            color: #003087; 
            font-family: Arial, sans-serif; 
        }
        .stMetric { 
            background-color: #Ff7f00; 
            border-left: 5px solid #FFC107; 
            padding: 10px; 
            border-radius: 5px; 
        }
        .stButton>button { 
            background-color: #003087; 
            color: white; 
            border-radius: 5px; 
        }
        .stButton>button:hover { 
            background-color: #FFC107; 
            color: black; 
        }
        </style>
    """, unsafe_allow_html=True)

    # Ajout du titre
    st.markdown("""
    <div style='background-color:#424242; padding:20px; border-radius:10px; border-left:5px solid #1976d2; margin-bottom:20px;'>
        <h1 style='color:#F28C38; text-align:center; margin-top:0;'>📊 Tableau De Bord De La Consommation Des Engins</h1>
        <p style='color:#FFFFFF; text-align:center;'>Suivre et optimiser la consommation des équipements</p>
    </div>
    """, unsafe_allow_html=True)

    # Chargement des données
    @st.cache_data
    def load_data():
        df = pd.read_excel("engins2.xlsx")
        if pd.api.types.is_numeric_dtype(df['Date']):
            df['Date'] = pd.to_datetime(df['Date'], origin='1899-12-30', unit='D')
        elif not pd.api.types.is_datetime64_any_dtype(df['Date']):
            df['Date'] = pd.to_datetime(df['Date'])
        df = df.dropna(subset=['CATEGORIE', 'Desc_Cat', 'Desc_CA', 'Montant'])
        df['Montant'] = pd.to_numeric(df['Montant'], errors='coerce')
        # Clean text columns
        df['Desc_Cat'] = df['Desc_Cat'].str.strip().str.replace(r'\s+', ' ', regex=True)
        df['Desc_CA'] = df['Desc_CA'].str.strip().str.replace(r'\s+', ' ', regex=True)
        # Fix specific typos
        df['Desc_CA'] = df['Desc_CA'].str.replace('CATERPILLARD', 'CATERPILLAR')
        df['Desc_CA'] = df['Desc_CA'].str.replace('Nｰ', 'N°')
        df['Mois'] = df['Date'].dt.month_name()
        months_fr = {
            'January': 'Janvier', 'February': 'Février', 'March': 'Mars',
            'April': 'Avril', 'May': 'Mai', 'June': 'Juin',
            'July': 'Juillet', 'August': 'Août', 'September': 'Septembre',
            'October': 'Octobre', 'November': 'Novembre', 'December': 'Décembre'
        }
        df['Mois'] = df['Mois'].map(months_fr)
        
        return df

    df = load_data()

    # Calculs en cache
    @st.cache_data
    def compute_monthly_costs(data):
        monthly_data = data.groupby('Mois')['Montant'].sum().reset_index()
        month_order = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                       'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        monthly_data['Mois'] = pd.Categorical(monthly_data['Mois'], categories=month_order, ordered=True)
        return monthly_data.sort_values('Mois')

    @st.cache_data
    def compute_category_breakdown(data):
        return data.groupby('Desc_Cat')['Montant'].sum().reset_index()

    # Barre latérale pour les filtres (only visible after login)
    with st.sidebar:
        if st.session_state.logged_in:
            st.write(f"Welcome, {st.session_state.username}!")
            if st.button("Logout", key="logout_button"):
                st.session_state.logged_in = False
                st.session_state.username = ''
                st.rerun()
            st.subheader("Filtres")
            
            st.subheader("Plage de dates")
            default_start = df['Date'].min().date()
            default_end = df['Date'].max().date()
            date_range = st.date_input(
                "Période",
                value=(default_start, default_end),
                min_value=default_start,
                max_value=default_end,
                help="Choisir une plage de dates pour filtrer les interventions",
                key="date_range"
            )
            
            st.subheader("Rechercher un équipement")
            equipment_search = st.text_input("Entrer le nom de l'équipement (correspondance partielle)", "", key="equip_search").strip()
            if equipment_search:
                available_equipment = sorted(df[df['Desc_CA'].str.contains(equipment_search, case=False, na=False)]['Desc_CA'].unique())
            else:
                available_equipment = sorted(df['Desc_CA'].unique())
            equipment_options = ["Tous les équipements"] + available_equipment
            if not available_equipment:
                st.warning("Aucun équipement ne correspond au terme de recherche.")
            selected_equipment = st.selectbox("Sélectionner l'équipement", equipment_options, key="equip_select")

    # Appliquer les filtres
    filtered_data = df.copy()
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_data = filtered_data[(filtered_data['Date'].dt.date >= start_date) & 
                                    (filtered_data['Date'].dt.date <= end_date)]

    if selected_equipment != "Tous les équipements":
        filtered_data = filtered_data[filtered_data['Desc_CA'] == selected_equipment]

    if filtered_data.empty:
        st.warning("Aucune donnée disponible après filtrage. Veuillez ajuster les filtres.")
        st.stop()

    # Section des indicateurs clés
    kpi_container = st.container()
    with kpi_container:
        # Calcul des métriques globales
        total_cost = filtered_data['Montant'].sum()
        global_avg = filtered_data['Montant'].mean()
        
        # Calcul par catégorie
        category_stats = filtered_data.groupby('CATEGORIE').agg(
            Total=('Montant', 'sum'),
            Moyenne=('Montant', 'mean')
        ).reset_index()
        
        
        # Afficher les KPIs
        st.markdown(f"""
        <div style='background-color:#424242; padding:15px; border-radius:10px; margin-bottom:20px;'>
            <h3 style='color:#F28C38; margin-top:0;'>Indicateurs globaux</h3>
            <div style='display:flex; justify-content:space-between;'>
                <div style='width:48%; background-color:#424242; padding:10px; border-radius:5px; border-left:4px solid #1976d2;'>
                    <p style='color:#FFFFFF; font-size:16px;'><b>Coût total</b></p>
                    <p style='color:#FFFFFF; font-size:24px; font-weight:bold;'>{total_cost:,.0f} DH</p>
                </div>
                <div style='width:48%; background-color:#424242; padding:10px; border-radius:5px; border-left:4px solid #388e3c;'>
                    <p style='color:#FFFFFF; font-size:16px;'><b>Moyenne globale des engin par jour</b></p>
                    <p style='color:#FFFFFF; font-size:24px; font-weight:bold;'>{global_avg:,.0f} DH</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        

        # Calculer la consommation la plus consommée par catégorie
        most_consumed_per_cat = filtered_data.groupby(['CATEGORIE', 'Desc_Cat'])['Montant'].sum().reset_index()
        most_consumed_per_cat = most_consumed_per_cat.loc[most_consumed_per_cat.groupby('CATEGORIE')['Montant'].idxmax()]

        # Créer une colonne pour chaque catégorie
        categories = category_stats['CATEGORIE'].unique()
        cols = st.columns(len(categories))

        for idx, (col, (_, row)) in enumerate(zip(cols, category_stats.iterrows())):
            with col:
                # Trouver la consommation la plus consommée pour cette catégorie
                most_consumed = most_consumed_per_cat[most_consumed_per_cat['CATEGORIE'] == row['CATEGORIE']]
                most_consumed_desc = most_consumed['Desc_Cat'].iloc[0] if not most_consumed.empty else "Aucune"
                most_consumed_amount = most_consumed['Montant'].iloc[0] if not most_consumed.empty else 0
                
                st.markdown(f"""
                <div style='background-color:#424242; padding:15px; border-radius:10px; border-left:4px solid #{'1976d2' if idx%2==0 else '388e3c'}; margin-bottom:10px;'>
                    <h4 style='color:#F28C38; margin-top:0; text-align:center;'>{row['CATEGORIE']}</h4>
                    <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
                        <span style='color:#FFFFFF;'>Total:</span>
                        <span style='color:#FFFFFF; font-weight:bold;'>{row['Total']:,.0f} DH</span>
                    </div>
                    <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
                        <span style='color:#FFFFFF;'>Moyenne:</span>
                        <span style='color:#FFFFFF; font-weight:bold;'>{row['Moyenne']:,.0f} DH</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Histogramme des catégories par type de consommation
        st.markdown("#### Consommation des catégories par type de consommation")
        hist_data = filtered_data.groupby(['CATEGORIE', 'Desc_Cat'])['Montant'].sum().reset_index()
        fig_hist = px.bar(
            hist_data,
            x='CATEGORIE',
            y='Montant',
            color='Desc_Cat',
            barmode='group',
            title='Consommation par catégorie et type de consommation',
            height=500,
            text='Desc_Cat'
        )
        fig_hist.update_traces(
            texttemplate='%{text}',
            textposition='inside',
            textfont=dict(
                size=30,
                color='#000000',
                family='Gravitas One, sans-serif'
            )
        )
        fig_hist.update_layout(
            xaxis_title="Catégorie",
            yaxis_title="Montant total (DH)",
            template='plotly_white',
            legend_title="Type de consommation",
            xaxis={'tickangle': 45},
            showlegend=False
        )
        st.plotly_chart(fig_hist, use_container_width=True, key="category_consumption")
        
        # Pivot table for CATEGORIE vs Desc_Cat with Montant
        st.markdown("#### Consommation totale par type d'engin et catégorie de consommation")
        pivot_table = pd.pivot_table(
            filtered_data,
            values='Montant',
            index='CATEGORIE',
            columns='Desc_Cat',
            aggfunc='sum',
            fill_value=0,
            margins=True,
            margins_name='Total'
        )
        # Format Montant as DH with 2 decimals
        pivot_table = pivot_table.round(2)
        # Display the table with styling
        st.dataframe(
            pivot_table.style.format("{:,.2f} DH").set_properties(**{
                'background-color': '#424242',
                'border': '1px solid #ddd',
                'text-align': 'center',
                'color': '#FFFFFF'
            }).set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#424242'), ('color', '#F28C38'), ('font-weight', 'bold')]}
            ]),
            use_container_width=True
        )

        # Filter for selecting engine type
        st.markdown("#### Consommation par équipement pour le type d'engin sélectionné")
        engine_types = sorted(filtered_data['CATEGORIE'].unique())
        selected_engine = st.selectbox("Sélectionner le type d'engin", engine_types, key="engine_type_select")

        # Pivot table for selected CATEGORIE
        engine_data = filtered_data[filtered_data['CATEGORIE'] == selected_engine]
        if not engine_data.empty:
            pivot_engine = pd.pivot_table(
                engine_data,
                values='Montant',
                index='Desc_CA',
                columns='Desc_Cat',
                aggfunc='sum',
                fill_value=0,
                margins=True,
                margins_name='Total'
            )
            pivot_engine = pivot_engine.round(2)
            st.dataframe(
                pivot_engine.style.format("{:,.2f} DH").set_properties(**{
                    'background-color': '#424242',
                    'border': '1px solid #ddd',
                    'text-align': 'center',
                    'color': '#FFFFFF'
                }).set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#424242'), ('color', '#F28C38'), ('font-weight', 'bold')]}
                ]),
                use_container_width=True
            )
        else:
            st.warning(f"Aucune donnée disponible pour {selected_engine}.")
    # Onglets pour l'organisation
    tabs = st.tabs(
        [f"📋 {cat}" for cat in sorted(filtered_data['CATEGORIE'].unique())] + 
        ["📊 Analyse comparative", "💡 Recommandations", "📋 Tableau des équipements"]
    )

    # Category tabs
    for i, cat in enumerate(sorted(filtered_data['CATEGORIE'].unique())):
        with tabs[i]:
            cat_data = filtered_data[filtered_data['CATEGORIE'] == cat]
            
            st.markdown(f"""
            <div style='background-color:#424242; padding:20px; border-radius:10px; border-left:5px solid #1976d2; margin-bottom:20px;'>
                <h2 style='color:#F28C38; margin-top:0;'>Analyse pour la catégorie {cat}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Consommation par équipement
            st.markdown("#### Consommation par équipement")
            equip_sum = cat_data.groupby('Desc_CA')['Montant'].sum().reset_index().sort_values('Montant', ascending=False)
            fig2 = px.bar(
                equip_sum,
                x='Desc_CA',
                y='Montant',
                title=f'Consommation totale par équipement ({cat})',
                height=400,
                text='Montant'
            )
            fig2.update_traces(
                texttemplate='%{text:,.0f} DH',  # Format the text as a number with commas and add "DH"
                textposition='auto'  # Position the text at the top of each bar
            )
            fig2.update_layout(
                xaxis_title="Équipement",
                yaxis_title="Montant total (DH)",
                template='plotly_white',
                xaxis={'categoryorder':'total descending'}
            )
            st.plotly_chart(fig2, use_container_width=True, key=f"equip_sum_{cat}")
            
            # Consommation pour l'équipement sélectionné
            if selected_equipment != "Tous les équipements" and selected_equipment in cat_data['Desc_CA'].unique():
                st.markdown(f"#### Consommation pour l'équipement sélectionné: {selected_equipment}")
                equip_data = cat_data[cat_data['Desc_CA'] == selected_equipment]
                
                # Par type de consommation
                fig3 = px.bar(
                    equip_data.groupby('Desc_Cat')['Montant'].sum().reset_index(),
                    x='Desc_Cat',
                    y='Montant',
                    title=f'Consommation par type pour {selected_equipment}',
                    height=400
                )
                fig3.update_layout(
                    xaxis_title="Type de consommation",
                    yaxis_title="Montant total (DH)",
                    template='plotly_white'
                )
                st.plotly_chart(fig3, use_container_width=True, key=f"equip_type_{selected_equipment}_{cat}")
                
                # Dans le temps
                fig4 = px.line(
                    equip_data.groupby('Date')['Montant'].sum().reset_index(),
                    x='Date',
                    y='Montant',
                    title=f'Évolution des coûts pour {selected_equipment}',
                    height=400
                )
                fig4.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Montant (DH)",
                    template='plotly_white'
                )
                st.plotly_chart(fig4, use_container_width=True, key=f"equip_time_{selected_equipment}_{cat}")

    # Analyse comparative tab
    with tabs[-3]:
        st.markdown("""
        <div style='background-color:#424242; padding:20px; border-radius:10px; border-left:5px solid #388e3c; margin-bottom:20px;'>
            <h2 style='color:#F28C38; margin-top:0;'>Analyse comparative</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Comparaison des catégories
        st.markdown("#### Comparaison des catégories")
        fig_comp = px.bar(
            filtered_data.groupby('CATEGORIE')['Montant'].sum().reset_index(),
            x='CATEGORIE',
            y='Montant',
            title='Coût total par catégorie',
            height=400,
            text='Montant'
        )

        fig_comp.update_layout(
            xaxis_title="Catégorie",
            yaxis_title="Montant total (DH)",
            template='plotly_white'
        )
        st.plotly_chart(fig_comp, use_container_width=True, key="category_comparison")
        


    # Recommandations tab
    with tabs[-2]:
        st.markdown("""
        <div style='background-color:#424242; padding:20px; border-radius:10px; border-left:5px solid #8e24aa; margin-bottom:20px;'>
            <h2 style='color:#F28C38; margin-top:0;'>Recommandations</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Top 3 des catégories les plus coûteuses
        top_categories = filtered_data.groupby('CATEGORIE')['Montant'].sum().nlargest(3).reset_index()
        
        st.markdown("#### Catégories prioritaires")
        cols = st.columns(3)
        colors = ['#d32f2f', '#ffa000', '#388e3c']
        for i, (col, (_, row)) in enumerate(zip(cols, top_categories.iterrows())):
            with col:
                st.markdown(f"""
                <div style='background-color:#424242; padding:15px; border-radius:10px; border-left:5px solid {colors[i]};'>
                    <h4 style='color:#F28C38; text-align:center;'>{row['CATEGORIE']}</h4>
                    <p style='color:#FFFFFF; text-align:center; font-size:24px; font-weight:bold;'>{row['Montant']:,.0f} DH</p>
                    <p style='color:#FFFFFF; text-align:center;'>{(row['Montant']/total_cost)*100:.1f}% du total</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background-color:#424242; padding:20px; border-radius:10px; margin-top:20px;'>
            <h3 style='color:#F28C38;'>Actions recommandées</h3>
            <ul style='color:#FFFFFF;'>
                <li>Prioriser les analyses des équipements dans les catégories les plus coûteuses</li>
                <li>Mettre en place un suivi mensuel des consommations par catégorie</li>
                <li>Comparer les performances des équipements similaires pour identifier les anomalies</li>
                <li>Négocier avec les fournisseurs pour les pièces les plus fréquemment remplacées</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Tableau des équipements tab
    with tabs[-1]:
        st.markdown("""
        <div style='background-color:#424242; padding:20px; border-radius:10px; border-left:5px solid #388e3c; margin-bottom:20px;'>
            <h2 style='color:#F28C38; margin-top:0;'>Tableau de la consommation des équipements</h2>
            <p style='color:#FFFFFF;'>Consommation détaillée par équipement pour la catégorie sélectionnée</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Filter for selecting multiple consumption types
        st.markdown("#### Filtrer par types de consommation")
        consumption_types = sorted(filtered_data['Desc_Cat'].unique())
        selected_consumptions = st.multiselect(
            "Sélectionner les types de consommation",
            consumption_types,
            default=None,
            key="consumption_types_multiselect",
            help="Sélectionnez un ou plusieurs types de consommation. Laissez vide pour afficher tous les types."
        )
        
        # Préparer les données du tableau sans la ligne de total
        table_df = filtered_data[['Date', 'Desc_CA', 'Desc_Cat', 'Montant']].copy()
        if selected_consumptions:
            table_df = table_df[table_df['Desc_Cat'].isin(selected_consumptions)]
        
        if table_df.empty:
            st.warning("Aucune donnée disponible pour les types de consommation sélectionnés.")
        else:
            table_df['Date'] = table_df['Date'].dt.strftime('%d/%m/%Y')
            table_df['Montant'] = table_df['Montant'].round(2)
            table_df = table_df.rename(columns={
                'Date': 'Date',
                'Desc_CA': 'Équipement',
                'Desc_Cat': 'Type de consommation',
                'Montant': 'Montant (DH)'
            })
            
            # Calculer le total pour la colonne 'Montant (DH)'
            total_montant = table_df['Montant (DH)'].sum()
            
            # Afficher le tableau avec un fond gris
            st.dataframe(
                table_df.style.format({
                    'Montant (DH)': '{:,.2f} DH',
                    'Date': lambda x: x if x else ''
                }).set_properties(**{
                    'background-color': '#424242',
                    'border': '1px solid #ddd',
                    'text-align': 'center',
                    'color': '#FFFFFF'
                }).set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#424242'), ('color', '#F28C38'), ('font-weight', 'bold')]}
                ]),
                height=600,
                use_container_width=True
            )
            
            # Afficher le total séparément sous le tableau
            st.markdown(f"""
            <div style='background-color:#424242; padding:10px; border-radius:10px; text-align:right; margin-top:10px;'>
                <p style='color:#FFFFFF; font-size:16px; font-weight:bold;'>Total : {total_montant:,.2f} DH</p>
            </div>
            """, unsafe_allow_html=True)

# Main Execution
def main():
    if not st.session_state.logged_in:
        auth_page()
    else:
        main_app()

if __name__ == '__main__':
    main()