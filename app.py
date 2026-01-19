# app.py - Fichier principal
import streamlit as st
from database import Config, DatabaseManager,Utils
from login_page import LoginPage
from sidebar_manager import SidebarManager
from chef_coupe_page import ChefCoupePage
from controle_qualite_page import ControleQualitePage
from directeur_page import DirecteurPage
from chef_piqure_page import ChefPiqurePage


class App:
    """Application principale"""

    def __init__(self):
        self.config = Config()
        self.db_manager = DatabaseManager()
        self.utils = Utils()

        # Initialiser la session
        self.config.init_session_state()

        # Charger les styles
        self._load_styles()

    def _load_styles(self):
        """Charge les styles CSS complets avec tableau amélioré"""
        st.set_page_config(**self.config.PAGE_CONFIG)
        st.markdown("""
        <style>
            /* ===== THEME PRINCIPAL REPETTO ===== */
            :root {
                --repetto-pink: #E75480;
                --repetto-light-pink: #F9E0E8;
                --repetto-dark: #2D3748;
                --repetto-light: #F8F9FA;
                --repetto-gray: #E2E8F0;
                --repetto-success: #10B981;
                --repetto-warning: #F59E0B;
                --repetto-danger: #EF4444;
                --repetto-info: #3B82F6;
            }
            
            /* ===== STYLES POUR RECOUPE ===== */

            .time-cell-recoupe {
                font-family: 'Courier New', 'JetBrains Mono', monospace;
                font-weight: 700;
                color: #FFFFFF;
                background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
                padding: 8px 12px !important;
                border-radius: 6px;
                text-align: center;
                font-size: 0.85rem;
                display: inline-block;
                min-width: 85px;
                border: 1px solid #D97706;
                box-shadow: 0 2px 6px rgba(245, 158, 11, 0.3);
            }

            .time-cell-total:hover::after {
                content: "Total = Temps coupe + Temps pause";
                position: absolute;
                background: #1F2937;
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 0.8rem;
                z-index: 1000;
                margin-top: 5px;
                white-space: nowrap;
            }

            .time-cell-empty {
                color: #9CA3AF;
                background: #F9FAFB;
                padding: 8px 12px !important;
                border-radius: 6px;
                display: inline-block;
                min-width: 85px;
                border: 1px solid #E5E7EB;
                text-align: center;
                font-size: 0.85rem;
            }

            .recoupe-badge {
                background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
                color: white;
                font-weight: 800;
                padding: 6px 14px;
                border-radius: 20px;
                display: inline-block;
                font-size: 0.85rem;
                box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
                border: 1px solid #D97706;
            }

            .recoupe-empty {
                color: #9CA3AF;
                background: #F9FAFB;
                padding: 6px 14px;
                border-radius: 20px;
                display: inline-block;
                font-size: 0.85rem;
                border: 1px solid #E5E7EB;
            }
            /* ===== FOND PRINCIPAL ===== */
            .stApp {
                background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
                font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
            }

            /* ===== SIDEBAR STYLISÉ ===== */
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
                border-right: 1px solid var(--repetto-gray);
                padding: 1rem;
            }

            [data-testid="stSidebar"] .stSelectbox {
                margin-bottom: 1rem;
            }

            /* ===== HEADER PRINCIPAL ===== */
            .main-header {
                font-size: 2.8rem;
                font-weight: 800;
                background: linear-gradient(90deg, var(--repetto-pink) 0%, #FF6B95 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
                font-family: 'Inter', sans-serif;
            }

            .sub-header {
                font-size: 1.1rem;
                color: var(--repetto-dark);
                opacity: 0.8;
                margin-bottom: 2rem;
                font-weight: 400;
            }

            /* ===== NAVIGATION BAR ===== */
            .nav-container {
                background: white;
                border-radius: 16px;
                padding: 0.8rem 1.5rem;
                margin: 1rem 0;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
                border: 1px solid var(--repetto-gray);
                display: flex;
                align-items: center;
                justify-content: space-between;
            }

            .user-info {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .user-avatar {
                width: 42px;
                height: 42px;
                background: linear-gradient(135deg, var(--repetto-pink) 0%, #FF6B95 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 18px;
            }

            /* ===== SECTION HEADERS ===== */
            .section-header {
                font-size: 1.6rem;
                font-weight: 700;
                color: var(--repetto-dark);
                padding: 1rem 0;
                margin: 2rem 0 1rem 0;
                border-bottom: 2px solid var(--repetto-light-pink);
                position: relative;
            }

            .section-header:before {
                content: '';
                position: absolute;
                bottom: -2px;
                left: 0;
                width: 60px;
                height: 2px;
                background: var(--repetto-pink);
            }
/* ===== STYLES POUR DEUX CHRONOMÈTRES ===== */
.dual-chrono-container {
    background: white;
    padding: 20px;
    border-radius: 12px;
    border: 2px solid #E2E8F0;
    margin: 15px 0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.dual-chrono-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #E2E8F0;
}

.dual-chrono-body {
    display: flex;
    gap: 20px;
    align-items: center;
}

.chrono-card {
    flex: 1;
    text-align: center;
    padding: 20px;
    border-radius: 10px;
    transition: all 0.3s ease;
}

.chrono-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.chrono-actif {
    background: linear-gradient(135deg, #F0FDF4 0%, #D1FAE5 100%);
    border: 2px solid #10B981;
}

.chrono-pause {
    background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
    border: 2px solid #EF4444;
}

.chrono-title {
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 10px;
}

.chrono-actif .chrono-title {
    color: #065F46;
}

.chrono-pause .chrono-title {
    color: #991B1B;
}

.chrono-value {
    font-size: 2rem;
    font-weight: 800;
    font-family: 'Courier New', monospace;
    margin: 10px 0;
}

.chrono-actif .chrono-value {
    color: #10B981;
}

.chrono-pause .chrono-value {
    color: #EF4444;
}

.chrono-percentage {
    font-size: 0.9rem;
    color: #6B7280;
    margin-bottom: 5px;
}

.chrono-status {
    font-size: 0.85rem;
    font-weight: 600;
    padding: 5px 10px;
    border-radius: 20px;
    display: inline-block;
}

.chrono-actif .chrono-status {
    background: #10B981;
    color: white;
}

.chrono-pause .chrono-status {
    background: #EF4444;
    color: white;
}

.chrono-separator {
    width: 2px;
    height: 100px;
    background: linear-gradient(180deg, transparent, #E2E8F0, transparent);
}

.dual-chrono-footer {
    margin-top: 20px;
    padding-top: 15px;
    border-top: 1px solid #E2E8F0;
    text-align: center;
    font-size: 0.85rem;
    color: #6B7280;
    display: flex;
    justify-content: space-around;
}

            /* ===== TIMER DISPLAY ===== */
            .timer-display {
                font-family: 'Courier New', 'JetBrains Mono', monospace;
                font-size: 2.2rem;
                font-weight: 800;
                text-align: center;
                padding: 1.5rem;
                background: linear-gradient(135deg, #1F2937 0%, #111827 100%);
                color: #10B981;
                border-radius: 16px;
                margin: 1rem 0;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
                letter-spacing: 2px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            .timer-paused {
                font-family: 'Courier New', 'JetBrains Mono', monospace;
                font-size: 2.2rem;
                font-weight: 800;
                text-align: center;
                padding: 1.5rem;
                background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
                color: #DC2626;
                border-radius: 16px;
                margin: 1rem 0;
                box-shadow: 0 8px 32px rgba(220, 38, 38, 0.15);
                letter-spacing: 2px;
                border: 2px solid #F87171;
                animation: blink-timer 1s ease-in-out infinite;
            }

            @keyframes blink-timer {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            /* ===== BOUTONS STYLISÉS ===== */
            .stButton > button {
                border-radius: 10px;
                font-weight: 600;
                transition: all 0.3s ease;
                border: none;
                padding: 10px 24px;
            }

            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
            }

            .btn-primary {
                background: linear-gradient(135deg, var(--repetto-pink) 0%, #FF6B95 100%) !important;
                color: white !important;
            }

            /* ===== BADGES DE STATUT ===== */
            .status-badge {
                padding: 8px 18px;
                border-radius: 25px;
                font-size: 0.85rem;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                margin: 2px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }

            .status-attente { 
                background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); 
                color: #92400E; 
                border: 1px solid #FBBF24;
            }
            .status-cours { 
                background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%); 
                color: #1E40AF; 
                border: 1px solid #60A5FA;
            }
            .status-pause { 
                background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%); 
                color: #991B1B; 
                border: 1px solid #F87171;
            }
            .status-termine { 
                background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); 
                color: #065F46; 
                border: 1px solid #10B981;
            }
            .status-approuve { 
                background: linear-gradient(135deg, var(--repetto-success) 0%, #34D399 100%); 
                color: white; 
                border: none;
            }
            .status-rejete { 
                background: linear-gradient(135deg, var(--repetto-danger) 0%, #F87171 100%); 
                color: white; 
                border: none;
            }
            .status-retravailler { 
                background: linear-gradient(135deg, var(--repetto-warning) 0%, #FBBF24 100%); 
                color: white; 
                border: none;
            }

            .status-partiel { 
                background: linear-gradient(135deg, #A78BFA 0%, #C4B5FD 100%); 
                color: white; 
                border: none;
            }

            /* ===== CARTES DE METRIQUES ===== */
            .metric-card {
                background: white;
                padding: 1.8rem;
                border-radius: 16px;
                box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
                border: 1px solid var(--repetto-gray);
                transition: all 0.3s ease;
                height: 100%;
            }

            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
                border-color: var(--repetto-light-pink);
            }

            .metric-title {
                font-size: 0.95rem;
                color: var(--repetto-dark);
                opacity: 0.7;
                font-weight: 600;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .metric-value {
                font-size: 2.2rem;
                font-weight: 800;
                color: var(--repetto-dark);
                line-height: 1;
                margin: 0.5rem 0;
            }

            .metric-change {
                font-size: 0.85rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 4px;
            }

            .metric-change.positive { color: var(--repetto-success); }
            .metric-change.negative { color: var(--repetto-danger); }

            /* ===== CARTES D'INFORMATION ===== */
            .info-card {
                background: white;
                padding: 1.5rem;
                border-radius: 14px;
                border: 1px solid var(--repetto-gray);
                box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
                margin-bottom: 1rem;
            }

            .info-card h4 {
                color: var(--repetto-pink);
                margin: 0 0 12px 0;
                font-size: 1.1rem;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            /* ===== CARTES SPECIALES ===== */
            .quality-control-section {
                background: linear-gradient(135deg, #FFFFFF 0%, #F0FDF4 100%);
                padding: 2rem;
                border-radius: 18px;
                border-left: 6px solid var(--repetto-success);
                margin: 1.5rem 0;
                box-shadow: 0 4px 20px rgba(16, 185, 129, 0.1);
            }

            .warning-card {
                background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
                padding: 1.5rem;
                border-radius: 14px;
                border-left: 6px solid var(--repetto-warning);
                margin: 1rem 0;
                border: 1px solid #FDE68A;
            }

            .alert-card {
                background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
                padding: 1.5rem;
                border-radius: 14px;
                border-left: 6px solid var(--repetto-danger);
                margin: 1rem 0;
                border: 1px solid #FECACA;
            }

            .info-notification {
                background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
                padding: 1.5rem;
                border-radius: 14px;
                border-left: 6px solid var(--repetto-info);
                margin: 1rem 0;
                border: 1px solid #BFDBFE;
            }

            /* ===== PAUSE INFO ===== */
            .pause-info {
                background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
                padding: 8px 16px;
                border-radius: 8px;
                color: #991B1B;
                font-weight: 600;
                font-size: 0.85rem;
                margin-top: 8px;
                border: 1px solid #F87171;
                display: inline-block;
            }

            /* ===== ONGLETS ===== */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background: none;
                padding: 0;
            }

            .stTabs [data-baseweb="tab"] {
                background: white;
                border-radius: 12px 12px 0 0;
                padding: 14px 28px;
                font-weight: 600;
                border: 1px solid var(--repetto-gray);
                border-bottom: none;
                transition: all 0.3s ease;
            }

            .stTabs [data-baseweb="tab"]:hover {
                background: var(--repetto-light-pink);
            }

            .stTabs [aria-selected="true"] {
                background: var(--repetto-pink) !important;
                color: white !important;
                border-color: var(--repetto-pink) !important;
            }

            /* ===== TABLEAU AMÉLIORÉ AVEC COULEURS ===== */
            .dataframe-container {
                max-height: 600px;
                overflow-y: auto;
                overflow-x: auto;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
                border: 1px solid #E2E8F0;
                margin: 1rem 0;
            }

            .data-table {
                width: 100%;
                border-collapse: collapse;
                background: white;
                min-width: 1200px;
            }

            .data-table thead {
                position: sticky;
                top: 0;
                z-index: 10;
                background: linear-gradient(135deg, #E75480 0%, #D63465 100%);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }

            .data-table th {
                padding: 14px 12px;
                text-align: left;
                color: white;
                font-weight: 700;
                font-size: 0.9rem;
                border-bottom: 2px solid #D63465;
                white-space: nowrap;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .data-table td {
                padding: 12px;
                border-bottom: 1px solid #E2E8F0;
                font-size: 0.85rem;
                vertical-align: middle;
            }

            .data-table tbody tr {
                cursor: pointer;
                transition: all 0.2s ease;
                background: white;
            }

            .data-table tbody tr:nth-child(even) {
                background: #F9FAFB;
            }

            .data-table tbody tr:hover {
                background: linear-gradient(135deg, #F9E0E8 0%, #FFF0F5 100%) !important;
                transform: scale(1.002);
                box-shadow: 0 2px 8px rgba(231, 84, 128, 0.15);
            }

            /* OF en première colonne */
            .data-table td:first-child {
                font-weight: 700;
                color: #E75480;
                font-size: 0.9rem;
            }

            /* Cellules avec statut */
            .status-cell {
                padding: 6px 12px;
                border-radius: 20px;
                font-weight: 600;
                font-size: 0.8rem;
                display: inline-block;
                text-align: center;
                min-width: 90px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
                transition: all 0.2s ease;
                white-space: nowrap;
            }

            .status-cell:hover {
                transform: scale(1.05);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            }

            /* Statuts Coupe avec couleurs distinctes */
            .status-attente { 
                background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); 
                color: #92400E;
                border: 1px solid #FBBF24;
            }

            .status-en-cours { 
                background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%); 
                color: #1E40AF;
                border: 1px solid #60A5FA;
                animation: pulse-status 2s ease-in-out infinite;
            }

            .status-terminee { 
                background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); 
                color: #065F46;
                border: 1px solid #10B981;
            }

            .status-pause { 
                background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%); 
                color: #991B1B;
                border: 1px solid #F87171;
                animation: blink-status 1.5s ease-in-out infinite;
            }

            /* Statuts Contrôle avec couleurs distinctes */
            .status-approuve { 
                background: linear-gradient(135deg, #10B981 0%, #059669 100%); 
                color: white;
                border: none;
            }

            .status-rejete { 
                background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%); 
                color: white;
                border: none;
            }

            .status-retravailler { 
                background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); 
                color: white;
                border: none;
            }

            .status-partiel { 
                background: linear-gradient(135deg, #A78BFA 0%, #8B5CF6 100%); 
                color: white;
                border: none;
            }

            /* Cellules de temps avec style monospace */
            .pause-cell {
                font-family: 'Courier New', 'JetBrains Mono', monospace;
                font-weight: 600;
                color: #991B1B;
                background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
                padding: 8px 12px !important;
                border-radius: 6px;
                text-align: center;
                font-size: 0.85rem;
                display: inline-block;
                min-width: 85px;
                border: 1px solid #F87171;
            }

            .pause-cell-active {
                font-family: 'Courier New', 'JetBrains Mono', monospace;
                font-weight: 700;
                color: #FFFFFF;
                background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
                padding: 8px 12px !important;
                border-radius: 6px;
                text-align: center;
                font-size: 0.85rem;
                display: inline-block;
                min-width: 85px;
                border: 1px solid #DC2626;
                box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
                animation: blink-pause-active 1s ease-in-out infinite;
            }

            .pause-cell-zero {
                color: #9CA3AF;
                background: #F9FAFB;
                padding: 8px 12px !important;
                border-radius: 6px;
                text-align: center;
                font-size: 0.85rem;
                display: inline-block;
                min-width: 85px;
                border: 1px solid #E5E7EB;
            }
            /* Cellule de progression avec couleurs selon pourcentage */
            .progress-cell {
                font-weight: 700;
                font-size: 0.9rem;
                padding: 6px 12px !important;
                border-radius: 6px;
                text-align: center;
                display: inline-block;
                min-width: 60px;
            }

            .progress-low { 
                background: #FEE2E2;
                color: #DC2626;
                border: 1px solid #F87171;
            }

            .progress-medium { 
                background: #FEF3C7;
                color: #D97706;
                border: 1px solid #FBBF24;
            }

            .progress-high { 
                background: #DBEAFE;
                color: #1E40AF;
                border: 1px solid #60A5FA;
            }

            .progress-complete { 
                background: #D1FAE5;
                color: #059669;
                border: 1px solid #10B981;
            }

            /* Animations */
            @keyframes pulse-status {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.8; transform: scale(0.98); }
            }

            @keyframes pulse-time {
                0%, 100% { transform: scale(1); box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08); }
                50% { transform: scale(1.05); box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3); }
            }

            @keyframes blink-status {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.6; }
            }

            @keyframes blink-pause {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.7; transform: scale(1.02); }
            }

            /* Scrollbar personnalisée pour le tableau */
            .dataframe-container::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }

            .dataframe-container::-webkit-scrollbar-track {
                background: #F3F4F6;
                border-radius: 10px;
            }

            .dataframe-container::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, #E75480 0%, #D63465 100%);
                border-radius: 10px;
            }

            .dataframe-container::-webkit-scrollbar-thumb:hover {
                background: #D63465;
            }

            /* ===== MODAL DÉTAILS ===== */
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 999;
                backdrop-filter: blur(4px);
                animation: fadeIn 0.3s ease-out;
            }

            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            .modal-content {
                background: white;
                border-radius: 16px;
                padding: 2rem;
                max-width: 900px;
                margin: 2rem auto;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-height: 80vh;
                overflow-y: auto;
                animation: slideIn 0.3s ease-out;
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-50px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .modal-content::-webkit-scrollbar {
                width: 6px;
            }

            .modal-content::-webkit-scrollbar-track {
                background: #F3F4F6;
            }

            .modal-content::-webkit-scrollbar-thumb {
                background: #E75480;
                border-radius: 10px;
            }

            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1.5rem;
                padding-bottom: 1rem;
                border-bottom: 3px solid #E75480;
            }

            .modal-title {
                font-size: 1.8rem;
                font-weight: 800;
                background: linear-gradient(90deg, #E75480 0%, #FF6B95 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            .detail-section {
                background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%);
                padding: 1.2rem;
                border-radius: 12px;
                margin: 1rem 0;
                border-left: 4px solid #E75480;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }

            .detail-section h4 {
                color: #E75480;
                margin: 0 0 1rem 0;
                font-size: 1.2rem;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .detail-row {
                display: flex;
                justify-content: space-between;
                padding: 0.6rem 0;
                border-bottom: 1px solid #E2E8F0;
                transition: all 0.2s ease;
            }

            .detail-row:hover {
                background: #F9E0E8;
                padding-left: 0.5rem;
                padding-right: 0.5rem;
                border-radius: 6px;
            }

            .detail-row:last-child {
                border-bottom: none;
            }

            .detail-label {
                font-weight: 600;
                color: #4B5563;
                flex: 1;
            }

            .detail-value {
                color: #1F2937;
                font-weight: 500;
                flex: 2;
                text-align: right;
            }

            /* ===== SIDEBAR CONTENT ===== */
            .sidebar-title {
                color: var(--repetto-pink);
                font-size: 1.8rem;
                font-weight: 800;
                margin-bottom: 0.5rem;
                text-align: center;
            }

            .sidebar-subtitle {
                color: var(--repetto-dark);
                opacity: 0.7;
                text-align: center;
                margin-bottom: 2rem;
                font-size: 0.9rem;
            }

            /* ===== PROGRESS BAR ===== */
            .stProgress > div > div > div > div {
                background: linear-gradient(90deg, var(--repetto-pink) 0%, #FF6B95 100%);
                border-radius: 10px;
            }

            /* ===== FOOTER ===== */
            .footer {
                margin-top: 3rem;
                padding-top: 1.5rem;
                border-top: 1px solid var(--repetto-gray);
                color: var(--repetto-dark);
                opacity: 0.6;
                font-size: 0.85rem;
                text-align: center;
            }

            /* ===== RESPONSIVE ===== */
            @media (max-width: 1400px) {
                .data-table th, .data-table td {
                    padding: 10px 8px;
                    font-size: 0.8rem;
                }

                .status-cell {
                    font-size: 0.75rem;
                    padding: 5px 10px;
                    min-width: 80px;
                }

                .time-cell, .pause-cell {
                    font-size: 0.75rem;
                    padding: 6px 10px !important;
                    min-width: 70px;
                }
            }

            @media (max-width: 1200px) {
                .main-header {
                    font-size: 2rem;
                }

                .modal-content {
                    margin: 1rem;
                    padding: 1.5rem;
                }

                .metric-value {
                    font-size: 1.8rem;
                }
            }

            @media (max-width: 768px) {
                .data-table {
                    min-width: 1000px;
                }

                .section-header {
                    font-size: 1.3rem;
                }
            }

            /* ===== CUSTOM STREAMLIT ELEMENTS ===== */
            .stDataFrame {
                border-radius: 12px;
                overflow: hidden;
            }

            /* Info boxes */
            .stInfo, .stSuccess, .stWarning, .stError {
                border-radius: 10px;
                padding: 1rem;
            }

            /* Expander */
            .streamlit-expanderHeader {
                background: white;
                border-radius: 10px;
                font-weight: 600;
            }

            /* Metrics */
            [data-testid="stMetricValue"] {
                font-size: 2rem;
                font-weight: 800;
            }
        </style>
        """, unsafe_allow_html=True)

    def run(self):
        """Exécute l'application"""
        # Initialiser la base de données
        if not st.session_state.db_initialized:
            with st.spinner("🔧 Initialisation du système..."):
                if self.db_manager.init_database():
                    st.session_state.db_initialized = True

        # Vérifier la connexion
        if not st.session_state.logged_in:
            login_page = LoginPage(self.db_manager)
            login_page.render()
        else:
            # Afficher la sidebar pour le directeur
            if st.session_state.user_role == "Chef de Production":
                sidebar_manager = SidebarManager(self.db_manager)
                sidebar_manager.display()

            # Header principal
            col_header1, col_header2, col_header3 = st.columns([4, 1, 1])

            with col_header1:
                user_role_display = {
                    "Chef de Coupe": "👨‍🔧 Chef de Coupe",
                    "Contrôle Qualité": "👌 Contrôle Qualité",
                    "Chef de Production": "📈 Directeur Production",
                    "Chef de Piqûre": "🪡 Chef de Piqûre"  # ← NOUVEAU
                }.get(st.session_state.user_role, st.session_state.user_role)

                st.markdown(f'<h1 style="margin: 0; color: #1F2937;">{user_role_display}</h1>', unsafe_allow_html=True)
                st.markdown(f'<p style="margin: 0; color: #6B7280;">{st.session_state.user_name} • Session Active</p>',
                            unsafe_allow_html=True)

            with col_header2:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: #10B981; border-radius: 10px; color: white;">
                    <div style="font-size: 0.9rem;">🔗 Connecté</div>
                    <div style="font-size: 0.8rem;">MySQL</div>
                </div>
                """, unsafe_allow_html=True)

            with col_header3:
                if st.button("🚪 Déconnexion", width='stretch', type="primary"):
                    st.session_state.logged_in = False
                    st.session_state.user_role = None
                    st.session_state.user_name = None
                    st.rerun()

            st.markdown("---")

            # Afficher la page appropriée
            # Afficher la page appropriée
            if st.session_state.user_role == "Chef de Coupe":
                chef_coupe_page = ChefCoupePage(self.db_manager)
                chef_coupe_page.render()
            elif st.session_state.user_role == "Contrôle Qualité":
                controle_page = ControleQualitePage(self.db_manager)
                controle_page.render()
            elif st.session_state.user_role == "Chef de Production":
                directeur_page = DirecteurPage(self.db_manager)
                directeur_page.render()
            elif st.session_state.user_role == "Chef de Piqûre":  # ← NOUVEAU
                chef_piqure_page = ChefPiqurePage(self.db_manager)
                chef_piqure_page.render()
            else:
                st.error("⚠️ Rôle non reconnu!")


# ==================== EXÉCUTION ====================

if __name__ == "__main__":
    app = App()
    app.run()