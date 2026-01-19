# database.py - Classes liées à la base de données
from datetime import datetime, timedelta
import hashlib
from typing import Optional, List, Dict, Any
import pymysql
from pymysql.cursors import DictCursor
import streamlit as st

class Config:
    """Configuration de l'application"""
    PAGE_CONFIG = {
        'page_title': "Repetto - Gestion Production",
        'layout': "wide",
        'page_icon': "👠",
        'initial_sidebar_state': "expanded",
        'menu_items': {
            'Get Help': 'https://www.repetto.com',
            'Report a bug': None,
            'About': "Système de Gestion de Production Repetto v1.0"
        }
    }

    DB_CONFIG = {
        'host': '192.168.1.210',
        'user': 'omar',
        'password': '1234',
        'port': 3306,
        'charset': 'utf8mb4',
        'cursorclass': DictCursor
    }

    DATABASE_NAME = 'usine_chaussures'

    @staticmethod
    def init_session_state():
        """Initialise l'état de la session"""
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.user_name = None
            st.session_state.db_initialized = False
            st.session_state.last_activity = None
            st.session_state.selected_period = "Aujourd'hui"
            st.session_state.selected_status = "Tous"
            st.session_state.selected_model = "Tous les Modèles"


class DatabaseManager:

    """Gestionnaire de base de données"""
    def __init__(self):
        self.config = Config.DB_CONFIG.copy()
        self.database_name = Config.DATABASE_NAME

    def create_database_if_not_exists(self) -> bool:
        """Crée la base de données si elle n'existe pas"""
        try:
            conn = pymysql.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password'],
                port=self.config['port'],
                charset=self.config['charset']
            )

            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database_name}")
                cursor.execute(f"USE {self.database_name}")

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur création base: {e}")
            return False

    def get_connection(self):
        """Crée une connexion à la base de données MySQL"""
        try:
            config_with_db = self.config.copy()
            config_with_db['database'] = self.database_name
            conn = pymysql.connect(**config_with_db)
            return conn
        except pymysql.err.OperationalError as e:
            import streamlit as st
            if "Unknown database" in str(e):
                if self.create_database_if_not_exists():
                    try:
                        config_with_db = self.config.copy()
                        config_with_db['database'] = self.database_name
                        conn = pymysql.connect(**config_with_db)
                        return conn
                    except Exception as e2:
                        st.error(f"❌ Erreur après création: {e2}")
                        return None
            else:
                st.error(f"❌ Erreur connexion: {e}")
                return None
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur inattendue: {e}")
            return None

    def hash_password(self, password: str) -> str:
        """Hash un mot de passe avec SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        """Vérifie les identifiants de l'utilisateur"""
        conn = self.get_connection()
        if conn is None:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()

                if user:
                    if user['password'] == password:
                        cursor.execute("UPDATE users SET password = %s WHERE username = %s",
                                       (self.hash_password(password), username))
                        conn.commit()
                        return user
                    elif user['password'] == self.hash_password(password):
                        return user

            return None
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur authentification: {e}")
            return None
        finally:
            conn.close()

    def init_database(self) -> bool:
        """Initialise les tables MySQL avec une structure logique"""
        if not self.create_database_if_not_exists():
            return False

        conn = self.get_connection()
        if conn is None:
            return False

        try:
            with conn.cursor() as cursor:
                # ===== TABLE 1: UTILISATEURS =====
                cursor.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            username VARCHAR(50) UNIQUE NOT NULL,
                            password VARCHAR(100) NOT NULL,
                            role VARCHAR(50) NOT NULL,
                            name VARCHAR(100) NOT NULL,
                            active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')

                # ===== TABLE 2: ORDRES DE FABRICATION (Header) =====
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS ordres_fabrication
                               (
                                   id
                                   INT
                                   PRIMARY
                                   KEY
                                   AUTO_INCREMENT,
                                   of
                                   VARCHAR
                               (
                                   50
                               ) UNIQUE NOT NULL,
                                   modele VARCHAR
                               (
                                   100
                               ) NOT NULL,
                                   code_modele VARCHAR
                               (
                                   50
                               ),
                                   couleur_modele VARCHAR
                               (
                                   50
                               ) NOT NULL,
                                   quantite INT NOT NULL,
                                   observation TEXT,
                                   date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
                                   date_fin_prevue DATETIME,
                                   statut VARCHAR
                               (
                                   50
                               ) DEFAULT 'En attente',
                                   derniere_mise_a_jour TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                                   )
                               ''')
                # ===== TABLE 3: DETAILS DE COUPE =====
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS details_coupe (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        of_id VARCHAR(50) NOT NULL,
                        coloris VARCHAR(50) NOT NULL,
                        matiere VARCHAR(50) NOT NULL,
                        matricule_coupeur VARCHAR(50) NOT NULL,
                        consommation DECIMAL(10,2) DEFAULT 0,
                        sur_consommation DECIMAL(10,2) DEFAULT 0,
                        observation TEXT,
                        statut_coupe VARCHAR(50) DEFAULT 'En attente',
                        date_debut_coupe DATETIME,
                        date_fin_coupe DATETIME,
                        temps_coupe INT DEFAULT 0,

                        # ===== NOUVELLES COLONNES POUR RECOUPE =====
                        temps_recoupe INT DEFAULT 0,
                        date_debut_recoupe DATETIME,
                        nombre_recoupe INT DEFAULT 0,

                        coupe_en_pause BOOLEAN DEFAULT FALSE,
                        temps_coupe_avant_pause INT DEFAULT 0,
                        date_derniere_pause DATETIME,
                        duree_totale_pause INT DEFAULT 0,

                        # ===== NOUVELLE COLONNE POUR SUIVI TEMPS =====
                        date_derniere_maj_coupe DATETIME DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (of_id) REFERENCES ordres_fabrication(of) ON DELETE CASCADE,
                        UNIQUE KEY unique_of_coupe (of_id),
                        derniere_mise_a_jour TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                ''')
                # ===== TABLE 4: DETAILS DE CONTROLE =====
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS details_controle (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        of_id VARCHAR(50) NOT NULL,
                        statut_controle VARCHAR(50) DEFAULT 'En attente',
                        date_debut_controle DATETIME,
                        date_fin_controle DATETIME,

                        # ===== DEUX CHRONOMÈTRES INDÉPENDANTS =====
                        temps_actif_total INT DEFAULT 0,          # Chrono 1: Temps actif de production (s'arrête en pause)
                        temps_pause_total INT DEFAULT 0,          # Chrono 2: Temps de pause (s'incrémente seulement en pause)

                        # Pour maintenir la compatibilité temporairement
                        temps_controle INT DEFAULT 0,             # Ancien temps total (déprécié)

                        # Informations de contrôle
                        quantite_a_controler INT DEFAULT 0,
                        quantite_controlee INT DEFAULT 0,
                        quantite_acceptee INT DEFAULT 0,
                        quantite_rejetee INT DEFAULT 0,
                        quantite_retravailler INT DEFAULT 0,
                        observation_controle TEXT,

                        # État du contrôle
                        controle_en_pause BOOLEAN DEFAULT FALSE,
                        date_derniere_maj DATETIME DEFAULT CURRENT_TIMESTAMP,  # Pour calculer l'intervalle

                        # Anciennes colonnes pour compatibilité
                        temps_controle_avant_pause INT DEFAULT 0,
                        duree_pause_controle INT DEFAULT 0,
                        date_derniere_pause DATETIME,

                        FOREIGN KEY (of_id) REFERENCES ordres_fabrication(of) ON DELETE CASCADE,
                        UNIQUE KEY unique_of_controle (of_id),
                        derniere_mise_a_jour TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS details_piqure
                               (
                                   id
                                   INT
                                   PRIMARY
                                   KEY
                                   AUTO_INCREMENT,
                                   of_id
                                   VARCHAR
                               (
                                   50
                               ) NOT NULL,
                                   matricule_piqueur VARCHAR
                               (
                                   50
                               ) NOT NULL,
                                   observation_piqure TEXT,
                                   statut_piqure VARCHAR
                               (
                                   50
                               ) DEFAULT 'En attente',
                                   date_debut_piqure DATETIME,
                                   date_fin_piqure DATETIME,
                                   temps_piqure INT DEFAULT 0,

                                   piqure_en_pause BOOLEAN DEFAULT FALSE,
                                   temps_piqure_avant_pause INT DEFAULT 0,
                                   date_derniere_pause_piqure DATETIME,
                                   duree_totale_pause_piqure INT DEFAULT 0,

                                   date_derniere_maj_piqure DATETIME DEFAULT CURRENT_TIMESTAMP,
                                   FOREIGN KEY
                               (
                                   of_id
                               ) REFERENCES ordres_fabrication
                               (
                                   of
                               ) ON DELETE CASCADE,
                                   UNIQUE KEY unique_of_piqure
                               (
                                   of_id
                               ),
                                   derniere_mise_a_jour TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP
                                   )
                               ''')
                # ===== TABLE 5: HISTORIQUE DES CHANGEMENTS =====
                cursor.execute('''
                        CREATE TABLE IF NOT EXISTS historique_changements (
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            of_id VARCHAR(50) NOT NULL,
                            type_operation VARCHAR(50) NOT NULL,
                            ancien_statut VARCHAR(50),
                            nouveau_statut VARCHAR(50),
                            description TEXT,
                            utilisateur_id INT,
                            date_changement DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (of_id) REFERENCES ordres_fabrication(of) ON DELETE CASCADE,
                            FOREIGN KEY (utilisateur_id) REFERENCES users(id) ON DELETE SET NULL,
                            INDEX idx_of_date (of_id, date_changement)
                        )
                    ''')

                # ===== TABLE 6: SESSIONS PAUSE =====
                cursor.execute('''
                        CREATE TABLE IF NOT EXISTS sessions_pause (
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            of_id VARCHAR(50) NOT NULL,
                            type_pause VARCHAR(50) NOT NULL,
                            date_debut DATETIME DEFAULT CURRENT_TIMESTAMP,
                            date_fin DATETIME,
                            duree_secondes INT,
                            raison TEXT,
                            FOREIGN KEY (of_id) REFERENCES ordres_fabrication(of) ON DELETE CASCADE,
                            INDEX idx_of_type (of_id, type_pause)
                        )
                    ''')

                # ===== TABLE 7: QUALITE DETAILS PAR SESSION =====
                cursor.execute('''
                        CREATE TABLE IF NOT EXISTS qualite_sessions (
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            of_id VARCHAR(50) NOT NULL,
                            num_session INT DEFAULT 1,
                            quantite_controle INT DEFAULT 0,
                            quantite_acceptee INT DEFAULT 0,
                            quantite_rejetee INT DEFAULT 0,
                            quantite_retravailler INT DEFAULT 0,
                            observation TEXT,
                            date_session DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (of_id) REFERENCES ordres_fabrication(of) ON DELETE CASCADE,
                            INDEX idx_of_session (of_id, num_session)
                        )
                    ''')

                # ===== INSÉRER LES UTILISATEURS PAR DÉFAUT =====
                cursor.execute("SELECT COUNT(*) FROM users")
                if cursor.fetchone()['COUNT(*)'] == 0:
                    default_users = [
                        ('chef_coupe', 'coupe123', 'Chef de Coupe', 'coupe_repetto'),
                        ('controle', 'controle123', 'Contrôle Qualité', 'controle_repetto'),
                        ('chef_prod', 'prod123', 'Chef de Production', 'groupe_repetto'),
                        ('chef_piqure', 'piqure123', 'Chef de Piqûre', 'piqure_repetto')  # ← NOUVEAU
                    ]
                    for user in default_users:
                        try:
                            cursor.execute(
                                "INSERT INTO users (username, password, role, name) VALUES (%s, %s, %s, %s)",
                                (user[0], self.hash_password(user[1]), user[2], user[3])
                            )
                        except pymysql.err.IntegrityError:
                            pass

            conn.commit()
            print("✅ Base de données initialisée avec succès!")
            return True
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur initialisation: {e}")
            return False
        finally:
            conn.close()

    def get_all_orders(self) -> List[Dict]:
        """Récupère tous les ordres avec les données de piqûre"""
        conn = self.get_connection()
        if conn is None:
            return []

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                               SELECT o.id,
                                      o.of,
                                      o.modele,
                                      o.couleur_modele,
                                      o.quantite,
                                      o.observation            as observation_of,
                                      o.date_creation,
                                      o.statut                 as statut_global,

                                      c.coloris,
                                      c.matiere,
                                      c.matricule_coupeur,
                                      c.consommation,
                                      c.sur_consommation,
                                      c.observation            as observation_coupe,
                                      c.statut_coupe,
                                      c.date_debut_coupe,
                                      c.date_fin_coupe,
                                      c.temps_coupe,
                                      c.temps_recoupe,
                                      c.date_debut_recoupe,
                                      c.nombre_recoupe,
                                      c.coupe_en_pause,
                                      c.temps_coupe_avant_pause,
                                      c.date_derniere_pause    as date_pause_coupe,
                                      c.duree_totale_pause,

                                      ctrl.statut_controle,
                                      ctrl.date_debut_controle,
                                      ctrl.date_fin_controle,
                                      ctrl.temps_actif_total,
                                      ctrl.temps_pause_total,
                                      ctrl.controle_en_pause,
                                      ctrl.date_derniere_maj,
                                      ctrl.temps_controle,
                                      ctrl.quantite_a_controler,
                                      ctrl.quantite_controlee,
                                      ctrl.quantite_acceptee,
                                      ctrl.quantite_rejetee,
                                      ctrl.quantite_retravailler,
                                      ctrl.observation_controle,
                                      ctrl.temps_controle_avant_pause,
                                      ctrl.duree_pause_controle,
                                      ctrl.date_derniere_pause as date_pause_controle,

                                      -- ===== NOUVELLES COLONNES PIQÛRE =====
                                      p.statut_piqure,
                                      p.matricule_piqueur,
                                      p.date_debut_piqure,
                                      p.date_fin_piqure,
                                      p.temps_piqure,
                                      p.piqure_en_pause,
                                      p.temps_piqure_avant_pause,
                                      p.date_derniere_pause_piqure,
                                      p.duree_totale_pause_piqure,
                                      p.observation_piqure,
                                      p.date_derniere_maj_piqure

                               FROM ordres_fabrication o
                                        LEFT JOIN details_coupe c ON o.of = c.of_id
                                        LEFT JOIN details_controle ctrl ON o.of = ctrl.of_id
                                        LEFT JOIN details_piqure p ON o.of = p.of_id
                               ORDER BY o.date_creation DESC
                               ''')

                orders = cursor.fetchall()
            return orders if orders else []
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur lecture ordres: {e}")
            return []
        finally:
            conn.close()

    def get_order_by_of(self, of: str) -> Optional[Dict]:
        """Récupère un ordre spécifique avec TOUTES ses données"""
        conn = self.get_connection()
        if conn is None:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT 
                        o.id,
                        o.of,
                        o.modele,
                        o.couleur_modele,
                        o.quantite,
                        o.observation as observation_of,
                        o.date_creation,
                        o.statut as statut_global,

                        c.coloris,
                        c.matiere,
                        c.matricule_coupeur,
                        c.consommation,
                        c.sur_consommation,
                        c.observation as observation_coupe,
                        c.statut_coupe,
                        c.date_debut_coupe,
                        c.date_fin_coupe,
                        c.temps_coupe,
                        c.temps_recoupe,
                        c.date_debut_recoupe,
                        c.nombre_recoupe,
                        c.coupe_en_pause,
                        c.temps_coupe_avant_pause,
                        c.date_derniere_pause as date_pause_coupe,
                        c.duree_totale_pause,

                        # ===== NOUVELLES COLONNES DEUX CHRONOMÈTRES =====
                        ctrl.statut_controle,
                        ctrl.date_debut_controle,
                        ctrl.date_fin_controle,
                        ctrl.temps_actif_total,
                        ctrl.temps_pause_total,
                        ctrl.controle_en_pause,
                        ctrl.date_derniere_maj,

                        # Anciennes colonnes pour compatibilité
                        ctrl.temps_controle,
                        ctrl.quantite_a_controler,
                        ctrl.quantite_controlee,
                        ctrl.quantite_acceptee,
                        ctrl.quantite_rejetee,
                        ctrl.quantite_retravailler,
                        ctrl.observation_controle,
                        ctrl.temps_controle_avant_pause,
                        ctrl.duree_pause_controle,
                        ctrl.date_derniere_pause as date_pause_controle

                    FROM ordres_fabrication o
                    LEFT JOIN details_coupe c ON o.of = c.of_id
                    LEFT JOIN details_controle ctrl ON o.of = ctrl.of_id
                    WHERE o.of = %s
                ''', (of,))

                order = cursor.fetchone()
            return order
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur: {e}")
            return None
        finally:
            conn.close()

    def create_order(self, **kwargs) -> bool:
        """Crée un nouvel ordre avec ses détails de coupe"""
        conn = self.get_connection()
        if conn is None:
            return False

        try:
            with conn.cursor() as cursor:
                # Insérer dans ordres_fabrication avec code_modele
                cursor.execute('''
                               INSERT INTO ordres_fabrication
                                   (of, modele, code_modele, couleur_modele, quantite, observation)
                               VALUES (%s, %s, %s, %s, %s, %s)
                               ''', (
                                   kwargs.get('of'),
                                   kwargs.get('modele'),
                                   kwargs.get('code_modele', ''),  # Récupérer code_modele
                                   kwargs.get('couleur_modele'),
                                   kwargs.get('quantite'),
                                   kwargs.get('observation', '')
                               ))

                # Insérer dans details_coupe avec date_debut_coupe = NULL au départ
                cursor.execute('''
                               INSERT INTO details_coupe
                               (of_id, coloris, matiere, matricule_coupeur, consommation,
                                sur_consommation, observation, date_debut_coupe, temps_coupe,
                                temps_recoupe, nombre_recoupe)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, 0, 0, 0)
                               ''', (kwargs.get('of'), kwargs.get('coloris'), kwargs.get('matiere'),
                                     kwargs.get('matricule_coupeur'), kwargs.get('consommation'),
                                     kwargs.get('sur_consommation'), kwargs.get('observation', '')))

                # Insérer dans details_controle (vide au départ)
                cursor.execute('''
                               INSERT INTO details_controle
                                   (of_id, statut_controle, date_debut_controle, temps_controle)
                               VALUES (%s, 'En attente', NULL, 0)
                               ''', (kwargs.get('of'),))

            conn.commit()
            return True
        except pymysql.err.IntegrityError:
            import streamlit as st
            st.error(f"❌ L'OF {kwargs.get('of')} existe déjà !")
            return False
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur création: {e}")
            return False
        finally:
            conn.close()

    def update_order(self, of: str, **kwargs) -> bool:
        """Met à jour un ordre (distribue les colonnes aux bonnes tables)"""
        conn = self.get_connection()
        if conn is None:
            return False

        try:
            with conn.cursor() as cursor:
                # Colonnes de ordres_fabrication
                ordres_columns = ['observation', 'statut']
                ordres_updates = {k: v for k, v in kwargs.items() if k in ordres_columns}

                # Colonnes de details_coupe
                coupe_columns = [
                    'coloris', 'matiere', 'matricule_coupeur', 'consommation', 'sur_consommation',
                    'observation_coupe', 'statut_coupe', 'date_debut_coupe', 'date_fin_coupe',
                    'temps_coupe', 'temps_recoupe', 'date_debut_recoupe', 'nombre_recoupe',
                    'coupe_en_pause', 'temps_coupe_avant_pause',
                    'date_derniere_pause', 'duree_totale_pause', 'date_derniere_maj_coupe'
                ]
                coupe_updates = {k: v for k, v in kwargs.items() if k in coupe_columns}

                # Colonnes de details_controle
                controle_columns = [
                    'statut_controle', 'date_debut_controle', 'date_fin_controle',
                    'temps_controle', 'quantite_a_controler', 'quantite_controlee',
                    'quantite_acceptee', 'quantite_rejetee', 'quantite_retravailler',
                    'observation_controle', 'controle_en_pause', 'temps_controle_avant_pause',
                    'duree_pause_controle'
                ]
                controle_updates = {k: v for k, v in kwargs.items() if k in controle_columns}

                # ===== NOUVELLES COLONNES DE PIQÛRE =====
                piqure_columns = [
                    'statut_piqure', 'matricule_piqueur', 'date_debut_piqure', 'date_fin_piqure',
                    'temps_piqure', 'piqure_en_pause', 'temps_piqure_avant_pause',
                    'date_derniere_pause_piqure', 'duree_totale_pause_piqure',
                    'observation_piqure', 'date_derniere_maj_piqure'
                ]
                piqure_updates = {k: v for k, v in kwargs.items() if k in piqure_columns}

                # Mettre à jour ordres_fabrication
                if ordres_updates:
                    set_clause = ", ".join([f"{key} = %s" for key in ordres_updates.keys()])
                    values = list(ordres_updates.values()) + [of]
                    cursor.execute(f"UPDATE ordres_fabrication SET {set_clause} WHERE of = %s", values)

                # Mettre à jour details_coupe
                if coupe_updates:
                    set_clause = ", ".join([f"{key} = %s" for key in coupe_updates.keys()])
                    values = list(coupe_updates.values()) + [of]
                    cursor.execute(f"UPDATE details_coupe SET {set_clause} WHERE of_id = %s", values)

                # Mettre à jour details_controle
                if controle_updates:
                    set_clause = ", ".join([f"{key} = %s" for key in controle_updates.keys()])
                    values = list(controle_updates.values()) + [of]
                    cursor.execute(f"UPDATE details_controle SET {set_clause} WHERE of_id = %s", values)

                # ===== METTRE À JOUR details_piqure =====
                if piqure_updates:
                    set_clause = ", ".join([f"{key} = %s" for key in piqure_updates.keys()])
                    values = list(piqure_updates.values()) + [of]
                    cursor.execute(f"UPDATE details_piqure SET {set_clause} WHERE of_id = %s", values)

            conn.commit()
            return True
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur mise à jour: {e}")
            return False
        finally:
            conn.close()

    def update_all_timers(self):
        """Met à jour les DEUX chronomètres indépendants"""
        conn = self.get_connection()
        if conn is None:
            return

        try:
            with conn.cursor() as cursor:
                # ===== 1. CHRONOMÈTRES DE COUPE =====
                cursor.execute('''
                               SELECT of_id,
                                      coupe_en_pause,
                                      date_derniere_maj_coupe,
                                      temps_coupe,
                                      duree_totale_pause
                               FROM details_coupe
                               WHERE statut_coupe = 'En cours'
                                 AND date_derniere_maj_coupe IS NOT NULL
                               ''')
                coupes = cursor.fetchall()

                updated_coupe_count = 0
                for coupe in coupes:
                    of_id = coupe['of_id']
                    is_paused = coupe['coupe_en_pause']
                    last_update = coupe['date_derniere_maj_coupe']

                    # Calculer le temps écoulé depuis la dernière mise à jour
                    cursor.execute('SELECT TIMESTAMPDIFF(SECOND, %s, NOW()) as ecoule', (last_update,))
                    time_elapsed = cursor.fetchone()['ecoule']

                    if time_elapsed > 0:
                        if is_paused:
                            # EN PAUSE : ajouter au chrono pause coupe
                            new_pause = (coupe['duree_totale_pause'] or 0) + time_elapsed
                            cursor.execute('''
                                           UPDATE details_coupe
                                           SET duree_totale_pause      = %s,
                                               date_derniere_maj_coupe = NOW()
                                           WHERE of_id = %s
                                           ''', (new_pause, of_id))
                            print(f"  ⏸️ COUPE OF {of_id}: +{time_elapsed}s au chrono PAUSE → {new_pause}s")
                        else:
                            # ACTIF : ajouter au chrono coupe
                            new_coupe = (coupe['temps_coupe'] or 0) + time_elapsed
                            cursor.execute('''
                                           UPDATE details_coupe
                                           SET temps_coupe             = %s,
                                               date_derniere_maj_coupe = NOW()
                                           WHERE of_id = %s
                                           ''', (new_coupe, of_id))
                            print(f"  ✂️ COUPE OF {of_id}: +{time_elapsed}s au chrono ACTIF → {new_coupe}s")

                        updated_coupe_count += 1

                # ===== 2. CHRONOMÈTRES DE CONTRÔLE =====
                cursor.execute('''
                               SELECT of_id,
                                      controle_en_pause,
                                      date_derniere_maj,
                                      temps_actif_total,
                                      temps_pause_total
                               FROM details_controle
                               WHERE statut_controle = 'En cours'
                                 AND date_derniere_maj IS NOT NULL
                               ''')

                controles = cursor.fetchall()

                updated_controle_count = 0
                for ctrl in controles:
                    of_id = ctrl['of_id']
                    is_paused = ctrl['controle_en_pause']
                    last_update = ctrl['date_derniere_maj']

                    # Calculer le temps écoulé depuis la dernière mise à jour
                    cursor.execute('SELECT TIMESTAMPDIFF(SECOND, %s, NOW()) as ecoule', (last_update,))
                    time_elapsed = cursor.fetchone()['ecoule']

                    if time_elapsed > 0:
                        if is_paused:
                            # EN PAUSE : ajouter au chrono pause
                            new_pause = (ctrl['temps_pause_total'] or 0) + time_elapsed
                            cursor.execute('''
                                           UPDATE details_controle
                                           SET temps_pause_total = %s,
                                               date_derniere_maj = NOW()
                                           WHERE of_id = %s
                                           ''', (new_pause, of_id))
                            print(f"  ⏸️ CONTRÔLE OF {of_id}: +{time_elapsed}s au chrono PAUSE → {new_pause}s")
                        else:
                            # ACTIF : ajouter au chrono actif
                            new_actif = (ctrl['temps_actif_total'] or 0) + time_elapsed
                            cursor.execute('''
                                           UPDATE details_controle
                                           SET temps_actif_total = %s,
                                               date_derniere_maj = NOW()
                                           WHERE of_id = %s
                                           ''', (new_actif, of_id))
                            print(f"  🔄 CONTRÔLE OF {of_id}: +{time_elapsed}s au chrono ACTIF → {new_actif}s")

                        updated_controle_count += 1

                # ===== 3. CHRONOMÈTRES DE PIQÛRE =====
                cursor.execute('''
                               SELECT of_id,
                                      piqure_en_pause,
                                      date_derniere_maj_piqure,
                                      temps_piqure,
                                      duree_totale_pause_piqure
                               FROM details_piqure
                               WHERE statut_piqure = 'En cours'
                                 AND date_derniere_maj_piqure IS NOT NULL
                               ''')
                piqures = cursor.fetchall()

                for piqure in piqures:
                    of_id = piqure['of_id']
                    is_paused = piqure['piqure_en_pause']
                    last_update = piqure['date_derniere_maj_piqure']

                    # Calculer le temps écoulé depuis la dernière mise à jour
                    cursor.execute('SELECT TIMESTAMPDIFF(SECOND, %s, NOW()) as ecoule', (last_update,))
                    time_elapsed = cursor.fetchone()['ecoule']

                    if time_elapsed > 0:
                        if is_paused:
                            # EN PAUSE : ajouter au chrono pause piqûre
                            new_pause = (piqure['duree_totale_pause_piqure'] or 0) + time_elapsed
                            cursor.execute('''
                                           UPDATE details_piqure
                                           SET duree_totale_pause_piqure = %s,
                                               date_derniere_maj_piqure  = NOW()
                                           WHERE of_id = %s
                                           ''', (new_pause, of_id))
                            print(f"  ⏸️ PIQÛRE OF {of_id}: +{time_elapsed}s au chrono PAUSE → {new_pause}s")
                        else:
                            # ACTIF : ajouter au chrono piqûre
                            new_piqure = (piqure['temps_piqure'] or 0) + time_elapsed
                            cursor.execute('''
                                           UPDATE details_piqure
                                           SET temps_piqure             = %s,
                                               date_derniere_maj_piqure = NOW()
                                           WHERE of_id = %s
                                           ''', (new_piqure, of_id))
                            print(f"  🪡 PIQÛRE OF {of_id}: +{time_elapsed}s au chrono ACTIF → {new_piqure}s")

                conn.commit()
        except Exception as e:
            print(f"❌ Erreur chronomètres doubles: {e}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()

    def debug_chronometre_controle(self, of_number: str = None):
        """Fonction de debug pour le chronomètre de contrôle"""
        conn = self.get_connection()
        if conn is None:
            return

        try:
            with conn.cursor() as cursor:
                if of_number:
                    query = '''
                        SELECT * FROM details_controle 
                        WHERE of_id = %s
                    '''
                    cursor.execute(query, (of_number,))
                else:
                    query = '''
                        SELECT * FROM details_controle 
                        WHERE statut_controle = 'En cours'
                    '''
                    cursor.execute(query)

                controles = cursor.fetchall()

                print(f"\n{'=' * 70}")
                print(f"🐛 DEBUG DÉTAILLÉ CHRONOMÈTRE CONTRÔLE")
                print(f"{'=' * 70}")

                for ctrl in controles:
                    print(f"\n📋 OF: {ctrl['of_id']}")
                    print(f"   Statut: {ctrl['statut_controle']}")
                    print(f"   En pause: {ctrl.get('controle_en_pause', 0)}")
                    print(f"   Temps contrôle: {ctrl['temps_controle']}s")
                    print(f"   Temps avant pause: {ctrl.get('temps_controle_avant_pause', 0)}s")
                    print(f"   Durée pause: {ctrl.get('duree_pause_controle', 0)}s")
                    print(f"   Date début: {ctrl.get('date_debut_controle')}")
                    print(f"   Date dernière pause: {ctrl.get('date_derniere_pause')}")

                    # Calcul manuel
                    if ctrl['date_debut_controle']:
                        cursor.execute('SELECT TIMESTAMPDIFF(SECOND, %s, NOW()) as total_seconds',
                                       (ctrl['date_debut_controle'],))
                        total = cursor.fetchone()['total_seconds']
                        pause_totale = ctrl.get('duree_pause_controle', 0)
                        temps_actif = total - pause_totale

                        print(f"\n   🔧 CALCULS MANUELS:")
                        print(f"      Total depuis début: {total}s ({total / 3600:.2f}h)")
                        print(f"      Pause totale: {pause_totale}s")
                        print(f"      Temps actif calculé: {temps_actif}s")
                        print(f"      Différence avec DB: {temps_actif - ctrl['temps_controle']}s")

                print(f"\n{'=' * 70}")
                print(f"Fin debug - {len(controles)} contrôles analysés")
                print(f"{'=' * 70}\n")

        except Exception as e:
            print(f"❌ Erreur debug: {e}")
        finally:
            conn.close()

    def toggle_controle_pause(self, of_number: str, mettre_en_pause: bool) -> bool:
        """Active/désactive la pause pour le contrôle"""
        conn = self.get_connection()
        if conn is None:
            return False

        try:
            with conn.cursor() as cursor:
                # D'abord, mettre à jour les chronomètres avant de changer l'état
                cursor.execute('''
                    SELECT controle_en_pause, date_derniere_maj, 
                           temps_actif_total, temps_pause_total
                    FROM details_controle 
                    WHERE of_id = %s
                ''', (of_number,))

                current_state = cursor.fetchone()
                if not current_state:
                    return False

                # Mettre à jour les chronos avec le temps écoulé
                time_elapsed = 0
                if current_state['date_derniere_maj']:
                    cursor.execute('SELECT TIMESTAMPDIFF(SECOND, %s, NOW()) as ecoule',
                                   (current_state['date_derniere_maj'],))
                    time_elapsed = cursor.fetchone()['ecoule']

                    if time_elapsed > 0:
                        if current_state['controle_en_pause']:
                            # Était en pause, ajouter au chrono pause
                            new_pause = (current_state['temps_pause_total'] or 0) + time_elapsed
                            cursor.execute('''
                                UPDATE details_controle 
                                SET temps_pause_total = %s,
                                    date_derniere_maj = NOW()
                                WHERE of_id = %s
                            ''', (new_pause, of_number))
                        else:
                            # Était actif, ajouter au chrono actif
                            new_actif = (current_state['temps_actif_total'] or 0) + time_elapsed
                            cursor.execute('''
                                UPDATE details_controle 
                                SET temps_actif_total = %s,
                                    date_derniere_maj = NOW()
                                WHERE of_id = %s
                            ''', (new_actif, of_number))

                # Maintenant changer l'état de pause
                cursor.execute('''
                    UPDATE details_controle 
                    SET controle_en_pause = %s,
                        date_derniere_maj = NOW()
                    WHERE of_id = %s
                ''', (mettre_en_pause, of_number))

                conn.commit()

                # Log
                action = "PAUSE" if mettre_en_pause else "REPRISE"
                print(f"\n🔧 {action} pour OF {of_number}")
                print(f"   Temps écoulé: {time_elapsed}s")
                print(f"   État précédent: {'En pause' if current_state['controle_en_pause'] else 'Actif'}")
                print(f"   Nouvel état: {'En pause' if mettre_en_pause else 'Actif'}")

                return True
        except Exception as e:
            print(f"❌ Erreur toggle pause: {e}")
            return False
        finally:
            conn.close()

    def start_controle(self, of_number: str, quantite_a_controler: int) -> bool:
        """Démarre le contrôle pour un OF"""
        conn = self.get_connection()
        if conn is None:
            return False

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE details_controle 
                    SET statut_controle = 'En cours',
                        date_debut_controle = NOW(),
                        date_derniere_maj = NOW(),
                        quantite_a_controler = %s,
                        temps_actif_total = 0,
                        temps_pause_total = 0,
                        controle_en_pause = FALSE
                    WHERE of_id = %s
                ''', (quantite_a_controler, of_number))

                conn.commit()

                print(f"\n🚀 DÉMARRAGE CONTRÔLE pour OF {of_number}")
                print(f"   Quantité à contrôler: {quantite_a_controler}")

                return True
        except Exception as e:
            print(f"❌ Erreur démarrage contrôle: {e}")
            return False
        finally:
            conn.close()

    def update_coupe_timestamp(self, of_number: str) -> bool:
        """Met à jour le timestamp de dernière mise à jour de la coupe"""
        conn = self.get_connection()
        if conn is None:
            return False

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE details_coupe 
                    SET date_derniere_maj_coupe = NOW()
                    WHERE of_id = %s
                ''', (of_number,))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Erreur update timestamp coupe: {e}")
            return False
        finally:
            conn.close()

    def get_retour_recoupe_paires(self, of_number: str) -> Dict:
        """Récupère les informations des paires issues de recoupe à re-contrôler"""
        conn = self.get_connection()
        if conn is None:
            return {'retravailler': 0, 'rejetee': 0, 'total': 0}

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                               SELECT quantite_retravailler,
                                      quantite_rejetee
                               FROM details_controle
                               WHERE of_id = %s
                               ''', (of_number,))

                result = cursor.fetchone()
                if result:
                    retravailler = result.get('quantite_retravailler', 0) or 0
                    rejetee = result.get('quantite_rejetee', 0) or 0

                    return {
                        'retravailler': int(retravailler),
                        'rejetee': int(rejetee),
                        'total': int(retravailler) + int(rejetee)
                    }
                return {'retravailler': 0, 'rejetee': 0, 'total': 0}
        except Exception as e:
            print(f"❌ Erreur récupération retours recoupe: {e}")
            return {'retravailler': 0, 'rejetee': 0, 'total': 0}
        finally:
            conn.close()
