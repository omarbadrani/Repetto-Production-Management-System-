# pages/sidebar_manager.py - Gestionnaire de la sidebar
import streamlit as st
from database import DatabaseManager
from typing import List, Dict


class SidebarManager:
    """Gestionnaire de la sidebar"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def display(self):
        """Affiche la sidebar"""
        with st.sidebar:
            st.markdown('<div class="sidebar-title">👠 Repetto</div>', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-subtitle">Gestion de Production</div>', unsafe_allow_html=True)

            st.markdown("---")

            # Info utilisateur
            st.markdown("### 👤 Utilisateur")
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 10px; border: 1px solid #E2E8F0;">
                <div style="color: #E75480; font-weight: bold;">{st.session_state.user_name}</div>
                <div style="font-size: 0.85rem; color: #6B7280;">{st.session_state.user_role}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 🔍 Filtres")

            # Récupérer les ordres pour les filtres
            orders = self.db_manager.get_all_orders()

            # Filtre par période
            period_options = ["Aujourd'hui", "Cette semaine", "Ce mois", "Trimestre", "Année"]
            if 'selected_period' not in st.session_state:
                st.session_state.selected_period = "Aujourd'hui"

            selected_period = st.selectbox(
                "📅 Période",
                period_options,
                index=period_options.index(st.session_state.selected_period),
                key="sidebar_period"
            )
            st.session_state.selected_period = selected_period

            # Filtre par statut
            status_options = ["Tous", "En cours", "Terminé", "En pause", "À problème"]
            if 'selected_status' not in st.session_state:
                st.session_state.selected_status = "Tous"

            selected_status = st.selectbox(
                "📈 Statut",
                status_options,
                index=status_options.index(st.session_state.selected_status),
                key="sidebar_status"
            )
            st.session_state.selected_status = selected_status

            # Filtre par modèle
            if orders:
                models = list(set([o['modele'] for o in orders]))
                models.sort()
                models.insert(0, "Tous les Modèles")
            else:
                models = ["Tous les Modèles"]

            if 'selected_model' not in st.session_state:
                st.session_state.selected_model = "Tous les Modèles"

            if st.session_state.selected_model not in models:
                st.session_state.selected_model = "Tous les Modèles"

            selected_model = st.selectbox(
                "👟 Modèle",
                models,
                index=models.index(st.session_state.selected_model),
                key="sidebar_model"
            )
            st.session_state.selected_model = selected_model

            st.markdown("---")

            # Statistiques rapides
            st.markdown("### 📊 Statistiques")
            if orders:
                # Filtrer les ordres selon les filtres
                filtered_orders = self._filter_orders(orders)

                total_paires = sum(o['quantite'] for o in filtered_orders)
                total_controlees = sum(o.get('quantite_controlee', 0) or 0 for o in filtered_orders)
                taux_controle = (total_controlees / total_paires * 100) if total_paires > 0 else 0

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📊 OF", len(filtered_orders))
                with col2:
                    st.metric("✅ Contrôle", f"{taux_controle:.1f}%")

                # Statuts de coupe
                en_cours = len([o for o in filtered_orders if o['statut_coupe'] == 'En cours'])
                termines = len([o for o in filtered_orders if o['statut_coupe'] == 'Terminée'])
                en_pause = len([o for o in filtered_orders if o.get('coupe_en_pause')])

                st.markdown(f"""
                <div style="background: white; padding: 0.8rem; border-radius: 8px; margin-top: 0.5rem; font-size: 0.85rem;">
                    <div style="margin-bottom: 5px;">🔄 En cours: <b>{en_cours}</b></div>
                    <div style="margin-bottom: 5px;">✅ Terminés: <b>{termines}</b></div>
                    <div>⏸️ En pause: <b>{en_pause}</b></div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Actions rapides
            st.markdown("### ⚡ Actions")

            if st.button("📤 Exporter", use_container_width=True, key="export_sidebar"):
                st.info("💾 Fonction d'export disponible prochainement")

            if st.button("🔄 Actualiser", use_container_width=True, key="refresh_sidebar"):
                st.rerun()

            st.markdown("---")

            # Bouton déconnexion
            if st.button("🚪 Déconnexion", use_container_width=True, type="primary", key="logout_sidebar_btn"):
                st.session_state.logged_in = False
                st.session_state.user_role = None
                st.session_state.user_name = None
                st.rerun()

            # Footer
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; font-size: 0.75rem; color: #9CA3AF; margin-top: 20px;">
                <div>👠 <b>Repetto</b></div>
                <div style="margin-top: 5px;">v1.0 © 2024</div>
            </div>
            """, unsafe_allow_html=True)

    def _filter_orders(self, orders: List[Dict]) -> List[Dict]:
        """Filtre les ordres selon les critères de la sidebar"""
        filtered = orders.copy()

        # Filtre par statut
        if st.session_state.selected_status != "Tous":
            if st.session_state.selected_status == "En cours":
                filtered = [o for o in filtered if o['statut_coupe'] == 'En cours']
            elif st.session_state.selected_status == "Terminé":
                filtered = [o for o in filtered if o['statut_coupe'] == 'Terminée']
            elif st.session_state.selected_status == "En pause":
                filtered = [o for o in filtered if o.get('coupe_en_pause') or o.get('controle_en_pause')]
            elif st.session_state.selected_status == "À problème":
                filtered = [o for o in filtered if
                            (o.get('quantite_rejetee', 0) or 0) + (o.get('quantite_retravailler', 0) or 0) > 0]

        # Filtre par modèle
        if st.session_state.selected_model != "Tous les Modèles":
            filtered = [o for o in filtered if o['modele'] == st.session_state.selected_model]

        return filtered