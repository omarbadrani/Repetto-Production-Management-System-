# pages/login_page.py - Page de connexion
import streamlit as st
import time
from datetime import datetime
from database import DatabaseManager


class LoginPage:
    """Page de connexion"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def render(self):
        """Affiche la page de connexion"""
        col1, col2, col3 = st.columns([1, 4, 1])

        with col2:
            st.markdown('<div class="main-header">🔐 Connexion Repetto</div>', unsafe_allow_html=True)
            st.markdown('<div class="sub-header">Système de Gestion de Production</div>', unsafe_allow_html=True)

            with st.container():
                st.markdown('<div class="info-card">', unsafe_allow_html=True)

                with st.form("login_form"):
                    col_input1, col_input2 = st.columns(2)

                    with col_input1:
                        username = st.text_input("👤 Nom d'utilisateur", placeholder="Entrez votre identifiant",
                                                 key="username_input")

                    with col_input2:
                        password = st.text_input("🔒 Mot de passe", type="password", placeholder="••••••••",
                                                 key="password_input")

                    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                    with col_btn2:
                        submit = st.form_submit_button("🚀 Se connecter", width='stretch', type="primary")

                    if submit:
                        if not username or not password:
                            st.error("❌ Veuillez saisir votre nom d'utilisateur et mot de passe")
                        else:
                            with st.spinner("🔍 Vérification des identifiants..."):
                                user = self.db_manager.verify_user(username, password)
                                if user:
                                    st.session_state.logged_in = True
                                    st.session_state.user_role = user['role']
                                    st.session_state.user_name = user['name']
                                    st.session_state.last_activity = datetime.now()
                                    st.success("✅ Connexion réussie!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Identifiants incorrects!")

                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")

#           with st.expander("🔍 Comptes de test disponibles", expanded=True):
            #               col_acc1, col_acc2, col_acc3 = st.columns(3)

            #   with col_acc1:
            #       st.markdown("""
            ##v       <div style="background: white; padding: 1rem; border-radius: 10px; border: 1px solid #E2E8F0;">
              #          <div style="color: #E75480; font-weight: bold; margin-bottom: 5px;">👨‍🔧 Chef de Coupe</div>
        #           <div style="font-family: monospace; font-size: 0.9rem;">User: chef_coupe</div>
            #       <div style="font-family: monospace; font-size: 0.9rem;">Pass: coupe123</div>
                 #   </div>
            #     """, unsafe_allow_html=True)

            #   with col_acc2:
            #       st.markdown("""
            #       <div style="background: white; padding: 1rem; border-radius: 10px; border: 1px solid #E2E8F0;">
            #           <div style="color: #E75480; font-weight: bold; margin-bottom: 5px;">👌 Contrôle Qualité</div>
            #           <div style="font-family: monospace; font-size: 0.9rem;">User: controle</div>
            #           <div style="font-family: monospace; font-size: 0.9rem;">Pass: controle123</div>
            #       </div>
            #       """, unsafe_allow_html=True)
            #
            ####   with col_acc3:
            #    st.markdown("""
            #       <div style="background: white; padding: 1rem; border-radius: 10px; border: 1px solid #E2E8F0;">
            #           <div style="color: #E75480; font-weight: bold; margin-bottom: 5px;">📈 Directeur</div>
            ####           <div style="font-family: monospace; font-size: 0.9rem;">User: chef_prod</div>
            ##        <div style="font-family: monospace; font-size: 0.9rem;">Pass: prod123</div>
            #      </div>
    #       """, unsafe_allow_html=True)