##############################"
    def get_all_employees(self) -> List[Dict]:
        """Récupère tous les employés depuis la table employes"""
        conn = self.get_connection()
        if conn is None:
            return []

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT 
                        id_employe,
                        matricule,
                        nom,
                        prenom
                    FROM employes
                    ORDER BY nom, prenom
                ''')
                employees = cursor.fetchall()
            return employees if employees else []
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur lecture employés: {e}")
            return []
        finally:
            conn.close()

    def get_employee_by_matricule(self, matricule: str) -> Optional[Dict]:
        """Récupère un employé par son matricule"""
        conn = self.get_connection()
        if conn is None:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT 
                        id_employe,
                        matricule,
                        nom,
                        prenom
                    FROM employes
                    WHERE matricule = %s
                ''', (matricule,))
                employee = cursor.fetchone()
            return employee
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur recherche employé: {e}")
            return None
        finally:
            conn.close()
#########################################"
    def get_all_modeles(self) -> List[Dict]:
        """Récupère tous les modèles depuis la table modeles"""
        conn = self.get_connection()
        if conn is None:
            return []

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                               SELECT nom_modele,
                                      code_modele,
                                      matiere,
                                      consignes_de_coupe,
                                      emport_de_piece
                               FROM modeles
                               ORDER BY nom_modele, code_modele
                               ''')
                modeles = cursor.fetchall()
            return modeles if modeles else []
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur lecture modèles: {e}")
            return []
        finally:
            conn.close()

    def get_modele_by_code(self, code_modele: str) -> Optional[Dict]:
        """Récupère un modèle par son code"""
        conn = self.get_connection()
        if conn is None:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                               SELECT nom_modele,
                                      code_modele,
                                      matiere,
                                      consignes_de_coupe,
                                      emport_de_piece
                               FROM modeles
                               WHERE code_modele = %s
                               ''', (code_modele,))
                modele = cursor.fetchone()
            return modele
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur recherche modèle: {e}")
            return None
        finally:
            conn.close()

    def get_modeles_by_nom(self, nom_modele: str) -> List[Dict]:
        conn = self.get_connection()
        if conn is None:
            return []

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                               SELECT nom_modele,
                                      code_modele,
                                      matiere,
                                      consignes_de_coupe,
                                      emport_de_piece
                               FROM modeles
                               WHERE nom_modele = %s
                               ORDER BY code_modele
                               """, (nom_modele,))
                return cursor.fetchall() or []
        finally:
            conn.close()

    def get_modele_by_nom(self, nom_modele: str) -> Optional[Dict]:
        """Récupère un modèle par son nom (le PREMIER trouvé)"""
        conn = self.get_connection()
        if conn is None:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                               SELECT nom_modele,
                                      code_modele,
                                      matiere,
                                      consignes_de_coupe,
                                      emport_de_piece
                               FROM modeles
                               WHERE nom_modele = %s LIMIT 1
                               ''', (nom_modele,))
                modele = cursor.fetchone()
            return modele
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur recherche modèle par nom: {e}")
            return None
        finally:
            conn.close()
################################################################
    def get_couleur_by_code(self, code_couleur: str) -> Optional[Dict]:
        """Récupère une couleur par son code"""
        conn = self.get_connection()
        if conn is None:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                               SELECT code_couleur,
                                      nom_couleur
                               FROM code_couleur
                               WHERE code_couleur = %s
                               ''', (code_couleur,))
                couleur = cursor.fetchone()
            return couleur
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur recherche couleur: {e}")
            return None
        finally:
            conn.close()

    def get_all_coloris(self) -> List[Dict]:
        """Récupère tous les couleurs depuis la table code_couleur"""
        conn = self.get_connection()
        if conn is None:
            return []

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                               SELECT code_couleur,
                                      nom_couleur
                               FROM code_couleur
                               ORDER BY code_couleur
                               ''')
                code_couleur = cursor.fetchall()
            return code_couleur if code_couleur else []
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur lecture couleurs: {e}")
            return []
        finally:
            conn.close()

    def get_surconsommation_data(self) -> List[Dict]:
        """Récupère les données de sur-consommation"""
        conn = self.get_connection()
        if conn is None:
            return []

        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                               SELECT o.of,
                                      o.modele,
                                      c.coloris,
                                      c.matiere,
                                      c.matricule_coupeur,
                                      c.consommation,
                                      c.sur_consommation,
                                      c.date_debut_coupe,
                                      c.date_fin_coupe,
                                      c.temps_coupe,
                                      c.duree_totale_pause,
                                      c.statut_coupe,
                                      u.nom         as nom_coupeur,
                                      u.prenom      as prenom_coupeur,
                                      c.observation as observation_coupe
                               FROM details_coupe c
                                        JOIN ordres_fabrication o ON c.of_id = o.of
                                        LEFT JOIN employes u ON c.matricule_coupeur = u.matricule
                               WHERE c.sur_consommation > 0
                               ORDER BY c.sur_consommation DESC
                               ''')
                data = cursor.fetchall()

            # Calculer les indicateurs additionnels
            for item in data:
                if item['consommation'] is not None and item['sur_consommation'] is not None:
                    consommation = float(item['consommation'])
                    surcons = float(item['sur_consommation'])
                    item['total_consommation'] = consommation + surcons
                    item['taux_surcons'] = (surcons / consommation * 100) if consommation > 0 else 0
                else:
                    item['total_consommation'] = 0
                    item['taux_surcons'] = 0

            return data if data else []
        except Exception as e:
            print(f"❌ Erreur récupération surconsommation: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            conn.close()
    # ===== 3. NOUVELLE MÉTHODE start_piqure() =====

    def start_piqure(self, of_number: str, matricule_piqueur: str, observation: str = "") -> bool:
        """Démarre l'opération de piqûre pour un OF"""
        conn = self.get_connection()
        if conn is None:
            return False

        try:
            with conn.cursor() as cursor:
                # Vérifier si l'enregistrement existe déjà
                cursor.execute('SELECT id FROM details_piqure WHERE of_id = %s', (of_number,))
                exists = cursor.fetchone()

                if exists:
                    # Mettre à jour
                    cursor.execute('''
                                   UPDATE details_piqure
                                   SET statut_piqure            = 'En attente',
                                       matricule_piqueur        = %s,
                                       observation_piqure       = %s,
                                       date_derniere_maj_piqure = NOW()
                                   WHERE of_id = %s
                                   ''', (matricule_piqueur, observation, of_number))
                else:
                    # Insérer
                    cursor.execute('''
                                   INSERT INTO details_piqure
                                   (of_id, matricule_piqueur, observation_piqure, statut_piqure,
                                    temps_piqure, date_derniere_maj_piqure)
                                   VALUES (%s, %s, %s, 'En attente', 0, NOW())
                                   ''', (of_number, matricule_piqueur, observation))

            conn.commit()
            return True
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Erreur démarrage piqûre: {e}")
            return False
        finally:
            conn.close()


