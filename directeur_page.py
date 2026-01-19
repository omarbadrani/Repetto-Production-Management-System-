# pages/directeur_page.py - Page directeur avec analyse sur-consommation
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from database import DatabaseManager, Utils, KPIManager, DualChronoUtils
from typing import List, Dict


class DirecteurPage:
    """Page directeur avec tableau amélioré et modal de détails"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.utils = Utils()

        # Initialiser l'état pour le modal
        if 'show_modal' not in st.session_state:
            st.session_state.show_modal = False
        if 'selected_of_detail' not in st.session_state:
            st.session_state.selected_of_detail = None

    def render(self):
        """Affiche la page directeur"""
        st_autorefresh(interval=10000, limit=100, key="directeur_refresh")

        # Header
        col_header1, col_header2, col_header3 = st.columns([3, 1, 1])

        with col_header1:
            st.markdown('<div class="main-header">👠 Repetto Production</div>', unsafe_allow_html=True)
            st.markdown('<div class="sub-header">Tableau de Bord Directionnel • Suivi Production en Temps Réel</div>',
                        unsafe_allow_html=True)

        with col_header2:
            today = datetime.now().strftime("%d/%m/%Y")
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background: white; border-radius: 12px; border: 1px solid #E2E8F0;">
                <div style="font-size: 0.9rem; color: #6B7280; margin-bottom: 5px;">📅 Date</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: #1F2937;">{today}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_header3:
            current_time = datetime.now().strftime("%H:%M")
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background: white; border-radius: 12px; border: 1px solid #E2E8F0;">
                <div style="font-size: 0.9rem; color: #6B7280; margin-bottom: 5px;">⏰ Heure</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: #1F2937;">{current_time}</div>
            </div>
            """, unsafe_allow_html=True)

        self.db_manager.update_all_timers()
        orders = self.db_manager.get_all_orders()

        if not orders:
            st.info("🤷 Aucun OF créé")
            return

        # KPIs
        st.markdown('<div class="section-header">📈 Indicateurs Clés de Performance</div>', unsafe_allow_html=True)
        kpi_manager = KPIManager(orders)
        kpi_manager.display_kpi_cards()

        # Tableau détaillé avec modal
        self._render_improved_table(orders)

        # Modal de détails (si activé)
        if st.session_state.show_modal and st.session_state.selected_of_detail:
            self._render_detail_modal()

        # Visualisations
        self._render_visualizations(orders)

        # Nouvel onglet d'analyse de sur-consommation
        self._render_surconsommation_analysis()

        # Footer
        st.markdown("---")
        st.markdown("""
        <div class="footer">
            <div>👠 <b>Repetto Production Management System</b> • v1.0 • © 2025</div>
            <div style="font-size: 0.8rem; margin-top: 5px;">Dernière mise à jour: {} • Données actualisées en temps réel</div>
        </div>
        """.format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)

    def _render_surconsommation_analysis(self):
        """Affiche l'analyse de sur-consommation"""
        st.markdown('<div class="section-header">📦 Analyse de la Sur-consommation</div>', unsafe_allow_html=True)

        # Récupérer les données
        surcons_data = self.db_manager.get_surconsommation_data()

        if not surcons_data:
            st.info("✅ Aucune sur-consommation enregistrée pour le moment")
            return

        # KPIs principaux
        total_surcons = sum(float(item['sur_consommation']) for item in surcons_data)
        total_consommation = sum(float(item['consommation']) for item in surcons_data)
        taux_moyen_surcons = (total_surcons / total_consommation * 100) if total_consommation > 0 else 0
        nombre_of = len(surcons_data)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📊 OF avec surcons", nombre_of)
        with col2:
            st.metric("📦 Sur-consommation totale", f"{total_surcons:.2f} m²")
        with col3:
            st.metric("📈 Taux moyen", f"{taux_moyen_surcons:.1f}%")


        st.markdown("---")

        # Filtres
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            # Filtrer par matière
            matieres = ["Toutes"] + sorted(list(set([item['matiere'] for item in surcons_data if item['matiere']])))
            filtre_matiere = st.selectbox("Matière", matieres, key="surcons_matiere")

        with col_f2:
            # Filtrer par coupeur
            coupeurs_info = []
            for item in surcons_data:
                if item.get('matricule_coupeur'):
                    nom_complet = f"{item.get('matricule_coupeur', '')}"
                    if item.get('prenom_coupeur') or item.get('nom_coupeur'):
                        nom_complet += f" - {item.get('prenom_coupeur', '')} {item.get('nom_coupeur', '')}"
                    coupeurs_info.append(nom_complet)

            coupeurs = ["Tous"] + sorted(list(set(coupeurs_info)))
            filtre_coupeur = st.selectbox("Coupeur", coupeurs, key="surcons_coupeur")

        with col_f3:
            # Filtrer par modèle
            modeles = ["Tous"] + sorted(list(set([item['modele'] for item in surcons_data if item['modele']])))
            filtre_modele = st.selectbox("Modèle", modeles, key="surcons_modele")

        # Appliquer les filtres
        filtered_data = surcons_data
        if filtre_matiere != "Toutes":
            filtered_data = [item for item in filtered_data if item['matiere'] == filtre_matiere]
        if filtre_coupeur != "Tous":
            filtered_data = [item for item in filtered_data if
                             f"{item.get('matricule_coupeur', '')} - {item.get('prenom_coupeur', '')} {item.get('nom_coupeur', '')}".strip() == filtre_coupeur.strip()]
        if filtre_modele != "Tous":
            filtered_data = [item for item in filtered_data if item['modele'] == filtre_modele]

        # Tableau détaillé
        st.markdown("### 📋 Détails par OF")

        if filtered_data:
            # Créer un DataFrame pour affichage
            df = pd.DataFrame(filtered_data)

            # Formater les colonnes
            df['sur_consommation'] = df['sur_consommation'].apply(lambda x: f"{float(x):.2f} m²")
            df['consommation'] = df['consommation'].apply(lambda x: f"{float(x):.2f} m²")

            # Calculer le total et le taux
            df['total_consommation'] = df.apply(
                lambda
                    row: f"{float(row['consommation'].replace(' m²', '')) + float(row['sur_consommation'].replace(' m²', '')):.2f} m²",
                axis=1
            )

            df['taux_surcons'] = df.apply(
                lambda row: float(row['sur_consommation'].replace(' m²', '')) / float(
                    row['consommation'].replace(' m²', '')) * 100
                if float(row['consommation'].replace(' m²', '')) > 0 else 0,
                axis=1
            )

            # Sélectionner et renommer les colonnes
            display_df = df[[
                'of', 'modele', 'matiere', 'coloris', 'matricule_coupeur',
                'consommation', 'sur_consommation', 'total_consommation', 'taux_surcons'
            ]].copy()

            display_df.columns = [
                'OF', 'Modèle', 'Matière', 'Coloris', 'Coupeur',
                'Cons. Std (m²)', 'Sur-cons (m²)', 'Total (m²)', 'Taux (%)'
            ]

            # Afficher le tableau avec Streamlit
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "OF": st.column_config.TextColumn("OF", width="small"),
                    "Modèle": st.column_config.TextColumn("Modèle", width="medium"),
                    "Matière": st.column_config.TextColumn("Matière", width="small"),
                    "Taux (%)": st.column_config.ProgressColumn(
                        "Taux (%)",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100
                    )
                }
            )

            # Graphiques d'analyse
            st.markdown("### 📊 Visualisations")
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                # Sur-consommation par matière
                if len(filtered_data) > 0:
                    surcons_by_matiere = {}
                    for item in filtered_data:
                        matiere = item['matiere'] or 'Non spécifié'
                        surcons = float(item['sur_consommation'])
                        if matiere not in surcons_by_matiere:
                            surcons_by_matiere[matiere] = 0
                        surcons_by_matiere[matiere] += surcons

                    if surcons_by_matiere:
                        fig1 = go.Figure(data=[
                            go.Bar(
                                x=list(surcons_by_matiere.keys()),
                                y=list(surcons_by_matiere.values()),
                                marker_color='#F59E0B',
                                text=[f"{v:.1f}m²" for v in surcons_by_matiere.values()],
                                textposition='auto'
                            )
                        ])
                        fig1.update_layout(
                            title="Sur-consommation par Matière (m²)",
                            height=400,
                            xaxis_title="Matière",
                            yaxis_title="Sur-consommation (m²)"
                        )
                        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

            with col_chart2:
                # Taux de sur-consommation par coupeur
                if len(filtered_data) > 0:
                    taux_by_coupeur = {}
                    for item in filtered_data:
                        # Récupérer le matricule - FORCER LE TYPE TEXTE
                        coupeur = str(item.get('matricule_coupeur', 'Inconnu')).strip()
                        if coupeur and coupeur != 'Inconnu' and item.get('consommation'):
                            try:
                                surcons = float(item['sur_consommation'])
                                consommation = float(item['consommation'])
                                if consommation > 0:
                                    taux = (surcons / consommation * 100)
                                    if coupeur not in taux_by_coupeur:
                                        taux_by_coupeur[coupeur] = []
                                    taux_by_coupeur[coupeur].append(taux)
                            except (ValueError, TypeError):
                                continue

                    # Calculer la moyenne par coupeur
                    if taux_by_coupeur:
                        avg_taux_by_coupeur = {}
                        for coupeur, taux_list in taux_by_coupeur.items():
                            if taux_list:
                                avg_taux_by_coupeur[coupeur] = sum(taux_list) / len(taux_list)

                        if avg_taux_by_coupeur:
                            # Trier par taux décroissant
                            sorted_items = sorted(avg_taux_by_coupeur.items(), key=lambda x: x[1], reverse=True)
                            coupeurs = [str(item[0]) for item in sorted_items]  # S'assurer que c'est du texte
                            taux_values = [item[1] for item in sorted_items]

                            # Créer le graphique avec traitement spécial pour l'axe X
                            fig2 = go.Figure(data=[
                                go.Bar(
                                    x=coupeurs,
                                    y=taux_values,
                                    marker_color='#EF4444',
                                    text=[f"{v:.1f}%" for v in taux_values],
                                    textposition='auto',
                                    hovertemplate="<b>Matricule: %{x}</b><br>Taux: %{y:.1f}%<extra></extra>",
                                    textfont=dict(size=10)
                                )
                            ])

                            # CORRECTION CRITIQUE : Forcer l'axe X à être traité comme catégorie textuelle
                            fig2.update_layout(
                                title="Taux moyen de Sur-consommation par Coupeur",
                                height=400,
                                xaxis_title="Matricule Coupeur",
                                yaxis_title="Taux moyen (%)",
                                xaxis={
                                    'type': 'category',  # Forcer le type catégoriel
                                    'tickmode': 'array',
                                    'tickvals': coupeurs,  # Valeurs exactes
                                    'ticktext': coupeurs,  # Texte exact (mêmes valeurs)
                                    'tickangle': -45,
                                    'tickfont': dict(size=10),
                                    # Empêcher le formatage automatique des nombres
                                    'tickformat': '',
                                    'showticklabels': True,
                                },
                                yaxis={
                                    'tickformat': '.1f',
                                    'title': 'Taux (%)'
                                },
                                margin=dict(l=50, r=50, t=80, b=150)  # Ajuster les marges
                            )

                            # Ajouter cette option pour désactiver le formatage automatique
                            fig2.update_xaxes(automargin=True)

                            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

                            # DEBUG: Afficher les données brutes
                            # st.write("DEBUG - Matricules:", coupeurs)
                            # st.write("DEBUG - Taux:", taux_values)

                        else:
                            st.info("⚠️ Données insuffisantes pour calculer les taux par coupeur")
                            # Analyse détaillée
            st.markdown("### 🔍 Analyse détaillée")

            # Top 5 des plus grosses sur-consommations
            st.markdown("**🏆 Top 5 des plus grosses sur-consommations :**")
            top5 = sorted(filtered_data,
                          key=lambda x: float(x['sur_consommation']),
                          reverse=True)[:5]

            for idx, item in enumerate(top5, 1):
                surcons = float(item['sur_consommation'])
                consommation = float(item['consommation'])
                taux = (surcons / consommation * 100) if consommation > 0 else 0

                st.markdown(f"""
                <div style="background: {'#FEF3C7' if idx == 1 else '#F3F4F6'}; 
                            padding: 12px; 
                            border-radius: 8px; 
                            border-left: 4px solid {'#F59E0B' if idx == 1 else '#D1D5DB'};
                            margin: 8px 0;">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <strong>#{idx} OF {item['of']}</strong> • {item['modele']} • {item['matiere']}
                        </div>
                        <div style="font-weight: 700; color: {'#92400E' if taux > 20 else '#1F2937'};">
                            {surcons:.2f} m² ({taux:.1f}%)
                        </div>
                    </div>
                    <div style="font-size: 0.9rem; color: #6B7280;">
                        Coupeur: {item.get('matricule_coupeur', 'N/A')} • Coloris: {item['coloris']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Export des données
            st.markdown("---")
            col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 2])

            with col_exp1:
                # Bouton pour exporter en Excel
                if st.button("📊 Exporter Excel", use_container_width=True, type="primary", key="export_excel"):
                    try:
                        # Créer un DataFrame
                        export_df = pd.DataFrame(filtered_data)

                        # Formater les colonnes numériques
                        numeric_cols = ['consommation', 'sur_consommation', 'total_consommation', 'taux_surcons']
                        for col in numeric_cols:
                            if col in export_df.columns:
                                export_df[col] = pd.to_numeric(export_df[col], errors='coerce')

                        # Sélectionner et organiser les colonnes
                        columns_to_export = [
                            'of', 'modele', 'matiere', 'coloris', 'matricule_coupeur',
                            'consommation', 'sur_consommation', 'total_consommation', 'taux_surcons',
                            'date_debut_coupe', 'date_fin_coupe', 'statut_coupe',
                            'nom_coupeur', 'prenom_coupeur', 'observation_coupe'
                        ]

                        # Garder seulement les colonnes existantes
                        available_columns = [col for col in columns_to_export if col in export_df.columns]
                        export_df = export_df[available_columns]

                        # Renommer les colonnes pour un meilleur affichage
                        column_names_fr = {
                            'of': 'OF',
                            'modele': 'Modèle',
                            'matiere': 'Matière',
                            'coloris': 'Coloris',
                            'matricule_coupeur': 'Matricule Coupeur',
                            'consommation': 'Consommation Std (m²)',
                            'sur_consommation': 'Sur-consommation (m²)',
                            'total_consommation': 'Total Consommation (m²)',
                            'taux_surcons': 'Taux Sur-cons (%)',
                            'date_debut_coupe': 'Date Début Coupe',
                            'date_fin_coupe': 'Date Fin Coupe',
                            'statut_coupe': 'Statut Coupe',
                            'nom_coupeur': 'Nom Coupeur',
                            'prenom_coupeur': 'Prénom Coupeur',
                            'observation_coupe': 'Observation'
                        }

                        export_df = export_df.rename(columns=column_names_fr)

                        # Créer un fichier Excel en mémoire
                        from io import BytesIO
                        output = BytesIO()

                        # Créer un writer Excel avec openpyxl
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            # Feuille principale
                            export_df.to_excel(writer, sheet_name='Sur-consommation', index=False)

                            # Ajuster la largeur des colonnes
                            worksheet = writer.sheets['Sur-consommation']
                            for column in worksheet.columns:
                                max_length = 0
                                column_letter = column[0].column_letter
                                for cell in column:
                                    try:
                                        if len(str(cell.value)) > max_length:
                                            max_length = len(str(cell.value))
                                    except:
                                        pass
                                adjusted_width = min(max_length + 2, 50)
                                worksheet.column_dimensions[column_letter].width = adjusted_width

                            # Ajouter une feuille de synthèse
                            summary_data = {
                                'Métrique': ['Total OF', 'Sur-consommation totale (m²)', 'Taux moyen (%)',
                                             'Coût estimé (€)'],
                                'Valeur': [
                                    len(filtered_data),
                                    total_surcons,
                                    taux_moyen_surcons,
                                    total_surcons * 15
                                ]
                            }
                            summary_df = pd.DataFrame(summary_data)
                            summary_df.to_excel(writer, sheet_name='Synthèse', index=False)

                            # Ajouter une feuille par matière
                            if len(filtered_data) > 0:
                                matieres = list(set([item['matiere'] for item in filtered_data if item['matiere']]))
                                for matiere in matieres:
                                    matiere_data = [item for item in filtered_data if item['matiere'] == matiere]
                                    matiere_df = pd.DataFrame(matiere_data)
                                    if not matiere_df.empty:
                                        matiere_df = matiere_df[
                                            ['of', 'modele', 'consommation', 'sur_consommation', 'taux_surcons']]
                                        matiere_df = matiere_df.rename(columns={
                                            'of': 'OF',
                                            'modele': 'Modèle',
                                            'consommation': 'Consommation (m²)',
                                            'sur_consommation': 'Sur-cons (m²)',
                                            'taux_surcons': 'Taux (%)'
                                        })
                                        sheet_name = matiere[:31]  # Excel limite à 31 caractères
                                        matiere_df.to_excel(writer, sheet_name=sheet_name, index=False)

                        output.seek(0)

                        # Téléchargement
                        filename = f"surconsommation_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                        st.download_button(
                            label="💾 Télécharger Excel",
                            data=output,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="download_excel"
                        )

                        st.success(f"✅ Fichier Excel prêt: {filename}")

                    except Exception as e:
                        st.error(f"❌ Erreur création Excel: {e}")
                        import traceback
                        traceback.print_exc()

            with col_exp2:
                # Option pour exporter en PDF (optionnel)
                if st.button("📄 Exporter PDF", use_container_width=True, key="export_pdf"):
                    st.info("🚧 Fonction PDF en développement")

            with col_exp3:
                st.info("""
                **💡 Fonctionnalités Excel :**
                - **Feuille principale** : Données détaillées
                - **Synthèse** : KPIs et totaux
                - **Par matière** : Analyse par type de matériau
                - **Mise en forme** : Largeurs de colonnes ajustées
                """)
        else:
            st.warning("⚠️ Aucune donnée ne correspond aux filtres sélectionnés")

    def _render_improved_table(self, orders: List[Dict]):
        """Affiche le tableau amélioré avec double chronomètre"""
        st.markdown('<div class="section-header">📊 Tableau de Suivi Production</div>', unsafe_allow_html=True)

        # Filtres compacts en ligne
        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([2, 2, 2, 2, 1])

        with col_f1:
            filter_status = st.selectbox("👌 Statut", ["Tous", "En cours", "Terminé", "En pause"],
                                         key="table_status_filter")

        with col_f2:
            models = ["Tous"] + sorted(list(set([o['modele'] for o in orders])))
            filter_model = st.selectbox("👟 Modèle", models, key="table_model_filter")

        with col_f3:
            filter_qualite = st.selectbox("✅ Qualité", ["Tous", "Avec problèmes", "Sans problèmes"],
                                          key="table_quality_filter")

        with col_f4:
            filter_pause = st.selectbox("⏸️ Pause", ["Tous", "En pause", "Actif"], key="table_pause_filter")

        with col_f5:
            if st.button("🔄", help="Actualiser", use_container_width=True):
                st.rerun()

        # Appliquer les filtres
        filtered_orders = []
        for order in orders:
            if self._apply_filters(order, filter_status, filter_model, filter_qualite, filter_pause):
                filtered_orders.append(order)

        # Construction des données du tableau
        # Construction des données du tableau
        table_data = []
        for order in filtered_orders:
            # ===== CALCULS POUR LA COUPE =====
            temps_coupe = order.get('temps_coupe', 0) or 0
            pause_coupe_duration = self.utils.calculate_pause_duration(order, 'coupe')
            total_coupe_avec_pause = temps_coupe + pause_coupe_duration

            # ===== CALCULS POUR LE CONTRÔLE =====
            pause_controle_duration = order.get('temps_pause_total', 0) or 0
            if pause_controle_duration == 0:
                pause_controle_duration = self.utils.calculate_pause_duration(order, 'controle')
            temps_controle_valeur = order.get('temps_actif_total', 0) or 0
            if temps_controle_valeur == 0:
                temps_controle_valeur = order.get('temps_controle', 0) or 0

            # Pourcentage de contrôle
            quantite_controlee = order.get('quantite_controlee', 0) or 0
            quantite_totale = order['quantite']
            pourcentage = (quantite_controlee / quantite_totale * 100) if quantite_totale > 0 else 0

            # ===== NOUVELLES DONNÉES PIQÛRE =====
            temps_piqure = order.get('temps_piqure', 0) or 0
            pause_piqure_duration = self.utils.calculate_pause_duration(order, 'piqure')
            statut_piqure = order.get('statut_piqure', 'En attente')

            table_data.append({
                'OF': order['of'],
                'Modèle': order['modele'],
                'Couleur': order['couleur_modele'],
                'Quantité': quantite_totale,
                'Statut Coupe': order['statut_coupe'],
                'Temps Coupe': self.utils.format_time(temps_coupe),
                'Statut Contrôle': order['statut_controle'],
                'Temps Contrôle': self.utils.format_time(temps_controle_valeur),
                'Pourcentage': pourcentage,

                # Nouvelles données piqûre
                'Statut Piqûre': statut_piqure,
                'Temps Piqûre': self.utils.format_time(temps_piqure),
                'Pause Piqûre': pause_piqure_duration,

                '_order_data': order
            })

        if not table_data:
            st.info("Aucun OF ne correspond aux filtres sélectionnés.")
            return

        # Affichage du tableau HTML
        self._render_html_table(table_data)

        # Sélecteur d'OF pour voir les détails
        st.markdown("---")
        st.markdown("### 🔍 Détails d'un OF")

        col_select1, col_select2 = st.columns([4, 1])

        with col_select1:
            of_list = [row['OF'] for row in table_data]
            selected_of = st.selectbox(
                "Sélectionner un OF pour voir tous les détails",
                ["Choisir un OF..."] + of_list,
                key="modal_of_selector",
                help="Sélectionnez un OF dans la liste pour afficher ses informations complètes"
            )

        with col_select2:
            st.write("")
            st.write("")
            if selected_of and selected_of != "Choisir un OF...":
                if st.button("📊 Afficher", use_container_width=True, type="primary"):
                    st.session_state.selected_of_detail = selected_of
                    st.session_state.show_modal = True

    def _render_html_table(self, table_data: List[Dict]):
        """Génère et affiche le tableau HTML avec couleurs - AVEC PIQÛRE ET PAUSES"""
        table_html = """
        <div class="dataframe-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>OF</th>
                        <th>Modèle</th>
                        <th>Couleur</th>
                        <th>Quantité</th>
                        <th>Statut Coupe</th>
                        <th>⏱️ Coupe</th>
                        <th>⏸️ Pause Coupe</th>  <!-- NOUVEAU -->
                        <th>Statut Ctrl</th>
                        <th>⏱️ Ctrl</th>
                        <th>⏸️ Pause Ctrl</th>   <!-- NOUVEAU -->
                        <th>% Ctrl</th>
                        <th>Statut Piqûre</th>
                        <th>⏱️ Piqûre</th>
                        <th>⏸️ Pause Piqûre</th>
                    </tr>
                </thead>
                <tbody>
        """

        for idx, row in enumerate(table_data):
            row_class = "table-row-even" if idx % 2 == 0 else "table-row-odd"
            table_html += f'<tr class="{row_class}">'

            # OF
            table_html += f'<td class="of-cell"><strong>{row["OF"]}</strong></td>'
            table_html += f'<td>{row["Modèle"]}</td>'
            table_html += f'<td>{row["Couleur"]}</td>'
            table_html += f'<td><strong>{row["Quantité"]}</strong></td>'

            # Statut Coupe
            status_coupe_class = self._get_status_class(row['Statut Coupe'])
            status_coupe_icon = self._get_status_icon(row['Statut Coupe'])
            table_html += f'<td><span class="status-cell {status_coupe_class}">{status_coupe_icon} {row["Statut Coupe"]}</span></td>'

            # Temps Coupe
            table_html += f'<td><span class="time-cell">⏱️ {row["Temps Coupe"]}</span></td>'

            # ===== PAUSE COUPE =====
            order_data = row.get('_order_data', {})
            pause_coupe_value = self.utils.calculate_pause_duration(order_data, 'coupe')
            if pause_coupe_value > 0:
                pause_coupe_display = self.utils.format_time(pause_coupe_value)
                if order_data.get('coupe_en_pause'):
                    table_html += f'<td><span class="pause-cell-active" title="EN PAUSE ACTUELLEMENT">⏸️ {pause_coupe_display}</span></td>'
                else:
                    table_html += f'<td><span class="pause-cell" title="Pause historique">⏸️ {pause_coupe_display}</span></td>'
            else:
                table_html += f'<td><span class="pause-cell-zero">-</span></td>'

            # Statut Contrôle
            status_ctrl_class = self._get_status_class(row['Statut Contrôle'])
            status_ctrl_icon = self._get_status_icon(row['Statut Contrôle'])
            table_html += f'<td><span class="status-cell {status_ctrl_class}">{status_ctrl_icon} {row["Statut Contrôle"]}</span></td>'

            # Temps Contrôle
            table_html += f'<td><span class="time-cell">⏱️ {row["Temps Contrôle"]}</span></td>'

            # ===== PAUSE CONTRÔLE =====
            pause_controle_value = order_data.get('temps_pause_total', 0) or 0
            if pause_controle_value == 0:
                pause_controle_value = self.utils.calculate_pause_duration(order_data, 'controle')

            if pause_controle_value > 0:
                pause_controle_display = self.utils.format_time(pause_controle_value)
                if order_data.get('controle_en_pause'):
                    table_html += f'<td><span class="pause-cell-active" title="EN PAUSE ACTUELLEMENT">⏸️ {pause_controle_display}</span></td>'
                else:
                    table_html += f'<td><span class="pause-cell" title="Pause historique">⏸️ {pause_controle_display}</span></td>'
            else:
                table_html += f'<td><span class="pause-cell-zero">-</span></td>'

            # % Contrôle
            progress_class = self._get_progress_class(row["Pourcentage"])
            table_html += f'<td><span class="progress-cell {progress_class}">{row["Pourcentage"]:.1f}%</span></td>'

            # ===== COLONNES PIQÛRE =====
            # Statut Piqûre
            statut_piqure = row.get('Statut Piqûre', 'En attente')
            status_piqure_class = self._get_status_class(statut_piqure)
            status_piqure_icon = self._get_status_icon(statut_piqure)
            table_html += f'<td><span class="status-cell {status_piqure_class}">{status_piqure_icon} {statut_piqure}</span></td>'

            # Temps Piqûre
            temps_piqure = row.get('Temps Piqûre', '00:00:00')
            table_html += f'<td><span class="time-cell">🪡 {temps_piqure}</span></td>'

            # Pause Piqûre
            pause_piqure_value = row.get('Pause Piqûre', 0)
            if pause_piqure_value > 0:
                pause_piqure_display = self.utils.format_time(pause_piqure_value)
                if order_data.get('piqure_en_pause'):
                    table_html += f'<td><span class="pause-cell-active" title="EN PAUSE ACTUELLEMENT">⏸️ {pause_piqure_display}</span></td>'
                else:
                    table_html += f'<td><span class="pause-cell" title="Pause historique">⏸️ {pause_piqure_display}</span></td>'
            else:
                table_html += f'<td><span class="pause-cell-zero">-</span></td>'

            table_html += '</tr>'

        table_html += """
                </tbody>
            </table>
        </div>
        """

        st.markdown(table_html, unsafe_allow_html=True)

    def _get_status_class(self, status: str) -> str:
        """Retourne la classe CSS pour le statut"""
        status_map = {
            'En attente': 'status-attente',
            'En cours': 'status-en-cours',
            'Terminée': 'status-terminee',
            'En pause': 'status-pause',
            'Approuvé ✅': 'status-approuve',
            'Rejeté ❌': 'status-rejete',
            'À retravailler 🔧': 'status-retravailler',
            'Contrôle partiel': 'status-partiel'
        }
        return status_map.get(status, 'status-attente')

    def _get_status_icon(self, status: str) -> str:
        """Retourne l'icône pour le statut"""
        icon_map = {
            'En attente': '⏳',
            'En cours': '🔄',
            'Terminée': '✅',
            'En pause': '⏸️',
            'Approuvé ✅': '✅',
            'Rejeté ❌': '❌',
            'À retravailler 🔧': '🔧',
            'Contrôle partiel': '🔄'
        }
        return icon_map.get(status, '❓')

    def _get_progress_class(self, percentage: float) -> str:
        """Retourne la classe CSS selon le pourcentage"""
        if percentage >= 100:
            return 'progress-complete'
        elif percentage >= 75:
            return 'progress-high'
        elif percentage >= 40:
            return 'progress-medium'
        else:
            return 'progress-low'

    def _apply_filters(self, order, filter_status, filter_model, filter_qualite, filter_pause):
        """Applique les filtres à un ordre"""
        if filter_status != "Tous":
            if filter_status == "En cours" and order['statut_coupe'] != 'En cours':
                return False
            if filter_status == "Terminé" and order['statut_coupe'] != 'Terminée':
                return False
            if filter_status == "En pause" and not (order.get('coupe_en_pause') or order.get('controle_en_pause')):
                return False

        if filter_model != "Tous" and order['modele'] != filter_model:
            return False

        if filter_qualite != "Tous":
            problems = (order.get('quantite_rejetee', 0) or 0) + (order.get('quantite_retravailler', 0) or 0)
            if filter_qualite == "Avec problèmes" and problems == 0:
                return False
            if filter_qualite == "Sans problèmes" and problems > 0:
                return False

        if filter_pause != "Tous":
            has_pause = order.get('coupe_en_pause') or order.get('controle_en_pause')
            if filter_pause == "En pause" and not has_pause:
                return False
            if filter_pause == "Actif" and has_pause:
                return False

        return True

    def _render_detail_modal(self):
        """Affiche le modal avec les détails complets de l'OF"""
        of_number = st.session_state.selected_of_detail
        order = self.db_manager.get_order_by_of(of_number)

        if not order:
            st.session_state.show_modal = False
            st.rerun()
            return

        st.markdown('<div class="modal-backdrop"></div>', unsafe_allow_html=True)

        with st.container():
            col_title, col_close = st.columns([5, 1])

            with col_title:
                st.markdown(f"""
                <div class="modal-title">
                    📊 Détails Complets - OF: <span style="color: #E75480;">{of_number}</span>
                </div>
                """, unsafe_allow_html=True)

            with col_close:
                if st.button("❌ Fermer", use_container_width=True, key="close_modal_btn"):
                    st.session_state.show_modal = False
                    st.session_state.selected_of_detail = None
                    st.rerun()

            st.markdown("---")

            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["📋 Général", "✂️ Coupe", "👌 Contrôle", "🪡 Piqûre", "📊 Statistiques"])

            with tab1:
                col_info1, col_info2 = st.columns(2)

                with col_info1:
                    st.markdown("#### 📋 Informations de Base")
                    st.markdown(f"""
                    <div class="detail-box">
                        <div class="detail-item"><strong>OF:</strong> {order['of']}</div>
                        <div class="detail-item"><strong>Modèle:</strong> {order['modele']}</div>
                        <div class="detail-item"><strong>Couleur Modèle:</strong> {order['couleur_modele']}</div>
                        <div class="detail-item"><strong>Coloris:</strong> {order['coloris']}</div>
                        <div class="detail-item"><strong>Matière:</strong> {order['matiere']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_info2:
                    st.markdown("#### 📊 Quantités & Production")
                    st.markdown(f"""
                    <div class="detail-box">
                        <div class="detail-item"><strong>Quantité Totale:</strong> {order['quantite']} paires</div>
                        <div class="detail-item"><strong>Matricule Coupeur:</strong> {order['matricule_coupeur']}</div>
                        <div class="detail-item"><strong>Consommation:</strong> {order['consommation']} m²</div>
                        <div class="detail-item"><strong>Sur-consommation:</strong> {order['sur_consommation']} m²</div>
                        <div class="detail-item"><strong>Date Création:</strong> {order['date_creation'].strftime('%d/%m/%Y %H:%M') if order['date_creation'] else '-'}</div>
                    </div>
                    """, unsafe_allow_html=True)

                if order.get('observation'):
                    st.markdown("#### 📝 Observations Générales")
                    st.info(order['observation'])

            with tab2:
                st.markdown("#### ✂️ Détails de la Coupe")

                col_coupe1, col_coupe2, col_coupe3 = st.columns(3)

                with col_coupe1:
                    st.metric("Statut", order['statut_coupe'])

                with col_coupe2:
                    st.metric("Temps Total", self.utils.format_time(order.get('temps_coupe', 0)))

                with col_coupe3:
                    temps_pause = self.utils.calculate_pause_duration(order, 'coupe')
                    st.metric("Temps Pause", self.utils.format_time(temps_pause))

                st.markdown("---")

                col_date1, col_date2 = st.columns(2)

                with col_date1:
                    if order.get('date_debut_coupe'):
                        st.success(f"🚀 Début: {order['date_debut_coupe'].strftime('%d/%m/%Y %H:%M')}")
                    else:
                        st.info("Pas encore démarré")

                with col_date2:
                    if order.get('date_fin_coupe'):
                        st.success(f"🏁 Fin: {order['date_fin_coupe'].strftime('%d/%m/%Y %H:%M')}")
                    else:
                        st.info("Non terminé")

            with tab3:
                st.markdown("#### 👌 Détails du Contrôle Qualité")

                quality_details = self.utils.get_quality_details(order)

                col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns(4)

                with col_ctrl1:
                    st.metric("Contrôlées", f"{quality_details['controlee']}/{order['quantite']}")

                with col_ctrl2:
                    st.metric("✅ Acceptées", quality_details['acceptee'],
                              delta=f"{quality_details['acceptee_pourcentage']:.1f}%")

                with col_ctrl3:
                    st.metric("❌ Rejetées", quality_details['rejetee'],
                              delta=f"{quality_details['rejetee_pourcentage']:.1f}%", delta_color="inverse")

                with col_ctrl4:
                    st.metric("🔧 À retravailler", quality_details['retravailler'],
                              delta=f"{quality_details['retravailler_pourcentage']:.1f}%", delta_color="inverse")

                st.markdown("---")

                col_time1, col_time2 = st.columns(2)

                with col_time1:
                    st.metric("Temps Contrôle", self.utils.format_time(order.get('temps_controle', 0)))

                with col_time2:
                    temps_pause_ctrl = self.utils.calculate_pause_duration(order, 'controle')
                    st.metric("Pause Contrôle", self.utils.format_time(temps_pause_ctrl))

                if order.get('observation_controle'):
                    st.markdown("#### 📝 Observations Contrôle")
                    st.warning(order['observation_controle'])

            with tab4:
                st.markdown("#### 🪡 Détails de la Piqûre")

                if order.get('statut_piqure'):
                    col_piqure1, col_piqure2, col_piqure3 = st.columns(3)

                    with col_piqure1:
                        st.metric("Statut", order.get('statut_piqure', 'Non démarré'))

                    with col_piqure2:
                        st.metric("Temps Total", self.utils.format_time(order.get('temps_piqure', 0)))

                    with col_piqure3:
                        temps_pause = self.utils.calculate_pause_duration(order, 'piqure')
                        st.metric("Temps Pause", self.utils.format_time(temps_pause))

                    st.markdown("---")

                    col_date1, col_date2 = st.columns(2)

                    with col_date1:
                        if order.get('date_debut_piqure'):
                            st.success(f"🚀 Début: {order['date_debut_piqure'].strftime('%d/%m/%Y %H:%M')}")
                        else:
                            st.info("Pas encore démarré")

                    with col_date2:
                        if order.get('date_fin_piqure'):
                            st.success(f"🏁 Fin: {order['date_fin_piqure'].strftime('%d/%m/%Y %H:%M')}")
                        else:
                            st.info("Non terminé")

                    if order.get('matricule_piqueur'):
                        st.markdown("---")
                        st.info(f"👤 Piqueur: {order['matricule_piqueur']}")

                    if order.get('observation_piqure'):
                        st.markdown("#### 📝 Observations Piqûre")
                        st.info(order['observation_piqure'])
                else:
                    st.info("⏳ Opération de piqûre non encore initiée")

    def _render_visualizations(self, orders: List[Dict]):
        """Affiche les visualisations avec configuration corrigée"""
        st.markdown('<div class="section-header">📊 Tableaux de Bord Visuels</div>', unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["📈 Aperçu Production", "👌 Analyse Qualité", "⏱️ Performance Temps"])

        plotly_config = {'displayModeBar': False, 'displaylogo': False}

        with tab1:
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                status_counts = {
                    'En attente': len([o for o in orders if o['statut_coupe'] == 'En attente']),
                    'En cours': len(
                        [o for o in orders if o['statut_coupe'] == 'En cours' and not o.get('coupe_en_pause')]),
                    'En pause': len([o for o in orders if o.get('coupe_en_pause')]),
                    'Terminée': len([o for o in orders if o['statut_coupe'] == 'Terminée'])
                }

                fig_pie = go.Figure(data=[go.Pie(
                    labels=list(status_counts.keys()),
                    values=list(status_counts.values()),
                    hole=.4,
                    marker_colors=['#FBBF24', '#3B82F6', '#EF4444', '#10B981']
                )])

                fig_pie.update_layout(
                    title="Distribution des Statuts de Coupe",
                    height=400,
                    showlegend=True
                )
                st.plotly_chart(fig_pie, use_container_width=True, config=plotly_config)

            with col_chart2:
                of_list = [o['of'] for o in orders[:8]]
                quantite_list = [o['quantite'] for o in orders[:8]]
                controle_list = [o.get('quantite_controlee', 0) or 0 for o in orders[:8]]

                fig_bar = go.Figure(data=[
                    go.Bar(name='Total', x=of_list, y=quantite_list, marker_color='#3B82F6'),
                    go.Bar(name='Contrôlées', x=of_list, y=controle_list, marker_color='#10B981')
                ])

                fig_bar.update_layout(
                    title="Progression Contrôle - Top 8 OF",
                    barmode='group',
                    height=400,
                    xaxis_tickangle=-45,
                    xaxis={
                        'type': 'category',  # Forcer le traitement comme catégorie
                        'tickmode': 'array'
                    }
                )
                st.plotly_chart(fig_bar, use_container_width=True, config=plotly_config)

        with tab2:
            col_qual1, col_qual2 = st.columns(2)

            with col_qual1:
                quality_data = []
                for order in orders[:10]:
                    quantite_controlee = order.get('quantite_controlee', 0) or 0
                    if quantite_controlee > 0:
                        quantite_rejetee = order.get('quantite_rejetee', 0) or 0
                        taux_rejet = (quantite_rejetee / quantite_controlee * 100)
                        quality_data.append({
                            'OF': order['of'],
                            'Taux Rejet': taux_rejet,
                            'Quantité': quantite_controlee
                        })

                if quality_data:
                    df_quality = pd.DataFrame(quality_data)
                    fig_quality = px.bar(
                        df_quality,
                        x='OF',
                        y='Taux Rejet',
                        title="Taux de Rejet par OF",
                        color='Taux Rejet',
                        color_continuous_scale=['#10B981', '#F59E0B', '#EF4444']
                    )
                    fig_quality.update_layout(height=400, xaxis_tickangle=-45)
                    st.plotly_chart(fig_quality, use_container_width=True, config=plotly_config)

            with col_qual2:
                model_data = {}
                for order in orders:
                    model = order['modele']
                    if model not in model_data:
                        model_data[model] = {'total': 0, 'problems': 0}

                    quantite_controlee = order.get('quantite_controlee', 0) or 0
                    quantite_rejetee = order.get('quantite_rejetee', 0) or 0
                    quantite_retravailler = order.get('quantite_retravailler', 0) or 0

                    model_data[model]['total'] += quantite_controlee
                    model_data[model]['problems'] += quantite_rejetee + quantite_retravailler

                if model_data:
                    models = list(model_data.keys())[:8]
                    problem_rates = []
                    for model in models:
                        if model_data[model]['total'] > 0:
                            rate = (model_data[model]['problems'] / model_data[model]['total'] * 100)
                        else:
                            rate = 0
                        problem_rates.append(rate)

                    fig_model = go.Figure(data=[
                        go.Bar(x=models, y=problem_rates, marker_color='#F59E0B')
                    ])
                    fig_model.update_layout(
                        title="Taux Problèmes par Modèle",
                        yaxis_title="% de Problèmes",
                        height=400,
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig_model, use_container_width=True, config=plotly_config)

        with tab3:
            col_time1, col_time2 = st.columns(2)

            with col_time1:
                times_data = []
                for order in orders[:10]:
                    if order.get('temps_coupe', 0) > 0:
                        # Récupérer le matricule et forcer en texte
                        matricule = str(order.get('matricule_coupeur', 'N/A')).strip()
                        times_data.append({
                            'Matricule': matricule,  # Utiliser le matricule comme axe X
                            'Temps Coupe (h)': order.get('temps_coupe', 0) / 3600,
                            'Temps Contrôle (h)': order.get('temps_controle', 0) / 3600,
                            'OF': order['of']  # Garder pour info
                        })

                if times_data:
                    df_times = pd.DataFrame(times_data)

                    # Option 1: Graphique avec matricules
                    fig_time = go.Figure(data=[
                        go.Bar(
                            name='Coupe',
                            x=df_times['Matricule'],
                            y=df_times['Temps Coupe (h)'],
                            marker_color='#3B82F6',
                            text=df_times['OF'],  # Afficher l'OF en hover
                            hovertemplate="<b>Matricule: %{x}</b><br>OF: %{text}<br>Temps: %{y:.1f}h<extra></extra>"
                        ),
                        go.Bar(
                            name='Contrôle',
                            x=df_times['Matricule'],
                            y=df_times['Temps Contrôle (h)'],
                            marker_color='#10B981',
                            text=df_times['OF'],
                            hovertemplate="<b>Matricule: %{x}</b><br>OF: %{text}<br>Temps: %{y:.1f}h<extra></extra>"
                        )
                    ])

                    fig_time.update_layout(
                        title="Temps par Coupeur (heures)",
                        barmode='group',
                        height=400,
                        xaxis_tickangle=-45,
                        xaxis={
                            'type': 'category',  # Forcer catégorie
                            'title': 'Matricule Coupeur',
                            'tickmode': 'array'
                        },
                        yaxis={'title': 'Heures'}
                    )
                    st.plotly_chart(fig_time, use_container_width=True, config=plotly_config)

            with col_time2:
                # Graphique des temps par OF (plus simple)
                of_list = [o['of'] for o in orders[:10] if o.get('temps_coupe', 0) > 0]
                coupe_times = [o.get('temps_coupe', 0) / 3600 for o in orders[:10] if o.get('temps_coupe', 0) > 0]
                controle_times = [o.get('temps_controle', 0) / 3600 for o in orders[:10] if
                                  o.get('temps_controle', 0) > 0]

                if coupe_times:
                    fig_dist = go.Figure()

                    if of_list and coupe_times:
                        fig_dist.add_trace(go.Bar(
                            x=of_list,
                            y=coupe_times,
                            name='Temps Coupe (h)',
                            marker_color='#3B82F6',
                            text=[f"{t:.1f}h" for t in coupe_times],
                            textposition='auto'
                        ))

                    if of_list and controle_times:
                        fig_dist.add_trace(go.Bar(
                            x=of_list,
                            y=controle_times,
                            name='Temps Contrôle (h)',
                            marker_color='#10B981',
                            text=[f"{t:.1f}h" for t in controle_times],
                            textposition='auto'
                        ))

                    fig_dist.update_layout(
                        title="Temps par OF (heures)",
                        height=400,
                        xaxis_title="OF",
                        yaxis_title="Heures",
                        xaxis={'type': 'category', 'tickangle': -45},
                        barmode='group'
                    )
                    st.plotly_chart(fig_dist, use_container_width=True, config=plotly_config)

