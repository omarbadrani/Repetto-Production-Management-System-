# pages/chef_coupe_page.py - Page chef de coupe avec auto-complétion code modèle
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time
from datetime import datetime, timedelta
from database import DatabaseManager, Utils
from typing import List, Dict, Optional


class ChefCoupePage:
    """Page chef de coupe"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.utils = Utils()

    def render(self):
        """Affiche la page chef de coupe"""
        st_autorefresh(interval=5000, limit=1000, key="chef_coupe_refresh")

        # Forcer le refresh des données
        st.cache_data.clear()
        st.markdown('<div class="main-header">👨‍🔧 Interface Chef de Coupe</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Gestion des Ordres de Fabrication • Suivi en temps réel</div>',
                    unsafe_allow_html=True)

        self.db_manager.update_all_timers()

        if 'last_activity' in st.session_state:
            if datetime.now() - st.session_state.last_activity > timedelta(minutes=30):
                st.warning("⚠️ Session expirée")
                st.session_state.logged_in = False
                st.rerun()
            else:
                st.session_state.last_activity = datetime.now()

        # Vérifier les retours qualité
        orders = self.db_manager.get_all_orders()
        retour_coupe = [o for o in orders if o['statut_controle'] == 'À retravailler 🔧']

        # Afficher une alerte s'il y a des retours
        if retour_coupe:
            total_retour = len(retour_coupe)
            total_paires_retour = sum(self.utils.get_quality_details(o)['retravailler'] for o in retour_coupe)

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); 
                        padding: 15px; 
                        border-radius: 12px; 
                        border-left: 6px solid #F59E0B;
                        margin-bottom: 20px;
                        border: 1px solid #FDE68A;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                    <span style="font-size: 1.5rem;">🔧</span>
                    <div>
                        <div style="font-weight: 700; color: #92400E; font-size: 1.1rem;">
                            ALERTE: {total_retour} OF en RETOUR QUALITÉ
                        </div>
                        <div style="color: #92400E; font-size: 0.9rem;">
                            Total à retravailler: {total_paires_retour} paires
                        </div>
                    </div>
                </div>
                <div style="font-size: 0.85rem; color: #92400E;">
                    Ces OF nécessitent une reproduction suite aux problèmes qualité détectés.
                    Consultez la section "Gestion des OF en cours" pour les redémarrer.
                </div>
            </div>
            """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📊 Créer OF", "⏱️ Gestion en cours"])

        with tab1:
            self._render_create_of()

        with tab2:
            self._render_manage_of()

    # ===== MODIFICATION 1: Dans chef_coupe_page.py - _render_create_of() =====

    def _render_create_of(self):
        """Affiche le formulaire de création d'OF avec auto-complétions"""
        st.markdown('<div class="section-header">Création d\'Ordre de Fabrication</div>', unsafe_allow_html=True)

        # Récupérer la liste des employés, modèles et couleurs
        employees = self.db_manager.get_all_employees()
        modeles = self.db_manager.get_all_modeles()
        couleurs = self.db_manager.get_all_coloris()  # NOUVEAU

        # Initialiser les variables de session pour le formulaire
        if 'selected_code_modele' not in st.session_state:
            st.session_state.selected_code_modele = ""
        if 'auto_nom_modele' not in st.session_state:
            st.session_state.auto_nom_modele = ""
        if 'auto_matiere' not in st.session_state:
            st.session_state.auto_matiere = ""
        if 'auto_consignes' not in st.session_state:
            st.session_state.auto_consignes = ""
        if 'auto_emport_piece' not in st.session_state:
            st.session_state.auto_emport_piece = ""
        if 'selected_code_couleur' not in st.session_state:  # NOUVEAU
            st.session_state.selected_code_couleur = ""
        if 'auto_nom_couleur' not in st.session_state:  # NOUVEAU
            st.session_state.auto_nom_couleur = ""

        with st.form("form_coupe", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                of = st.text_input("OF *", placeholder="OF-2025-001", help="Numéro unique d'ordre de fabrication")

                # ===== SÉLECTEUR DE CODE MODÈLE =====
                if modeles:
                    code_options = sorted(list(set([m['code_modele'] for m in modeles if m['code_modele']])))

                    selected_code = st.selectbox(
                        "Code Modèle *",
                        options=[""] + code_options,
                        format_func=lambda x: "Sélectionner un code modèle..." if x == "" else x,
                        help="Sélectionnez le code du modèle - Les autres champs se rempliront automatiquement",
                        key="code_modele_select"
                    )

                    if selected_code and selected_code != st.session_state.selected_code_modele:
                        st.session_state.selected_code_modele = selected_code
                        modele_info = self.db_manager.get_modele_by_code(selected_code)
                        if modele_info:
                            st.session_state.auto_nom_modele = modele_info.get('nom_modele', '')
                            st.session_state.auto_matiere = modele_info.get('matiere', '')
                            st.session_state.auto_consignes = modele_info.get('consignes_de_coupe', '')
                            st.session_state.auto_emport_piece = modele_info.get('emport_de_piece', '')
                    elif not selected_code:
                        st.session_state.selected_code_modele = ""
                        st.session_state.auto_nom_modele = ""
                        st.session_state.auto_matiere = ""
                        st.session_state.auto_consignes = ""
                        st.session_state.auto_emport_piece = ""

                    code_modele = selected_code
                else:
                    st.warning("Aucun modèle trouvé dans la base de données")
                    code_modele = ""

                # Champ Nom Modèle (auto-rempli)
                modele = st.text_input(
                    "Nom Modèle *",
                    value=st.session_state.auto_nom_modele,
                    placeholder="Sera rempli automatiquement",
                    help="Ce champ se remplit automatiquement selon le code modèle",
                    disabled=True


                )

                # ===== NOUVEAU: SÉLECTEUR CODE COULEUR AVEC AUTO-COMPLÉTION =====
                if couleurs:
                    couleur_options = sorted(list(set([c['code_couleur'] for c in couleurs if c['code_couleur']])))

                    selected_couleur_code = st.selectbox(
                        "Code Couleur *",
                        options=[""] + couleur_options,
                        format_func=lambda x: "Sélectionner une couleur..." if x == "" else x,
                        help="Sélectionnez le code couleur - Le nom se remplira automatiquement",
                        key="code_couleur_select"
                    )

                    # Auto-complétion du nom couleur (SANS on_change)
                    if selected_couleur_code and selected_couleur_code != st.session_state.selected_code_couleur:
                        st.session_state.selected_code_couleur = selected_couleur_code
                        couleur_info = self.db_manager.get_couleur_by_code(selected_couleur_code)
                        if couleur_info:
                            st.session_state.auto_nom_couleur = couleur_info.get('nom_couleur', '')
                    elif not selected_couleur_code:
                        st.session_state.selected_code_couleur = ""
                        st.session_state.auto_nom_couleur = ""

                    couleur_modele = selected_couleur_code
                else:
                    st.warning("Aucune couleur trouvée dans la base de données")
                    couleur_modele = ""

                # Afficher directement le nom de la couleur en dessous du selectbox
                if st.session_state.auto_nom_couleur:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%); 
                                padding: 10px; 
                                border-radius: 8px; 
                                border-left: 4px solid #3B82F6;
                                margin: 10px 0;">
                        <div style="font-weight: 600; color: #0C3B82;">
                            ✅ Coloris: <strong>{st.session_state.auto_nom_couleur}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                quantite = st.number_input("Quantité *", min_value=1, step=1, value=100,
                                           help="Nombre total de paires à produire")

                # Champ Coloris caché (pour le formulaire)
                coloris = st.session_state.auto_nom_couleur

            with col2:
                # Champ Matière (auto-rempli)
                matiere = st.text_input(
                    "Matière *",
                    value=st.session_state.auto_matiere,
                    placeholder="Sera rempli automatiquement",
                    help="Ce champ se remplit automatiquement selon le code modèle",
                    disabled=True
                )

                # Sélecteur Matricule Coupeur
                if employees:
                    employee_options = [f"{emp['matricule']} - {emp['nom']} {emp['prenom']}" for emp in employees]
                    selected_employee = st.selectbox(
                        "Matricule Coupeur *",
                        options=[""] + employee_options,
                        format_func=lambda x: "Sélectionner un employé..." if x == "" else x,
                        help="Sélectionnez le coupeur assigné"
                    )
                    if selected_employee:
                        matricule_selected = selected_employee.split(" - ")[0]
                    else:
                        matricule_selected = ""
                else:
                    st.warning("Aucun employé trouvé dans la base de données")
                    matricule_selected = ""

                consommation = st.number_input("Consommation (m²) *", min_value=0.0, step=0.01, value=2.5,
                                               format="%.2f", help="Surface de matière nécessaire par paire")
                observation = st.text_area("Observations",
                                           placeholder="Remarques spécifiques, exigences particulières...")

            # Boutons de soumission
            st.markdown("---")
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submitted = st.form_submit_button("✅ Créer l'OF", use_container_width=True, type="primary")

            if submitted:
                # Validation
                required_fields = [of, modele, couleur_modele, coloris, matiere, code_modele]
                if not all(required_fields):
                    st.error("❌ Remplissez tous les champs obligatoires!")
                elif not matricule_selected:
                    st.error("❌ Veuillez sélectionner un matricule coupeur!")
                else:
                    if not self.db_manager.get_order_by_of(of):
                        if self.db_manager.create_order(
                                of=of,
                                modele=modele,
                                code_modele=code_modele,
                                couleur_modele=couleur_modele,
                                quantite=quantite,
                                coloris=coloris,
                                matiere=matiere,
                                matricule_coupeur=matricule_selected,
                                consommation=consommation,
                                sur_consommation=0,
                                observation=observation
                        ):
                            st.success(f"✅ OF {of} créé avec succès!")
                            # Réinitialiser les variables de session
                            st.session_state.selected_code_modele = ""
                            st.session_state.auto_nom_modele = ""
                            st.session_state.auto_matiere = ""
                            st.session_state.auto_consignes = ""
                            st.session_state.auto_emport_piece = ""
                            st.session_state.selected_code_couleur = ""
                            st.session_state.auto_nom_couleur = ""
                            time.sleep(1.5)
                            st.rerun()
                    else:
                        st.error(f"❌ L'OF {of} existe déjà !")

    def _render_manage_of(self):
        """Affiche la gestion des OF en cours"""
        st.markdown('<div class="section-header">Gestion des OF en Cours</div>', unsafe_allow_html=True)

        orders = self.db_manager.get_all_orders()
        # Inclure les OF en cours ET les OF à retravailler
        of_disponibles = [o for o in orders if o['statut_coupe'] in ['En attente', 'En cours'] or
                          o['statut_controle'] == 'À retravailler 🔧']

        if of_disponibles:
            # Afficher la section gestion de sur-consommation en haut
            self._render_sur_consommation_section(of_disponibles)

            st.markdown("---")

            # Puis afficher les OF
            for order in of_disponibles:
                with st.container():
                    # Déterminer si c'est un retour à la coupe
                    is_retour_coupe = order['statut_controle'] == 'À retravailler 🔧'

                    # Style différent pour les retours
                    card_class = "alert-card" if is_retour_coupe else "info-card"
                    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

                    col_info, col_timer, col_actions = st.columns([2.5, 2.5, 1.5])

                    # RÉCUPÉRER LES DONNÉES DU MODÈLE
                    modele_info = self.db_manager.get_modele_by_nom(order.get('modele', ''))
                    consignes_coupe = modele_info.get('consignes_de_coupe', '') if modele_info else ''
                    emport_piece = modele_info.get('emport_de_piece', '') if modele_info else ''

                    with col_info:
                        # Header avec signal pour les retours
                        if is_retour_coupe:
                            st.markdown(f"**🔧 RETOUR À LA COUPE - OF:** `{order['of']}`")
                        else:
                            st.markdown(f"**OF:** `{order['of']}`")

                        st.markdown(f"**Modèle:** {order['modele']} - {order['couleur_modele']}")

                        # Afficher les détails qualité si c'est un retour
                        if is_retour_coupe:
                            quality_details = self.utils.get_quality_details(order)
                            quantite_retravailler = quality_details['retravailler']

                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); 
                                        padding: 10px; 
                                        border-radius: 8px; 
                                        border-left: 4px solid #F59E0B;
                                        margin: 10px 0;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span style="font-size: 1.2rem;">🔧</span>
                                    <span style="font-weight: 700; color: #92400E;">
                                        QUANTITÉ À RETRAVAILLER: {quantite_retravailler} paires
                                    </span>
                                </div>
                                <div style="color: #92400E; font-size: 0.85rem; margin-top: 5px;">
                                    ⏸️ Compteur en pause
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Détails complets du retour
                            with st.expander("📊 Détails du retour qualité", expanded=False):
                                st.markdown(f"""
                                **Analyse qualité précédente:**
                                - Total contrôlé: {order.get('quantite_controlee', 0)}/{order['quantite']} paires
                                - ✅ Acceptées: {quality_details['acceptee']} paires ({quality_details['acceptee_pourcentage']:.1f}%)
                                - ❌ Rejetées: {quality_details['rejetee']} paires (définitives - {quality_details['rejetee_pourcentage']:.1f}%)
                                - 🔧 À retravailler: {quantite_retravailler} paires ({quality_details['retravailler_pourcentage']:.1f}%)

                                **Temps précédent:** {self.utils.format_time(order.get('temps_coupe', 0))}
                                **Nouvelle production:** {quantite_retravailler} paires à reproduire
                                """)

                                if order.get('observation_controle'):
                                    st.markdown("**📝 Observations qualité:**")
                                    st.info(order['observation_controle'])

                        # Informations standard
                        st.markdown(
                            f"**Quantité:** {order['quantite']} | **Coloris:** {order['coloris']} | **Matière:** {order['matiere']}")

                        # AFFICHAGE DES CONSIGNES ET IMPORT DE PIÈCE - DANS COL_INFO
                        if consignes_coupe or emport_piece:
                            st.markdown("---")

                            if consignes_coupe:
                                st.markdown(f"""
                                <div style="border: 2px solid #3B82F6; 
                                            border-radius: 6px; 
                                            padding: 10px; 
                                            background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
                                            margin: 8px 0;">
                                    <div style="font-weight: 700; color: #0C3B82; font-size: 0.95rem; margin-bottom: 8px;">
                                        📋 CONSIGNES DE COUPE
                                    </div>
                                    <div style="color: #1E40AF; font-size: 0.85rem; line-height: 1.5;">
                                        {consignes_coupe}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                            if emport_piece:
                                st.markdown(f"""
                                <div style="border: 2px solid #3B82F6; 
                                            border-radius: 6px; 
                                            padding: 10px; 
                                            background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
                                            margin: 8px 0;">
                                    <div style="font-weight: 700; color: #0C3B82; font-size: 0.95rem; margin-bottom: 8px;">
                                        📦 IMPORT DE PIÈCE
                                    </div>
                                    <div style="color: #1E40AF; font-size: 0.85rem; line-height: 1.5;">
                                        {emport_piece}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                        if order.get('observation') and not is_retour_coupe:
                            with st.expander("📝 Observations"):
                                st.write(order['observation'])

                    with col_timer:
                        # AFFICHAGE DU CHRONOMÈTRE
                        if is_retour_coupe:
                            # Pour les retours, afficher les temps précédents
                            elapsed = order.get('temps_coupe', 0) or 0
                            time_display = self.utils.format_time(elapsed)

                            # Si en pause, afficher le temps avant pause
                            if order.get('coupe_en_pause'):
                                elapsed_pause = order.get('temps_coupe_avant_pause', elapsed) or elapsed
                                time_display = self.utils.format_time(elapsed_pause)
                                st.markdown(f'<div class="timer-paused">{time_display}</div>', unsafe_allow_html=True)
                                st.markdown(f"**⏸️ COMPTEUR PAUSÉ**")
                            else:
                                st.markdown(f'<div class="timer-display">{time_display}</div>', unsafe_allow_html=True)
                                st.markdown(f"**EN ATTENTE**")

                            # Afficher le temps total précédent
                            st.markdown(f"""
                            <div style="background: #F3F4F6; padding: 8px; border-radius: 6px; margin-top: 10px; text-align: center;">
                                <div style="font-size: 0.85rem; color: #6B7280;">Temps coupe initial</div>
                                <div style="font-weight: 700; color: #1F2937;">{self.utils.format_time(order.get('temps_coupe', 0))}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        elif order['statut_coupe'] == 'En cours':
                            # COUPE EN COURS - afficher le chrono EN DIRECT
                            if order.get('coupe_en_pause'):
                                # EN PAUSE - afficher temps avant pause
                                elapsed = order.get('temps_coupe_avant_pause', 0) or 0
                                status_text = "⏸️ EN PAUSE"
                                st.markdown(f'<div class="timer-paused">{self.utils.format_time(elapsed)}</div>',
                                            unsafe_allow_html=True)
                            else:
                                # EN COURS - afficher temps courant
                                elapsed = order.get('temps_coupe', 0) or 0
                                status_text = "🔄 EN COURS"
                                st.markdown(f'<div class="timer-display">{self.utils.format_time(elapsed)}</div>',
                                            unsafe_allow_html=True)

                            st.markdown(f"**{status_text}**")

                            # Afficher les pauses
                            pause_info = self.utils.get_pause_info(order)
                            if pause_info:
                                st.markdown(f'<div class="pause-info">{pause_info}</div>', unsafe_allow_html=True)

                        else:
                            # EN ATTENTE
                            st.info("⏳ En attente de démarrage")

                    with col_actions:
                        # Si c'est un retour à la coupe
                        if is_retour_coupe:
                            quality_details = self.utils.get_quality_details(order)
                            quantite_a_reproduire = quality_details['retravailler']

                            # Afficher les temps précédents
                            col_temps1, col_temps2 = st.columns(2)

                            with col_temps1:
                                st.metric(
                                    "⏱️ Initial",
                                    self.utils.format_time(order.get('temps_coupe', 0))
                                )

                            with col_temps2:
                                if order.get('temps_recoupe', 0) > 0:
                                    st.metric(
                                        "⏱️ Recoupe",
                                        self.utils.format_time(order.get('temps_recoupe', 0))
                                    )
                                else:
                                    st.metric(
                                        "⏱️ Recoupe",
                                        "---"
                                    )

                            st.markdown("---")

                            # Boutons d'action
                            col_btn1 = st.columns(1)[0]
                            with col_btn1:
                                if st.button("▶️ Reprendre", key=f"resume_retour_{order['of']}",
                                             use_container_width=True,
                                             type="primary"):
                                    nouveau_nombre = (order.get('nombre_recoupe', 0) or 0) + 1

                                    if self.db_manager.update_order(order['of'],
                                                                    statut_coupe='En cours',
                                                                    statut_controle='Contrôle partiel',
                                                                    coupe_en_pause=False,
                                                                    temps_recoupe=0,
                                                                    date_debut_recoupe=datetime.now(),
                                                                    date_derniere_pause=None,
                                                                    nombre_recoupe=nouveau_nombre,
                                                                    quantite=quantite_a_reproduire,
                                                                    date_derniere_maj_coupe=datetime.now()):
                                        st.success(
                                            f"▶️ Recoupe #{nouveau_nombre} démarrée!")
                                        time.sleep(1.5)
                                        st.rerun()



                        # Logique normale pour les OF non-retour
                        elif order['statut_coupe'] == 'En attente':
                            if st.button("▶️ Débuter", key=f"start_{order['of']}", use_container_width=True,
                                         type="primary"):
                                if self.db_manager.update_order(order['of'],
                                                                statut_coupe='En cours',
                                                                date_debut_coupe=datetime.now(),
                                                                date_derniere_maj_coupe=datetime.now()):
                                    st.rerun()

                        elif order['statut_coupe'] == 'En cours':
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if order.get('coupe_en_pause'):
                                    if st.button("▶️ Reprendre", key=f"resume_{order['of']}", use_container_width=True,
                                                 type="primary"):
                                        total_pause = self.utils.calculate_pause_duration(order, 'coupe')
                                        if self.db_manager.update_order(order['of'],
                                                                        coupe_en_pause=False,
                                                                        duree_totale_pause=total_pause,
                                                                        date_derniere_pause=None,
                                                                        date_derniere_maj_coupe=datetime.now()):
                                            st.rerun()
                                else:
                                    if st.button("⏸️ Pause", key=f"pause_{order['of']}", use_container_width=True):
                                        if self.db_manager.update_order(order['of'],
                                                                        coupe_en_pause=True,
                                                                        temps_coupe_avant_pause=order.get('temps_coupe',
                                                                                                          0),
                                                                        date_derniere_pause=datetime.now(),
                                                                        date_derniere_maj_coupe=datetime.now()):
                                            st.rerun()
                            with col_btn2:
                                if not order.get('coupe_en_pause'):
                                    if st.button("✅ Terminer", key=f"finish_{order['of']}", use_container_width=True,
                                                 type="primary"):
                                        if self.db_manager.update_order(order['of'],
                                                                        statut_coupe='Terminée',
                                                                        date_fin_coupe=datetime.now(),
                                                                        quantite_a_controler=order['quantite'],
                                                                        date_derniere_maj_coupe=datetime.now()):
                                            st.success(f"✅ Coupe terminée!")
                                            time.sleep(1.5)
                                            st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)
                    st.divider()
        else:
            st.info("🎉 Tous les OF sont terminés!")

            if orders:
                st.markdown("### 📊 Statistiques du Jour")

                # Calculer les retours à la coupe
                of_retour_coupe = [o for o in orders if o['statut_controle'] == 'À retravailler 🔧']
                total_retour_coupe = len(of_retour_coupe)
                total_paires_retour = sum(self.utils.get_quality_details(o)['retravailler'] for o in of_retour_coupe)

                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                with col_stat1:
                    total_of = len(orders)
                    st.metric("Total OF", total_of)
                with col_stat2:
                    of_termines = len([o for o in orders if o['statut_coupe'] == 'Terminée' and
                                       o['statut_controle'] in ['Approuvé ✅', 'Terminée']])
                    st.metric("OF Terminés", of_termines)
                with col_stat3:
                    total_paires = sum(o['quantite'] for o in orders)
                    st.metric("Paires Total", f"{total_paires:,}")
                with col_stat4:
                    if total_retour_coupe > 0:
                        st.metric("🔧 Retours", f"{total_retour_coupe}",
                                  delta=f"{total_paires_retour} paires")
                    else:
                        st.metric("🔧 Retours", "0")

    def _render_sur_consommation_section(self, orders: List[Dict]):
        """Affiche une section séparée pour gérer la sur-consommation"""
        st.markdown('<div class="section-header">📦 Gestion de la Sur-consommation</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown("""
            <div class="info-card">
                <h4>📋 Informations</h4>
                Enregistrez la sur-consommation observée lors de la coupe pour chaque OF.
                Cette information permet de suivre les pertes et d'optimiser la consommation.
            </div>
            """, unsafe_allow_html=True)

            col_select = st.columns(1)[0]

            with col_select:
                # Créer une liste des OF en cours ou en attente
                of_choices = [f"{o['of']} - {o['modele']}" for o in orders if
                              o['statut_coupe'] in ['En attente', 'En cours']]

                if of_choices:
                    selected_of_info = st.selectbox(
                        "Sélectionner un OF",
                        of_choices,
                        key="sur_consommation_select",
                        help="Choisissez l'OF pour lequel vous souhaitez enregistrer la sur-consommation"
                    )

                    if selected_of_info:
                        of_number = selected_of_info.split(" - ")[0]
                        selected_order = self.db_manager.get_order_by_of(of_number)

                        if selected_order:
                            # Afficher les informations actuelles
                            col_info1, col_info2, col_info3 = st.columns(3)

                            # Convertir en float pour éviter les erreurs Decimal
                            consommation = float(selected_order['consommation'] or 0)
                            current_surcons = float(selected_order.get('sur_consommation', 0) or 0)
                            total = consommation + current_surcons

                            with col_info1:
                                st.metric("Consommation Standard", f"{consommation:.2f} m²")

                            with col_info2:
                                st.metric("Sur-consommation Actuelle", f"{current_surcons:.2f} m²")

                            with col_info3:
                                st.metric("Total par Paire", f"{total:.2f} m²")

                            # Formulaire d'enregistrement
                            st.markdown("---")
                            with st.form(f"sur_consommation_form_{of_number}", clear_on_submit=True):
                                st.markdown("**Enregistrement de Sur-consommation**")

                                nouvelle_surcons = st.number_input(
                                    "Nouvelle valeur de sur-consommation (m²)",
                                    min_value=0.0,
                                    step=0.01,
                                    value=current_surcons,
                                    format="%.2f",
                                    key=f"input_surcons_{of_number}",
                                    help="Indiquez la surface supplémentaire consommée (pertes, découpe, etc.)"
                                )

                                raison = st.text_area(
                                    "Raison de la sur-consommation",
                                    placeholder="Ex: Perte matière, defaut découpe, retouches...",
                                    key=f"raison_surcons_{of_number}",
                                    help="Expliquez pourquoi il y a une sur-consommation"
                                )

                                # Aperçu
                                if nouvelle_surcons != current_surcons:
                                    difference = nouvelle_surcons - current_surcons
                                    direction = "augmentation" if difference > 0 else "réduction"
                                    nouveau_total = consommation + nouvelle_surcons
                                    st.markdown(f"""
                                    <div style="background: #F0FDF4; padding: 10px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #10B981;">
                                        <div style="color: #065F46; font-weight: 600;">
                                            {direction.upper()} : {abs(difference):.2f} m² → Total: {nouveau_total:.2f} m²
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)

                                col_btn1, col_btn2 = st.columns(2)

                                with col_btn1:
                                    submitted = st.form_submit_button("💾 Enregistrer", use_container_width=True,
                                                                      type="primary")

                                with col_btn2:
                                    reset_submitted = st.form_submit_button("🗑️ Effacer", use_container_width=True)

                                # ===== CORRECTION: AJOUTER LE CODE POUR ENREGISTRER =====
                                if submitted:
                                    try:
                                        if self.db_manager.update_order(
                                                of_number,
                                                sur_consommation=nouvelle_surcons
                                        ):
                                            # Ajouter la raison dans l'observation si fournie
                                            if raison:
                                                current_obs = selected_order.get('observation_coupe', '') or ''
                                                new_obs = current_obs + f"\n\n📦 Sur-consommation ({datetime.now().strftime('%d/%m/%Y %H:%M')}): {nouvelle_surcons:.2f} m² - {raison}"
                                                self.db_manager.update_order(
                                                    of_number,
                                                    observation_coupe=new_obs
                                                )

                                            st.success(f"✅ Sur-consommation enregistrée: {nouvelle_surcons:.2f} m²")
                                            time.sleep(1.5)
                                            st.rerun()
                                        else:
                                            st.error("❌ Erreur lors de l'enregistrement")
                                    except Exception as e:
                                        st.error(f"❌ Erreur: {str(e)}")

                                if reset_submitted:
                                    try:
                                        if self.db_manager.update_order(
                                                of_number,
                                                sur_consommation=0.0
                                        ):
                                            st.success("✅ Sur-consommation réinitialisée à 0")
                                            time.sleep(1.5)
                                            st.rerun()
                                        else:
                                            st.error("❌ Erreur lors de la réinitialisation")
                                    except Exception as e:
                                        st.error(f"❌ Erreur: {str(e)}")

                else:
                    st.info("Aucun OF en cours ou en attente")