class Utils:
    """Classe d'utilitaires"""

    @staticmethod
    def format_time(seconds: int) -> str:
        """Formate en HH:MM:SS"""
        if seconds <= 0:
            return "00:00:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{int(hours):02d}:{int(minutes):02d}:{int(secs):02d}"

    @staticmethod
    def get_status_badge(status: str) -> str:
        """Retourne un badge HTML pour le statut"""
        status_config = {
            'En attente': {'class': 'status-attente', 'icon': '⏳', 'text': 'En attente'},
            'En cours': {'class': 'status-cours', 'icon': '🔄', 'text': 'En cours'},
            'Terminée': {'class': 'status-termine', 'icon': '✅', 'text': 'Terminée'},
            'En pause': {'class': 'status-pause', 'icon': '⏸️', 'text': 'En pause'},
            'Approuvé ✅': {'class': 'status-approuve', 'icon': '✅', 'text': 'Approuvé'},
            'Rejeté ❌': {'class': 'status-rejete', 'icon': '❌', 'text': 'Rejeté'},
            'À retravailler 🔧': {'class': 'status-retravailler', 'icon': '🔧', 'text': 'À retravailler'},
            'Contrôle partiel': {'class': 'status-partiel', 'icon': '👌', 'text': 'Contrôle partiel'}
        }

        if status in status_config:
            config = status_config[status]
            return f'<span class="status-badge {config["class"]}">{config["icon"]} {config["text"]}</span>'
        else:
            return f'<span class="status-badge status-attente">❓ {status}</span>'

    @staticmethod
    def calculate_pause_duration(order: Dict, pause_type: str = 'coupe') -> int:
        """Calcule la durée totale de pause"""
        try:
            if pause_type == 'coupe':
                duree_totale = order.get('duree_totale_pause', 0) or 0
                duree_totale = int(duree_totale) if duree_totale is not None else 0

                # Si en pause, ajouter le temps écoulé depuis la dernière pause
                if order.get('coupe_en_pause') and order.get('date_derniere_pause'):
                    try:
                        if isinstance(order['date_derniere_pause'], str):
                            last_pause = datetime.fromisoformat(order['date_derniere_pause'].replace('Z', '+00:00'))
                        else:
                            last_pause = order['date_derniere_pause']

                        current_pause_duration = int((datetime.now() - last_pause).total_seconds())
                        return duree_totale + current_pause_duration
                    except:
                        return duree_totale

                return duree_totale

            elif pause_type == 'controle':
                # Pour contrôle, utiliser temps_pause_total
                duree_totale = order.get('temps_pause_total', 0) or 0
                duree_totale = int(duree_totale) if duree_totale is not None else 0

                # Si en pause, ajouter le temps écoulé depuis la dernière maj
                if order.get('controle_en_pause') and order.get('date_derniere_maj'):
                    try:
                        if isinstance(order['date_derniere_maj'], str):
                            last_update = datetime.fromisoformat(order['date_derniere_maj'].replace('Z', '+00:00'))
                        else:
                            last_update = order['date_derniere_maj']

                        current_pause_duration = int((datetime.now() - last_update).total_seconds())
                        return duree_totale + current_pause_duration
                    except:
                        return duree_totale

                return duree_totale

            elif pause_type == 'piqure':
                duree_totale = order.get('duree_totale_pause_piqure', 0) or 0
                duree_totale = int(duree_totale) if duree_totale is not None else 0

                # Si en pause, ajouter le temps écoulé depuis la dernière pause
                if order.get('piqure_en_pause') and order.get('date_derniere_pause_piqure'):
                    try:
                        if isinstance(order['date_derniere_pause_piqure'], str):
                            last_pause = datetime.fromisoformat(
                                order['date_derniere_pause_piqure'].replace('Z', '+00:00'))
                        else:
                            last_pause = order['date_derniere_pause_piqure']

                        current_pause_duration = int((datetime.now() - last_pause).total_seconds())
                        return duree_totale + current_pause_duration
                    except:
                        return duree_totale

                return duree_totale

            else:
                return 0
        except Exception as e:
            print(f"❌ Erreur calculate_pause_duration: {e}")
            return 0
    @staticmethod
    def get_quality_details(order: Dict) -> Dict:
        """Retourne les détails qualité"""
        quantite_controlee = order.get('quantite_controlee', 0) or 0
        quantite_acceptee = order.get('quantite_acceptee', 0) or 0
        quantite_rejetee = order.get('quantite_rejetee', 0) or 0
        quantite_retravailler = order.get('quantite_retravailler', 0) or 0

        # Si quantite_acceptee n'est pas défini, le calculer
        if quantite_acceptee == 0 and quantite_controlee > 0:
            quantite_acceptee = quantite_controlee - quantite_rejetee - quantite_retravailler

        return {
            'controlee': quantite_controlee,
            'acceptee': quantite_acceptee,
            'rejetee': quantite_rejetee,
            'retravailler': quantite_retravailler,
            'acceptee_pourcentage': (quantite_acceptee / quantite_controlee * 100) if quantite_controlee > 0 else 0,
            'rejetee_pourcentage': (quantite_rejetee / quantite_controlee * 100) if quantite_controlee > 0 else 0,
            'retravailler_pourcentage': (
                    quantite_retravailler / quantite_controlee * 100) if quantite_controlee > 0 else 0
        }

    @staticmethod
    def get_pause_info(order: Dict) -> str:
        """Retourne infos sur les pauses de coupe"""
        try:
            duree_pause = Utils.calculate_pause_duration(order, 'coupe')
            duree_pause = int(duree_pause) if duree_pause is not None else 0

            if order.get('coupe_en_pause'):
                return f"⏸️ EN PAUSE: {Utils.format_time(duree_pause)}"
            elif duree_pause > 0:
                return f"⏸️ Total pauses: {Utils.format_time(duree_pause)}"
            return ""
        except Exception:
            return ""

    @staticmethod
    def get_controle_pause_info(order: Dict) -> str:
        """Retourne infos sur les pauses de contrôle"""
        try:
            duree_pause = Utils.calculate_pause_duration(order, 'controle')
            duree_pause = int(duree_pause) if duree_pause is not None else 0

            if order.get('controle_en_pause'):
                return f"⏸️ EN PAUSE: {Utils.format_time(duree_pause)}"
            elif duree_pause > 0:
                return f"⏸️ Total pauses contrôle: {Utils.format_time(duree_pause)}"
            return ""
        except Exception:
            return ""
    @staticmethod
    def get_pause_info_piqure(order: Dict) -> str:
        """Retourne infos sur les pauses de piqûre"""
        try:
            duree_pause = Utils.calculate_pause_duration(order, 'piqure')
            duree_pause = int(duree_pause) if duree_pause is not None else 0

            if order.get('piqure_en_pause'):
                return f"⏸️ EN PAUSE: {Utils.format_time(duree_pause)}"
            elif duree_pause > 0:
                return f"⏸️ Total pauses: {Utils.format_time(duree_pause)}"
            return ""
        except Exception:
            return ""

