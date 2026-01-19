# pages/controle_qualite_page.py - Page contrôle qualité
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time
from datetime import datetime, timedelta
from database import DatabaseManager, Utils
from typing import Dict, List


class ControleQualitePage:
    """Page contrôle qualité"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.utils = Utils()

    def render(self):
        """Affiche la page contrôle qualité"""
        st_autorefresh(interval=5000, limit=100, key="controle_refresh")

        st.markdown('<div class="main-header">👌 Interface Contrôle Qualité</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Gestion Qualité • Inspection et Validation</div>', unsafe_allow_html=True)

        self.db_manager.update_all_timers()

        if 'last_activity' in st.session_state:
            if datetime.now() - st.session_state.last_activity > timedelta(minutes=30):
                st.warning("⚠️ Session expirée")
                st.session_state.logged_in = False
                st.rerun()
            else:
                st.session_state.last_activity = datetime.now()

        orders = self.db_manager.get_all_orders()
        of_a_controler = [o for o in orders if o['statut_coupe'] in ['En cours', 'Terminée']]

        if not of_a_controler:
            st.info("⏳ Aucun OF en production")
            return

        # Statistiques
        st.markdown('<div class="section-header">📊 Tableau de Bord Qualité</div>', unsafe_allow_html=True)
        col_stats = st.columns(5)

        total_of = len(of_a_controler)
        of_en_coupe = len([o for o in of_a_controler if o['statut_coupe'] == 'En cours'])
        of_termine_coupe = len([o for o in of_a_controler if o['statut_coupe'] == 'Terminée'])
        total_paires = sum(o['quantite'] for o in of_a_controler)
        total_controlees = sum(o.get('quantite_controlee', 0) or 0 for o in of_a_controler)

        with col_stats[0]:
            st.metric("OF Total", total_of)
        with col_stats[1]:
            st.metric("En coupe", of_en_coupe)
        with col_stats[2]:
            st.metric("Coupe finie", of_termine_coupe)
        with col_stats[3]:
            st.metric("Contrôlées", f"{total_controlees:,}")
        with col_stats[4]:
            taux_controle = (total_controlees / total_paires * 100) if total_paires > 0 else 0
            st.metric("Taux Contrôle", f"{taux_controle:.1f}%")

        # Sélection OF
        st.markdown('<div class="section-header">👌 Contrôle des OF</div>', unsafe_allow_html=True)

        of_list = []
        for o in of_a_controler:
            status_icon = "🔄" if o['statut_coupe'] == 'En cours' else "✅"
            quantite_controlee = o.get('quantite_controlee', 0) or 0
            of_list.append(
                f"{status_icon} {o['of']} | {o['modele']} ({o['quantite']} paires) [{quantite_controlee}/{o['quantite']}]")

        selected_of = st.selectbox("Sélectionnez un OF à contrôler", of_list,
                                   help="Choisissez l'OF pour démarrer ou continuer le contrôle")

        if selected_of:
            of_number = selected_of.split(" ")[1]
            current_order = self.db_manager.get_order_by_of(of_number)

            if current_order:
                self._render_order_control(current_order)

    def _render_order_control(self, order: Dict):
        """Affiche le contrôle d'un ordre spécifique"""
        # DEBUG amélioré
        print(f"\n🎯 DEBUG CONTROLE PAGE pour OF: {order['of']}")
        print(f"   Statut contrôle: {order['statut_controle']}")
        print(f"   En pause: {order.get('controle_en_pause', 0)}")
        print(f"   Temps actif total: {order.get('temps_actif_total', 0)}s")
        print(f"   Temps pause total: {order.get('temps_pause_total', 0)}s")
        print(f"   Ancien temps contrôle: {order.get('temps_controle', 0)}s")
        print(f"   Date début: {order.get('date_debut_controle')}")
        print(f"   Date dernière maj: {order.get('date_derniere_maj')}")

        # Info OF
        col_info1, col_info2 = st.columns(2)

        with col_info1:
            st.markdown(
                f"<div class='info-card'><h4>📊 Informations OF</h4><b>OF:</b> {order['of']}<br><b>Modèle:</b> {order['modele']}<br><b>Couleur:</b> {order['couleur_modele']}<br><b>Quantité:</b> {order['quantite']} paires</div>",
                unsafe_allow_html=True)

        with col_info2:
            # Afficher les DEUX chronomètres dans la carte
            temps_actif = order.get('temps_actif_total', 0) or 0
            temps_pause = order.get('temps_pause_total', 0) or 0

            st.markdown(
                f"<div class='info-card'><h4>⏱️ Chronomètres</h4>"
                f"<b>🔄 Production:</b> {self.utils.format_time(temps_actif)}<br>"
                f"<b>⏸️ Pauses:</b> {self.utils.format_time(temps_pause)}<br>"
                f"<b>📊 Total:</b> {self.utils.format_time(temps_actif + temps_pause)}<br>"
                f"<b>État:</b> {'⏸️ EN PAUSE' if order.get('controle_en_pause') else '🔄 ACTIF'}</div>",
                unsafe_allow_html=True)

        # Progression avec prise en compte des retours
        quantite_totale = order['quantite']
        quantite_controlee = order.get('quantite_controlee', 0) or 0

        # ===== NOUVEAU: Ajouter les paires de recoupe dans le calcul =====
        quantite_retravailler = order.get('quantite_retravailler', 0) or 0
        quantite_rejetee = order.get('quantite_rejetee', 0) or 0

        # Total des paires à contrôler (production + retours)
        total_paires_a_controler = quantite_totale + quantite_retravailler + quantite_rejetee

        quantite_restante = total_paires_a_controler - quantite_controlee

        st.markdown('<div class="section-header">📊 Progression du Contrôle</div>', unsafe_allow_html=True)
        col_prog1, col_prog2, col_prog3 = st.columns(3)
        with col_prog1:
            st.metric("Contrôlées", f"{quantite_controlee}")
        with col_prog2:
            st.metric("Restantes", f"{quantite_restante}")
        with col_prog3:
            if total_paires_a_controler > 0:
                # ===== CORRECTION: Pourcentage basé sur production + retours =====
                pourcentage = (quantite_controlee / total_paires_a_controler) * 100
                st.metric("% Contrôle", f"{pourcentage:.1f}%")

        if total_paires_a_controler > 0:
            progress = quantite_controlee / total_paires_a_controler
            st.progress(min(1.0, progress))

            # Afficher la note si des retours existent
            if (quantite_retravailler + quantite_rejetee) > 0:
                st.caption(
                    f"📝 Note: Le pourcentage inclut {quantite_retravailler + quantite_rejetee} paires issues de recoupe")

        # Contrôle
        statut_controle = order['statut_controle']

        if statut_controle == 'En attente':
            self._render_start_control(order)
        elif statut_controle == 'En cours':
            self._render_ongoing_control(order)
        else:
            self._render_finished_control(order)

    def _render_start_control(self, order: Dict):
        """Affiche le début du contrôle"""
        st.markdown('<div class="quality-control-section"><h4>🚀 Début du Contrôle</h4></div>',
                    unsafe_allow_html=True)

        if order['statut_coupe'] != 'Terminée':
            st.markdown('<div class="warning-card">'
                        '<h4>⚠️ Information Importante</h4>'
                        '<b>La coupe est encore en cours.</b><br>'
                        'Vous ne pouvez contrôler qu\'une partie des paires pour le moment.<br>'
                        'Le contrôle complet sera possible une fois la coupe terminée.'
                        '</div>', unsafe_allow_html=True)

        max_quantite = order['quantite'] if order['statut_coupe'] == 'Terminée' else min(order['quantite'], 100)
        quantite_a_controler_input = st.number_input("Quantité à contrôler dans cette session",
                                                     min_value=1,
                                                     max_value=max_quantite,
                                                     value=min(max_quantite, 50),
                                                     step=1,
                                                     help="Nombre de paires à contrôler maintenant")

        col_start1, col_start2, col_start3 = st.columns([1, 2, 1])
        with col_start2:
            if st.button("🔄 Démarrer le Contrôle", width='stretch', type="primary"):
                if self.db_manager.start_controle(order['of'], quantite_a_controler_input):
                    st.success(f"✅ Contrôle démarré pour {quantite_a_controler_input} paires!")
                    time.sleep(1)
                    st.rerun()

    def _render_ongoing_control(self, order: Dict):
        """Affiche le contrôle en cours avec DEUX chronomètres indépendants"""
        st.markdown('<div class="quality-control-section"><h4>🔄 Contrôle en Cours</h4></div>',
                    unsafe_allow_html=True)

        # Afficher les DEUX chronomètres
        temps_actif = order.get('temps_actif_total', 0) or 0
        temps_pause = order.get('temps_pause_total', 0) or 0
        en_pause = order.get('controle_en_pause', False)

        # Convertir en int
        temps_actif = int(temps_actif) if temps_actif is not None else 0
        temps_pause = int(temps_pause) if temps_pause is not None else 0

        col_chrono1, col_chrono2 = st.columns(2)

        with col_chrono1:
            # Chrono 1: Temps actif de production
            if en_pause:
                st.markdown(f'''
                    <div class="timer-paused">
                        {self.utils.format_time(temps_actif)}
                    </div>
                ''', unsafe_allow_html=True)
                st.markdown("**⏸️ Production Figée**")
                st.info(f"Dernière valeur: {self.utils.format_time(temps_actif)}")
            else:
                st.markdown(f'''
                    <div class="timer-display" style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white;">
                        {self.utils.format_time(temps_actif)}
                    </div>
                ''', unsafe_allow_html=True)
                st.markdown("**🔄 Production en Cours**")
                st.success(f"Temps actif: {self.utils.format_time(temps_actif)}")

        with col_chrono2:
            # Chrono 2: Temps de pause
            if en_pause:
                st.markdown(f'''
                    <div class="timer-display" style="background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%); color: white;">
                        {self.utils.format_time(temps_pause)}
                    </div>
                ''', unsafe_allow_html=True)
                st.markdown("**⏸️ Pause en Cours**")
                st.warning(f"Pause accumulée: {self.utils.format_time(temps_pause)}")
            else:
                st.markdown(f'''
                    <div class="timer-display" style="background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: white;">
                        {self.utils.format_time(temps_pause)}
                    </div>
                ''', unsafe_allow_html=True)
                st.markdown("**📊 Total Pauses**")
                st.info(f"Pauses totales: {self.utils.format_time(temps_pause)}")






        # Boutons de contrôle
        quantite_a_controler = order.get('quantite_a_controler', 0) or 0
        quantite_controlee = order.get('quantite_controlee', 0) or 0
        quantite_restante = quantite_a_controler - quantite_controlee

        if quantite_restante > 0:
            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                if en_pause:
                    if st.button("▶️ Reprendre Production", key=f"resume_{order['of']}",
                                 width='stretch', type="primary"):
                        if self.db_manager.toggle_controle_pause(order['of'], False):
                            st.success("✅ Production reprise!")
                            time.sleep(1)
                            st.rerun()
                else:
                    if st.button("⏸️ Mettre en Pause", key=f"pause_{order['of']}",
                                 width='stretch'):
                        if self.db_manager.toggle_controle_pause(order['of'], True):
                            st.success("⏸️ Production en pause!")
                            time.sleep(1)
                            st.rerun()

            # Formulaire de contrôle (restera le même)
            with st.form(f"controle_form_{order['of']}"):
                st.markdown("#### 📝 Enregistrement des Contrôles")

                col_q1, col_q2, col_q3 = st.columns(3)

                with col_q1:
                    quantite_approuvee = st.number_input(
                        "✅ Approuvées",
                        min_value=0,
                        max_value=quantite_restante,
                        value=0,
                        step=1,
                        key=f"approuve_{order['of']}"
                    )

                with col_q2:
                    quantite_rejetee = st.number_input(
                        "❌ Rejetées",
                        min_value=0,
                        max_value=quantite_restante,
                        value=0,
                        step=1,
                        key=f"rejete_{order['of']}"
                    )

                with col_q3:
                    quantite_retravailler = st.number_input(
                        "🔧 À retravailler",
                        min_value=0,
                        max_value=quantite_restante,
                        value=0,
                        step=1,
                        key=f"retravailler_{order['of']}"
                    )

                total_session = quantite_approuvee + quantite_rejetee + quantite_retravailler

                if total_session > quantite_restante:
                    st.error(f"❌ La somme dépasse le maximum autorisé ({quantite_restante})!")
                elif total_session > 0:
                    st.markdown(f"""
                    <div style="background: #F0FDF4; padding: 12px; border-radius: 8px; margin: 10px 0;">
                        <div style="font-weight: bold; margin-bottom: 5px;">📊 Résumé de la session :</div>
                        <div>• Total paires contrôlées : <b>{total_session}</b></div>
                        <div>• ✅ Approuvées : {quantite_approuvee} ({quantite_approuvee / total_session * 100:.1f}%)</div>
                        <div>• ❌ Rejetées : {quantite_rejetee} ({quantite_rejetee / total_session * 100:.1f}%)</div>
                        <div>• 🔧 À retravailler : {quantite_retravailler} ({quantite_retravailler / total_session * 100:.1f}%)</div>
                    </div>
                    """, unsafe_allow_html=True)

                observation = st.text_area(
                    "Observations et remarques",
                    value=order.get('observation_controle', ''),
                    placeholder="Détails des défauts constatés, remarques qualité...",
                    key=f"obs_{order['of']}"
                )

                col_submit1, col_submit2 = st.columns(2)

                with col_submit1:
                    submitted = st.form_submit_button("💾 Enregistrer cette session", width='stretch')

                with col_submit2:
                    terminer = st.form_submit_button("✅ Terminer contrôle complet", width='stretch',
                                                     type="primary")

                if submitted or terminer:
                    if total_session == 0:
                        st.error("❌ Veuillez saisir au moins une paire à contrôler!")
                    else:
                        # Appeler la méthode de traitement
                        self._process_control_session(order, quantite_approuvee, quantite_rejetee,
                                                      quantite_retravailler, observation, terminer)

    def _render_finished_control(self, order: Dict):
        """Affiche le contrôle terminé"""
        st.markdown(
            f'<div class="quality-control-section"><h4>{self.utils.get_status_badge(order["statut_controle"])}</h4></div>',
            unsafe_allow_html=True)

        quantite_controlee = order.get('quantite_controlee', 0) or 0
        quantite_totale = order['quantite']

        # ===== NOUVEAU: Vérifier s'il y a des retours de recoupe =====
        quantite_retravailler = order.get('quantite_retravailler', 0) or 0
        quantite_rejetee = order.get('quantite_rejetee', 0) or 0

        # Calculer les paires restantes à contrôler (y compris les retours)
        paires_restantes_originales = quantite_totale - quantite_controlee
        paires_retour_recoupe = quantite_retravailler + quantite_rejetee

        # Total des paires à contrôler (originales + retours)
        total_a_controler = paires_restantes_originales + paires_retour_recoupe

        # Afficher une alerte si des retours de recoupe sont disponibles
        if paires_retour_recoupe > 0 and order['statut_coupe'] == 'Terminée':
            st.markdown(f'''
            <div class="info-notification">
                <h4>🔧 Paires issues de recoupe disponibles</h4>
                <div style="display: flex; gap: 20px; margin: 10px 0;">
                    <div style="flex: 1; background: #FEF3C7; padding: 10px; border-radius: 8px; border-left: 4px solid #F59E0B;">
                        <div style="font-size: 0.9rem; color: #92400E;">Retravaillées</div>
                        <div style="font-size: 1.2rem; font-weight: 700; color: #92400E;">{quantite_retravailler} paires</div>
                    </div>
                    <div style="flex: 1; background: #FEE2E2; padding: 10px; border-radius: 8px; border-left: 4px solid #EF4444;">
                        <div style="font-size: 0.9rem; color: #991B1B;">Rejetées (reproduction)</div>
                        <div style="font-size: 1.2rem; font-weight: 700; color: #991B1B;">{quantite_rejetee} paires</div>
                    </div>
                </div>
                <div style="margin-top: 10px; font-size: 0.9rem; color: #4B5563;">
                    Ces paires ont été re-travaillées en recoupe et doivent être re-contrôlées.
                    <b>Elles s'ajoutent aux {paires_restantes_originales} paires restantes de la production originale.</b>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        if total_a_controler > 0:
            st.markdown('<div class="section-header">▶️ Ajouter des Paires au Contrôle</div>',
                        unsafe_allow_html=True)

            if order['statut_coupe'] != 'Terminée':
                st.markdown('<div class="warning-card">'
                            '<h4>⚠️ Information</h4>'
                            'La coupe est encore en cours.<br>'
                            'Vous pouvez seulement ajouter un nombre limité de paires à contrôler.'
                            '</div>', unsafe_allow_html=True)
                max_ajout = min(total_a_controler, 100)
            else:
                max_ajout = total_a_controler

            # Afficher la répartition
            if paires_retour_recoupe > 0:
                st.markdown(f"""
                <div style="background: #F3F4F6; padding: 10px; border-radius: 8px; margin: 10px 0;">
                    <div style="font-weight: 600; margin-bottom: 5px;">📊 Répartition des paires à contrôler:</div>
                    <div>• 🆕 Production originale restante: <b>{paires_restantes_originales} paires</b></div>
                    <div>• 🔧 Retours de recoupe: <b>{paires_retour_recoupe} paires</b></div>
                    <div style="margin-top: 5px; font-weight: 700;">• 📈 Total disponible: <b>{total_a_controler} paires</b></div>
                </div>
                """, unsafe_allow_html=True)

            quantite_a_ajouter = st.number_input("Paires supplémentaires à contrôler",
                                                 min_value=1,
                                                 max_value=max_ajout,
                                                 value=min(max_ajout, 50),
                                                 step=1,
                                                 key=f"add_{order['of']}",
                                                 help=f"Inclut les {paires_retour_recoupe} paires issues de recoupe")

            col_continue1, col_continue2, col_continue3 = st.columns([1, 2, 1])
            with col_continue2:
                if st.button("▶️ Continuer le Contrôle", width='stretch', type="primary",
                             key=f"continue_{order['of']}"):
                    if self.db_manager.update_order(order['of'],
                                                    statut_controle='En cours',
                                                    date_debut_controle=datetime.now(),
                                                    quantite_a_controler=quantite_controlee + quantite_a_ajouter):
                        st.success(f"✅ Contrôle repris pour {quantite_a_ajouter} paires!")
                        time.sleep(1)
                        st.rerun()
        else:
            st.success("🎉 Toutes les paires (originales + recoupe) ont été contrôlées!")

            # Afficher le résumé final
            if paires_retour_recoupe > 0:
                st.markdown(f"""
                <div class="info-card">
                    <h4>📊 Synthèse complète</h4>
                    <div style="display: flex; gap: 15px; margin: 10px 0;">
                        <div style="flex: 1; text-align: center;">
                            <div style="font-size: 0.9rem; color: #6B7280;">Total production</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #1F2937;">{quantite_totale}</div>
                        </div>
                        <div style="flex: 1; text-align: center;">
                            <div style="font-size: 0.9rem; color: #6B7280;">Paires recoupe</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #F59E0B;">{paires_retour_recoupe}</div>
                        </div>
                        <div style="flex: 1; text-align: center;">
                            <div style="font-size: 0.9rem; color: #6B7280;">Total contrôlé</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #10B981;">{quantite_controlee}</div>
                        </div>
                    </div>
                    <div style="font-size: 0.9rem; color: #4B5563; margin-top: 10px;">
                        <b>Note:</b> Le pourcentage de contrôle est calculé sur {quantite_totale + paires_retour_recoupe} paires au total.
                    </div>
                </div>
                """, unsafe_allow_html=True)

    def _process_control_session(self, order: Dict, quantite_approuvee: int,
                                 quantite_rejetee: int, quantite_retravailler: int,
                                 observation: str, is_final: bool):
        """Traite l'enregistrement d'une session de contrôle avec gestion des retours"""
        try:
            nouvelle_quantite = (order.get('quantite_controlee', 0) or 0) + \
                                quantite_approuvee + quantite_rejetee + quantite_retravailler

            # Calculer les nouveaux totaux
            current_acceptee = order.get('quantite_acceptee', 0) or 0
            current_rejetee = order.get('quantite_rejetee', 0) or 0
            current_retravailler = order.get('quantite_retravailler', 0) or 0

            # ===== NOUVEAU: Gestion spéciale des retours de recoupe =====
            # Si ce sont des paires issues de recoupe, les traiter différemment
            total_acceptee = current_acceptee + quantite_approuvee
            total_rejetee = current_rejetee + quantite_rejetee
            total_retravailler = current_retravailler + quantite_retravailler

            # Calculer le total des paires à contrôler (production + retours)
            quantite_totale_production = order['quantite']
            total_retours = (order.get('quantite_retravailler', 0) or 0) + (order.get('quantite_rejetee', 0) or 0)
            total_a_controler = quantite_totale_production + total_retours

            # Mettre à jour la base
            update_data = {
                'quantite_controlee': nouvelle_quantite,
                'quantite_acceptee': total_acceptee,
                'quantite_rejetee': total_rejetee,
                'quantite_retravailler': total_retravailler,
                'observation_controle': observation
            }

            if is_final and order['statut_coupe'] == 'Terminée':
                if nouvelle_quantite >= total_a_controler:
                    if (total_rejetee + total_retravailler) > 0:
                        # Retour à la coupe - NOUVEAU: distinguer si ce sont des retours de recoupe
                        if total_retours > 0:
                            update_data['statut_controle'] = 'Contrôle complet avec retours 🔄'
                            st.warning(
                                f"⚠️ Contrôle complet terminé avec {total_rejetee + total_retravailler} paires à retravailler")
                        else:
                            update_data['statut_controle'] = 'À retravailler 🔧'
                            st.warning(f"⚠️ OF retourne à la coupe ({total_rejetee + total_retravailler} paires)")
                    else:
                        # Tout est accepté
                        if total_retours > 0:
                            update_data['statut_controle'] = 'Approuvé avec recoupe ✅'
                        else:
                            update_data['statut_controle'] = 'Approuvé ✅'
                        update_data['date_fin_controle'] = datetime.now()
                        st.success("✅ Contrôle COMPLET terminé avec SUCCÈS!")
                else:
                    update_data['statut_controle'] = 'Contrôle partiel'
                    st.info("ℹ️ Session enregistrée (contrôle partiel)")
            else:
                update_data['statut_controle'] = 'Contrôle partiel'
                st.success(f"✅ Session enregistrée: {nouvelle_quantite}/{total_a_controler} paires")

            # Appliquer les mises à jour
            if self.db_manager.update_order(order['of'], **update_data):
                time.sleep(1)
                st.rerun()

        except Exception as e:
            st.error(f"❌ Erreur: {e}")