# pages/chef_piqure_page.py - Page chef piqûre
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time
from datetime import datetime, timedelta
from database import DatabaseManager, Utils
from typing import List, Dict, Optional


class ChefPiqurePage:
    """Page chef piqûre - Gestion des opérations de piqûre"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.utils = Utils()

    def render(self):
        """Affiche la page chef de piqûre"""
        st_autorefresh(interval=5000, limit=1000, key="chef_piqure_refresh")

        # Forcer le refresh des données
        st.cache_data.clear()
        st.markdown('<div class="main-header">🪡 Interface Chef de Piqûre</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Gestion des Opérations de Piqûre • Suivi en temps réel</div>',
                    unsafe_allow_html=True)

        self.db_manager.update_all_timers()

        if 'last_activity' in st.session_state:
            if datetime.now() - st.session_state.last_activity > timedelta(minutes=30):
                st.warning("⚠️ Session expirée")
                st.session_state.logged_in = False
                st.rerun()
            else:
                st.session_state.last_activity = datetime.now()

        # Récupérer TOUS les ordres
        orders = self.db_manager.get_all_orders()

        # Filtrer les OF éligibles pour la piqûre
        of_prets_piqure = []

        for order in orders:
            # Vérifier si la coupe est terminée
            coupe_terminee = order['statut_coupe'] == 'Terminée'

            # Vérifier si le contrôle est terminé (n'importe quel statut sauf 'En attente' et 'En cours')
            controle_valide = order['statut_controle'] not in ['En attente', 'En cours']

            # Vérifier si la piqûre n'est pas déjà en cours ou terminée
            statut_piqure = order.get('statut_piqure')
            piqure_non_demarree = statut_piqure in [None, 'En attente', 'Non démarré']

            # Vérifier l'éligibilité
            if coupe_terminee and controle_valide and piqure_non_demarree:
                of_prets_piqure.append(order)

        # Filtrer les OF déjà en piqûre
        of_en_piqure = [o for o in orders if o.get('statut_piqure') in ['En cours', 'En attente']]

        # Afficher une alerte s'il y a des OF prêts
        if of_prets_piqure:
            total_prets = len(of_prets_piqure)
            total_paires_prets = sum(o['quantite'] for o in of_prets_piqure)

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); 
                        padding: 15px; 
                        border-radius: 12px; 
                        border-left: 6px solid #10B981;
                        margin-bottom: 20px;
                        border: 1px solid #6EE7B7;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                    <span style="font-size: 1.5rem;">✅</span>
                    <div>
                        <div style="font-weight: 700; color: #065F46; font-size: 1.1rem;">
                            {total_prets} OF PRÊTS POUR LA PIQÛRE
                        </div>
                        <div style="color: #065F46; font-size: 0.9rem;">
                            Total: {total_paires_prets} paires - Coupe terminée + Contrôle validé
                        </div>
                    </div>
                </div>
                <div style="font-size: 0.85rem; color: #065F46; margin-top: 10px;">
                    ✅ Conditions: Coupe terminée + Contrôle validé (quel que soit le résultat)
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Afficher les OF déjà en piqûre
        if of_en_piqure:
            total_en_piqure = len(of_en_piqure)
            total_paires_en_piqure = sum(o['quantite'] for o in of_en_piqure)

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #E0E7FF 0%, #C7D2FE 100%); 
                        padding: 15px; 
                        border-radius: 12px; 
                        border-left: 6px solid #4F46E5;
                        margin-bottom: 20px;
                        border: 1px solid #818CF8;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                    <span style="font-size: 1.5rem;">🪡</span>
                    <div>
                        <div style="font-weight: 700; color: #3730A3; font-size: 1.1rem;">
                            {total_en_piqure} OF EN PIQÛRE
                        </div>
                        <div style="color: #3730A3; font-size: 0.9rem;">
                            Total: {total_paires_en_piqure} paires en cours de piqûre
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🪡 Démarrer Piqûre", "⏱️ Gestion en cours"])

        with tab1:
            self._render_start_piqure(of_prets_piqure)

        with tab2:
            self._render_manage_piqure(of_en_piqure)

    # MODIFICATION dans chef_piqure_page.py - Méthode _render_start_piqure

    def _render_start_piqure(self, of_prets_piqure: List[Dict]):
        """Affiche le formulaire pour démarrer une opération de piqûre"""
        st.markdown('<div class="section-header">Démarrer une Opération de Piqûre</div>', unsafe_allow_html=True)

        if not of_prets_piqure:
            st.info("🔋 Aucun OF prêt pour la piqûre. Conditions requises :")
            st.markdown("""
            <div class="info-card">
                <h4>🔋 Conditions pour démarrer la piqûre :</h4>
                <ul>
                    <li>✅ <b>Coupe terminée</b> (statut: Terminée)</li>
                    <li>✅ <b>Contrôle qualité validé</b> (statut: N'importe quel statut SAUF "En attente" ou "En cours")</li>
                    <li>⏳ <b>Piqûre non encore démarrée</b> (statut: En attente ou Non démarré)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            return

        # Récupérer la liste des employés
        employees = self.db_manager.get_all_employees()

        with st.form("form_piqure_start", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                # Sélectionner l'OF
                of_options = [f"{o['of']} - {o['modele']} ({o['quantite']} paires)" for o in of_prets_piqure]
                selected_of_info = st.selectbox(
                    "OF à piquer *",
                    of_options,
                    help="Sélectionnez l'OF dont la coupe est terminée"
                )

                if selected_of_info:
                    of_number = selected_of_info.split(" - ")[0]
                    selected_order = next((o for o in of_prets_piqure if o['of'] == of_number), None)

                    if selected_order:
                        # Afficher les détails de l'OF
                        st.markdown(f"""
                        <div style="background: #F0FDF4; padding: 15px; border-radius: 10px; margin: 10px 0; border: 1px solid #A7F3D0;">
                            <div style="font-weight: 700; color: #065F46; font-size: 1.1rem; margin-bottom: 10px;">
                                🔋 Détails de l'OF sélectionné
                            </div>
                            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                                <tr>
                                    <td style="padding: 6px 0; font-weight: 600; color: #047857; width: 40%;">OF:</td>
                                    <td style="padding: 6px 0;"><strong>{selected_order['of']}</strong></td>
                                </tr>
                                <tr>
                                    <td style="padding: 6px 0; font-weight: 600; color: #047857;">Modèle:</td>
                                    <td style="padding: 6px 0;">{selected_order['modele']}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 6px 0; font-weight: 600; color: #047857;">Couleur:</td>
                                    <td style="padding: 6px 0;">{selected_order['couleur_modele']}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 6px 0; font-weight: 600; color: #047857;">Matière:</td>
                                    <td style="padding: 6px 0;">{selected_order['matiere']}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 6px 0; font-weight: 600; color: #047857;">Quantité:</td>
                                    <td style="padding: 6px 0;"><strong>{selected_order['quantite']} paires</strong></td>
                                </tr>
                                <tr>
                                    <td style="padding: 6px 0; font-weight: 600; color: #047857;">Statut Coupe:</td>
                                    <td style="padding: 6px 0;">
                                        <span style="color: #10B981; font-weight: 600;">✅ {selected_order['statut_coupe']}</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 6px 0; font-weight: 600; color: #047857;">Statut Contrôle:</td>
                                    <td style="padding: 6px 0;">
                                        <span style="{'color: #10B981;' if selected_order['statut_controle'] == 'Approuvé ✅' else 'color: #F59E0B;'} font-weight: 600;">
                                            {'✅' if selected_order['statut_controle'] == 'Approuvé ✅' else '⚠️'} {selected_order['statut_controle']}
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)

                        # Afficher un avertissement si le contrôle a détecté des problèmes
                        if selected_order['statut_controle'] in ['Contrôle complet avec retours 📊', 'À retravailler 🔧']:
                            quantite_retravailler = selected_order.get('quantite_retravailler', 0) or 0
                            quantite_rejetee = selected_order.get('quantite_rejetee', 0) or 0

                            st.markdown(f"""
                            <div style="background: #FEF3C7; padding: 12px; border-radius: 8px; border-left: 4px solid #F59E0B; margin: 10px 0;">
                                <div style="font-weight: 700; color: #92400E; margin-bottom: 8px;">
                                    ⚠️ Contrôle avec problèmes détectés
                                </div>
                                <div style="font-size: 0.9rem; color: #92400E;">
                                    • 🔧 Paires à retravailler: {quantite_retravailler}<br>
                                    • ❌ Paires rejetées: {quantite_rejetee}<br>
                                    • ✅ Paires acceptées: {selected_order['quantite'] - quantite_rejetee - quantite_retravailler}
                                </div>
                                <div style="font-size: 0.85rem; color: #92400E; margin-top: 8px;">
                                    <strong>Note:</strong> La piqûre sera faite sur les paires acceptées seulement.
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

            with col2:
                # Sélecteur Matricule Piqueur
                if employees:
                    employee_options = [f"{emp['matricule']} - {emp['nom']} {emp['prenom']}" for emp in employees]
                    selected_employee = st.selectbox(
                        "Matricule Piqueur *",
                        options=[""] + employee_options,
                        format_func=lambda x: "Sélectionner un piqueur..." if x == "" else x,
                        help="Sélectionnez le piqueur assigné"
                    )
                    if selected_employee:
                        matricule_selected = selected_employee.split(" - ")[0]
                    else:
                        matricule_selected = ""
                else:
                    st.warning("Aucun employé trouvé dans la base de données")
                    matricule_selected = ""

                # Observation
                observation = st.text_area(
                    "Observations",
                    placeholder="Remarques spécifiques pour cette opération de piqûre...",
                    key="obs_piqure_start",
                    height=100
                )

            # Boutons de soumission
            st.markdown("---")
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                # ===== MODIFICATION: Désactiver le bouton si piqûre existe déjà =====
                button_disabled = False
                button_label = "▶️ Démarrer la Piqûre"

                if selected_of_info and selected_of_info != "Choisir un OF...":
                    of_number = selected_of_info.split(" - ")[0]
                    selected_order = self.db_manager.get_order_by_of(of_number)

                    if selected_order and selected_order.get('statut_piqure') not in [None, 'En attente',
                                                                                      'Non démarré']:
                        button_disabled = True
                        statut_piqure_actual = selected_order.get('statut_piqure', 'Inconnue')
                        button_label = f"✅ Piqûre déjà {statut_piqure_actual}"

                submitted = st.form_submit_button(
                    button_label,
                    use_container_width=True,
                    type="primary",
                    disabled=button_disabled  # Désactiver si piqûre existe
                )

                if button_disabled and selected_of_info and selected_of_info != "Choisir un OF...":
                    st.warning(
                        f"⚠️ Cet OF a déjà une opération de piqûre en cours ou terminée. Impossible de redémarrer.")

            if submitted:
                if not matricule_selected:
                    st.error("❌ Veuillez sélectionner un matricule piqueur!")
                elif not selected_of_info:
                    st.error("❌ Veuillez sélectionner un OF!")
                else:
                    # Vérifier à nouveau que l'OF est toujours éligible
                    check_order = self.db_manager.get_order_by_of(of_number)
                    if not check_order:
                        st.error(f"❌ L'OF {of_number} n'existe plus dans la base de données!")
                    else:
                        # Vérifier les conditions
                        coupe_ok = check_order['statut_coupe'] == 'Terminée'
                        controle_ok = check_order['statut_controle'] not in ['En attente', 'En cours']
                        piqure_ok = check_order.get('statut_piqure') in [None, 'En attente', 'Non démarré']

                        if not coupe_ok:
                            st.error(
                                f"❌ La coupe de l'OF {of_number} n'est pas terminée! (Statut: {check_order['statut_coupe']})")
                        elif not controle_ok:
                            st.error(
                                f"❌ Le contrôle de l'OF {of_number} n'est pas encore terminé! (Statut: {check_order['statut_controle']})")
                        elif not piqure_ok:
                            st.error(
                                f"❌ Une opération de piqûre existe déjà pour cet OF! (Statut: {check_order['statut_piqure']})")
                        else:
                            # Démarrer l'opération de piqûre
                            if self.db_manager.start_piqure(
                                    of_number=of_number,
                                    matricule_piqueur=matricule_selected,
                                    observation=observation
                            ):
                                st.success(f"✅ Piqûre démarrée pour OF {of_number}!")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors du démarrage de la piqûre.")

    def _render_manage_piqure(self, of_en_piqure: List[Dict]):
        """Affiche la gestion des OF en cours de piqûre"""
        st.markdown('<div class="section-header">Gestion des Piqûres en Cours</div>', unsafe_allow_html=True)

        if not of_en_piqure:
            st.info("🎉 Aucune piqûre en cours!")
            return

        for order in of_en_piqure:
            with st.container():
                st.markdown('<div class="info-card">', unsafe_allow_html=True)

                col_info, col_timer, col_actions = st.columns([2.5, 2.5, 1.5])

                with col_info:
                    st.markdown(f"**OF:** `{order['of']}`")
                    st.markdown(f"**Modèle:** {order['modele']} - {order['couleur_modele']}")
                    st.markdown(
                        f"**Quantité:** {order['quantite']} | **Piqueur:** {order.get('matricule_piqueur', 'N/A')}")

                    if order.get('observation_piqure'):
                        with st.expander("📝 Observations"):
                            st.write(order['observation_piqure'])

                with col_timer:
                    # AFFICHAGE DU CHRONOMÈTRE
                    if order.get('statut_piqure') == 'En cours':
                        if order.get('piqure_en_pause'):
                            # EN PAUSE - afficher temps avant pause
                            elapsed = order.get('temps_piqure_avant_pause', 0) or 0
                            status_text = "⏸️ EN PAUSE"
                            st.markdown(f'<div class="timer-paused">{self.utils.format_time(elapsed)}</div>',
                                        unsafe_allow_html=True)
                        else:
                            # EN COURS - afficher temps courant
                            elapsed = order.get('temps_piqure', 0) or 0
                            status_text = "🔄 EN COURS"
                            st.markdown(f'<div class="timer-display">{self.utils.format_time(elapsed)}</div>',
                                        unsafe_allow_html=True)

                        st.markdown(f"**{status_text}**")

                        # Afficher les pauses
                        pause_info = self.utils.get_pause_info_piqure(order)
                        if pause_info:
                            st.markdown(f'<div class="pause-info">{pause_info}</div>', unsafe_allow_html=True)

                    else:
                        # EN ATTENTE
                        st.info("⏳ En attente de démarrage")

                with col_actions:
                    if order.get('statut_piqure') == 'En attente':
                        if st.button("▶️ Débuter", key=f"start_piqure_{order['of']}", use_container_width=True,
                                     type="primary"):
                            if self.db_manager.update_order(order['of'],
                                                            statut_piqure='En cours',
                                                            date_debut_piqure=datetime.now(),
                                                            date_derniere_maj_piqure=datetime.now()):
                                st.rerun()

                    elif order.get('statut_piqure') == 'En cours':
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if order.get('piqure_en_pause'):
                                if st.button("▶️ Reprendre", key=f"resume_piqure_{order['of']}",
                                             use_container_width=True,
                                             type="primary"):
                                    total_pause = self.utils.calculate_pause_duration(order, 'piqure')
                                    if self.db_manager.update_order(order['of'],
                                                                    piqure_en_pause=False,
                                                                    duree_totale_pause_piqure=total_pause,
                                                                    date_derniere_pause_piqure=None,
                                                                    date_derniere_maj_piqure=datetime.now()):
                                        st.rerun()
                            else:
                                if st.button("⏸️ Pause", key=f"pause_piqure_{order['of']}", use_container_width=True):
                                    if self.db_manager.update_order(order['of'],
                                                                    piqure_en_pause=True,
                                                                    temps_piqure_avant_pause=order.get('temps_piqure',
                                                                                                       0),
                                                                    date_derniere_pause_piqure=datetime.now(),
                                                                    date_derniere_maj_piqure=datetime.now()):
                                        st.rerun()
                        with col_btn2:
                            if not order.get('piqure_en_pause'):
                                if st.button("✅ Terminer", key=f"finish_piqure_{order['of']}", use_container_width=True,
                                             type="primary"):
                                    if self.db_manager.update_order(order['of'],
                                                                    statut_piqure='Terminée',
                                                                    date_fin_piqure=datetime.now(),
                                                                    date_derniere_maj_piqure=datetime.now()):
                                        st.success(f"✅ Piqûre terminée!")
                                        time.sleep(1.5)
                                        st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)
                st.divider()