class DualChronoUtils:
    """Utilitaires pour les deux chronomètres"""

    @staticmethod
    def get_dual_chrono_info(order: Dict) -> Dict:
        """Retourne les informations des deux chronomètres"""
        temps_actif = order.get('temps_actif_total', 0) or 0
        temps_pause = order.get('temps_pause_total', 0) or 0

        # Conversion en int
        temps_actif = int(temps_actif) if temps_actif is not None else 0
        temps_pause = int(temps_pause) if temps_pause is not None else 0

        # Calcul du temps total écoulé
        total_ecoule = 0
        if order.get('date_debut_controle'):
            try:
                total_ecoule = int((datetime.now() - order['date_debut_controle']).total_seconds())
            except:
                total_ecoule = 0

        # Calcul des pourcentages
        if total_ecoule > 0:
            pourcentage_actif = (temps_actif / total_ecoule * 100)
            pourcentage_pause = (temps_pause / total_ecoule * 100)
        else:
            pourcentage_actif = pourcentage_pause = 0

        return {
            'temps_actif': temps_actif,
            'temps_pause': temps_pause,
            'total_ecoule': total_ecoule,
            'pourcentage_actif': pourcentage_actif,
            'pourcentage_pause': pourcentage_pause,
            'en_pause': bool(order.get('controle_en_pause')),
            'date_debut': order.get('date_debut_controle'),
            'date_derniere_maj': order.get('date_derniere_maj')
        }

    @staticmethod
    def format_dual_display_html(order: Dict) -> str:
        """Retourne le HTML pour afficher les deux chronomètres"""
        info = DualChronoUtils.get_dual_chrono_info(order)
        utils = Utils()

        html = f"""
        <div class="dual-chrono-container">
            <div class="dual-chrono-header">
                <span style="font-weight: 700; color: #1F2937;">⏱️ Chronomètres Indépendants</span>
                <span class="status-badge {'status-pause' if info['en_pause'] else 'status-cours'}">
                    {'⏸️ EN PAUSE' if info['en_pause'] else '🔄 ACTIF'}
                </span>
            </div>

            <div class="dual-chrono-body">
                <div class="chrono-card chrono-actif">
                    <div class="chrono-title">🔄 Production</div>
                    <div class="chrono-value">{utils.format_time(info['temps_actif'])}</div>
                    <div class="chrono-percentage">{info['pourcentage_actif']:.1f}%</div>
                    <div class="chrono-status">{'⏸️ Figé' if info['en_pause'] else '🔄 Incrémente'}</div>
                </div>

                <div class="chrono-separator"></div>

                <div class="chrono-card chrono-pause">
                    <div class="chrono-title">⏸️ Pauses</div>
                    <div class="chrono-value">{utils.format_time(info['temps_pause'])}</div>
                    <div class="chrono-percentage">{info['pourcentage_pause']:.1f}%</div>
                    <div class="chrono-status">{'🔄 Incrémente' if info['en_pause'] else '⏸️ Figé'}</div>
                </div>
            </div>

            <div class="dual-chrono-footer">
                <div>📊 Total écoulé: {utils.format_time(info['total_ecoule'])}</div>
                <div>📐 Actif + Pause = {utils.format_time(info['temps_actif'] + info['temps_pause'])}</div>
            </div>
        </div>
        """
        return html

    @staticmethod
    def calculate_time_since_last_update(order: Dict) -> int:
        """Calcule le temps écoulé depuis la dernière mise à jour"""
        if not order.get('date_derniere_maj'):
            return 0

        try:
            last_update = order['date_derniere_maj']
            if isinstance(last_update, str):
                last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))

            return int((datetime.now() - last_update).total_seconds())
        except:
            return 0


class KPIManager:
    """Gestionnaire des KPIs"""

    def __init__(self, orders: List[Dict]):
        self.orders = orders
        self.utils = Utils()

    def calculate_kpis(self) -> Dict:
        """Calcule tous les KPIs"""
        total_of = len(self.orders)
        of_en_coupe = len([o for o in self.orders if o['statut_coupe'] == 'En cours'])
        of_en_pause_coupe = len([o for o in self.orders if o.get('coupe_en_pause')])
        of_termines_coupe = len([o for o in self.orders if o['statut_coupe'] == 'Terminée'])
        of_en_controle = len([o for o in self.orders if o['statut_controle'] == 'En cours'])
        of_en_pause_controle = len([o for o in self.orders if o.get('controle_en_pause')])

        # Temps de pause totaux
        total_pause_coupe = sum(self.utils.calculate_pause_duration(o, 'coupe')
                                for o in self.orders if o.get('coupe_en_pause') or o.get('duree_totale_pause', 0) > 0)
        total_pause_controle = sum(self.utils.calculate_pause_duration(o, 'controle')
                                   for o in self.orders if
                                   o.get('controle_en_pause') or o.get('duree_pause_controle', 0) > 0)

        # Quantités
        total_quantite = sum(o['quantite'] for o in self.orders)
        total_controlees = sum(o.get('quantite_controlee', 0) or 0 for o in self.orders)
        total_rejetees = sum(o.get('quantite_rejetee', 0) or 0 for o in self.orders)
        total_retravailler = sum(o.get('quantite_retravailler', 0) or 0 for o in self.orders)

        # Calculer les acceptées
        total_acceptees = 0
        for o in self.orders:
            quantite_controlee = o.get('quantite_controlee', 0) or 0
            quantite_rejetee = o.get('quantite_rejetee', 0) or 0
            quantite_retravailler = o.get('quantite_retravailler', 0) or 0
            total_acceptees += quantite_controlee - quantite_rejetee - quantite_retravailler

        # Taux
        taux_problemes = ((total_rejetees + total_retravailler) / total_controlees * 100) if total_controlees > 0 else 0
        taux_controle = (total_controlees / total_quantite * 100) if total_quantite > 0 else 0
        taux_completion = (of_termines_coupe / total_of * 100) if total_of > 0 else 0
        taux_acceptation = (total_acceptees / total_controlees * 100) if total_controlees > 0 else 0

        return {
            'total_of': total_of,
            'of_en_coupe': of_en_coupe,
            'of_en_pause_coupe': of_en_pause_coupe,
            'of_termines_coupe': of_termines_coupe,
            'of_en_controle': of_en_controle,
            'of_en_pause_controle': of_en_pause_controle,
            'total_pause_coupe': total_pause_coupe,
            'total_pause_controle': total_pause_controle,
            'total_quantite': total_quantite,
            'total_controlees': total_controlees,
            'total_rejetees': total_rejetees,
            'total_retravailler': total_retravailler,
            'total_acceptees': total_acceptees,
            'taux_problemes': taux_problemes,
            'taux_controle': taux_controle,
            'taux_completion': taux_completion,
            'taux_acceptation': taux_acceptation
        }

    def display_kpi_cards(self):
        """Affiche les cartes KPI"""
        import streamlit as st
        kpis = self.calculate_kpis()

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">OF Actifs</div>
                <div class="metric-value">{kpis['total_of']}</div>
                <div class="metric-change positive">↗️ {kpis['of_en_coupe']} en cours</div>
                <div style="margin-top: 15px; font-size: 0.85rem; color: #6B7280;">
                    <div>✅ {kpis['of_termines_coupe']} terminés</div>
                    <div>⏸️ {kpis['of_en_pause_coupe']} en pause</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Production</div>
                <div class="metric-value">{kpis['total_quantite']:,}</div>
                <div class="metric-title">paires totales</div>
                <div style="margin-top: 15px; font-size: 0.85rem; color: #6B7280;">
                    <div>👌 {kpis['total_controlees']:,} contrôlées</div>
                    <div>📈 {kpis['taux_controle']:.1f}% taux contrôle</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Qualité</div>
                <div class="metric-value">{kpis['taux_acceptation']:.1f}%</div>
                <div class="metric-title">taux acceptation</div>
                <div style="margin-top: 15px; font-size: 0.85rem; color: #6B7280;">
                    <div>✅ {kpis['total_acceptees']:,} acceptées</div>
                    <div>❌ {kpis['total_rejetees']:,} rejetées</div>
                    <div>🔧 {kpis['total_retravailler']:,} à retravailler</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Pauses</div>
                <div class="metric-value">{Utils.format_time(kpis['total_pause_coupe'])}</div>
                <div class="metric-title">temps pause coupe</div>
                <div style="margin-top: 15px; font-size: 0.85rem; color: #6B7280;">
                    <div>⏸️ {kpis['of_en_pause_coupe']} OF en pause coupe</div>
                    <div>⏱️ {Utils.format_time(kpis['total_pause_controle'])} pause contrôle</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Efficacité</div>
                <div class="metric-value">{kpis['taux_completion']:.1f}%</div>
                <div class="metric-title">complétion</div>
                <div style="margin-top: 15px; font-size: 0.85rem; color: #6B7280;">
                    <div>⏱️ {kpis['of_en_controle']} en contrôle</div>
                    <div>⏸️ {kpis['of_en_pause_controle']} contrôle pause</div>
                </div>
            </div>
            """, unsafe_allow_html=True)