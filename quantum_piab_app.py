"""
Comprehensive Quantum Particle in a Box (PIAB) Streamlit Application
=====================================================================
Features:
- Wave function and probability density visualization
- Energy level calculations
- Probability in spatial regions
- Expectation values and Heisenberg uncertainty principle
- Time evolution (stationary & superposition states)
- Molecular orbital analogy (HOMO-LUMO analysis)
- Data export to CSV

Author: Quantum Mechanics Toolbox
Date: 2025

FIXED: Removed openpyxl dependency to avoid installation errors
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.integrate import quad
import warnings
import json
from io import StringIO

# Configure settings
warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Page config
st.set_page_config(
    page_title="Quantum PIAB Explorer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Physical constants (atomic units)
HBAR = 1.0  # Reduced Planck constant
MASS = 1.0  # Particle mass

# ============================================================================
# CORE QUANTUM MECHANICS FUNCTIONS
# ============================================================================

@st.cache_data
def calculate_energy(n, L=1.0, factor=1.0):
    """Calculate energy eigenvalue E_n for particle in a box."""
    if n < 1:
        raise ValueError("Quantum number n must be >= 1")
    return factor * (n**2) / (L**2)


@st.cache_data
def calculate_wavefunction(x, n, L=1.0):
    """Calculate normalized wave function ψ_n(x)."""
    x = np.asarray(x)
    psi = np.zeros_like(x, dtype=float)
    mask = (x >= 0) & (x <= L)
    psi[mask] = np.sqrt(2/L) * np.sin(n * np.pi * x[mask] / L)
    return psi


@st.cache_data
def calculate_probability_density(x, n, L=1.0):
    """Calculate probability density |ψ_n(x)|²."""
    psi = calculate_wavefunction(x, n, L)
    return psi**2


def calculate_probability_in_region(n, L, x1, x2):
    """Calculate probability of finding particle in region [x1, x2]."""
    if not (0 <= x1 < x2 <= L):
        raise ValueError(f"Region [{x1}, {x2}] must be within [0, {L}]")
    
    def integrand(x):
        psi_at_x = np.sqrt(2/L) * np.sin(n * np.pi * x / L)
        return psi_at_x**2
    
    probability, error = quad(integrand, x1, x2)
    return probability, error


def calculate_expectation_values(n, L=1.0):
    """Calculate expectation values and uncertainties."""
    def integrand_x(x):
        psi = np.sqrt(2/L) * np.sin(n * np.pi * x / L)
        return x * psi**2
    
    def integrand_x2(x):
        psi = np.sqrt(2/L) * np.sin(n * np.pi * x / L)
        return x**2 * psi**2
    
    expectation_x, _ = quad(integrand_x, 0, L)
    expectation_x2, _ = quad(integrand_x2, 0, L)
    
    delta_x = np.sqrt(expectation_x2 - expectation_x**2)
    delta_p = n * np.pi * HBAR / L
    uncertainty_product = delta_x * delta_p
    heisenberg_limit = HBAR / 2
    expectation_E = calculate_energy(n, L)
    
    return {
        'expectation_x': expectation_x,
        'expectation_x2': expectation_x2,
        'delta_x': delta_x,
        'delta_p': delta_p,
        'uncertainty_product': uncertainty_product,
        'heisenberg_limit': heisenberg_limit,
        'expectation_E': expectation_E,
        'satisfies_heisenberg': uncertainty_product >= heisenberg_limit
    }


def analyze_homo_lumo(num_carbons, bond_length_angstrom=1.4):
    """Analyze HOMO-LUMO gap for conjugated polyene."""
    h = 6.626e-34
    c = 3.0e8
    me = 9.109e-31
    eV_to_J = 1.602e-19
    angstrom_to_m = 1e-10
    
    L_angstrom = (num_carbons - 1) * bond_length_angstrom
    L_m = L_angstrom * angstrom_to_m
    num_pi_electrons = num_carbons
    
    n_HOMO = int(np.ceil(num_pi_electrons / 2))
    n_LUMO = n_HOMO + 1
    
    E_HOMO_J = (n_HOMO**2 * h**2) / (8 * me * L_m**2)
    E_LUMO_J = (n_LUMO**2 * h**2) / (8 * me * L_m**2)
    
    gap_J = E_LUMO_J - E_HOMO_J
    gap_eV = gap_J / eV_to_J
    
    lambda_m = (h * c) / gap_J
    lambda_nm = lambda_m * 1e9
    
    if lambda_nm < 400:
        color_region = "UV (colorless)"
    elif 400 <= lambda_nm < 495:
        color_region = "Blue region"
    elif 495 <= lambda_nm < 570:
        color_region = "Green region"
    elif 570 <= lambda_nm < 620:
        color_region = "Yellow-Orange region"
    elif 620 <= lambda_nm < 750:
        color_region = "Red region"
    else:
        color_region = "Infrared (colorless)"
    
    return {
        'L_angstrom': L_angstrom,
        'n_HOMO': n_HOMO,
        'n_LUMO': n_LUMO,
        'E_HOMO_eV': E_HOMO_J / eV_to_J,
        'E_LUMO_eV': E_LUMO_J / eV_to_J,
        'gap_eV': gap_eV,
        'lambda_nm': lambda_nm,
        'color_region': color_region
    }


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def plot_piab(n, L=1.0, num_points=500):
    """Create side-by-side visualization of wavefunction and probability density."""
    x = np.linspace(0, L, num_points)
    psi_n = calculate_wavefunction(x, n, L)
    prob_density = calculate_probability_density(x, n, L)
    E_n = calculate_energy(n, L)
    
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f'Quantum State n = {n} | Energy E₍ₙ₎ = {E_n:.4f} a.u.', 
                 fontsize=14, fontweight='bold')
    
    # Left plot: Wave function
    ax[0].plot(x, psi_n, linewidth=2.5, color='#2E86DE', label=r'$\psi_n(x)$')
    ax[0].axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax[0].axvline(0, color='black', linestyle=':', linewidth=1.5)
    ax[0].axvline(L, color='black', linestyle=':', linewidth=1.5)
    ax[0].fill_between(x, psi_n, alpha=0.2, color='#2E86DE')
    ax[0].set_title(r'Wave Function $\psi_n(x)$', fontsize=12, fontweight='bold')
    ax[0].set_xlabel('Position x (a.u.)')
    ax[0].set_ylabel('Amplitude')
    ax[0].grid(True, alpha=0.3)
    ax[0].legend()
    
    # Right plot: Probability density
    ax[1].plot(x, prob_density, linewidth=2.5, color='#EE5A6F', label=r'$|\psi_n(x)|^2$')
    ax[1].axvline(0, color='black', linestyle=':', linewidth=1.5)
    ax[1].axvline(L, color='black', linestyle=':', linewidth=1.5)
    ax[1].fill_between(x, prob_density, color='#EE5A6F', alpha=0.3)
    ax[1].set_title(r'Probability Density $|\psi_n(x)|^2$', fontsize=12, fontweight='bold')
    ax[1].set_xlabel('Position x (a.u.)')
    ax[1].set_ylabel('Probability Density (a.u.⁻¹)')
    ax[1].grid(True, alpha=0.3)
    ax[1].legend()
    
    plt.tight_layout()
    return fig


def plot_multiple_states(n_values, L=1.0):
    """Plot multiple quantum states."""
    x = np.linspace(0, L, 500)
    
    fig, axes = plt.subplots(2, len(n_values), figsize=(15, 8))
    fig.suptitle('Wave Functions and Probability Densities for Multiple States', 
                 fontsize=14, fontweight='bold')
    
    for idx, n in enumerate(n_values):
        psi = calculate_wavefunction(x, n, L)
        prob = calculate_probability_density(x, n, L)
        E = calculate_energy(n, L)
        
        # Wavefunction
        axes[0, idx].plot(x, psi, linewidth=2, color='#2E86DE')
        axes[0, idx].fill_between(x, psi, alpha=0.2, color='#2E86DE')
        axes[0, idx].set_title(f'n={n}, E={E:.2f}', fontweight='bold')
        axes[0, idx].set_ylabel('ψ(x)')
        axes[0, idx].grid(True, alpha=0.3)
        axes[0, idx].axhline(0, color='gray', linestyle='--', alpha=0.5)
        
        # Probability density
        axes[1, idx].plot(x, prob, linewidth=2, color='#EE5A6F')
        axes[1, idx].fill_between(x, prob, alpha=0.3, color='#EE5A6F')
        axes[1, idx].set_xlabel('Position x')
        axes[1, idx].set_ylabel('|ψ(x)|²')
        axes[1, idx].grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_energy_levels(n_max, L=1.0):
    """Plot energy level diagram."""
    n_values = np.arange(1, n_max + 1)
    energies = [calculate_energy(n, L) for n in n_values]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(n_values)))
    
    for i, (n, E) in enumerate(zip(n_values, energies)):
        ax.hlines(E, 0, 1, colors=colors[i], linewidth=3, label=f'n={n}, E={E:.2f}')
        ax.text(1.05, E, f'n={n}\nE={E:.2f}', va='center', fontsize=10, fontweight='bold')
    
    ax.set_xlim(-0.1, 1.5)
    ax.set_ylim(0, max(energies) * 1.1)
    ax.set_ylabel('Energy (a.u.)', fontsize=12, fontweight='bold')
    ax.set_title(f'Energy Level Diagram (L = {L} a.u.)', fontsize=14, fontweight='bold')
    ax.set_xticks([])
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    return fig


def plot_probability_region(n, L, x1, x2):
    """Visualize probability density with highlighted region."""
    probability, error = calculate_probability_in_region(n, L, x1, x2)
    
    x = np.linspace(0, L, 500)
    prob_density = calculate_probability_density(x, n, L)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(x, prob_density, linewidth=2.5, color='#2E86DE', label=r'$|\psi_n(x)|^2$ (full)')
    
    x_region = x[(x >= x1) & (x <= x2)]
    prob_region = prob_density[(x >= x1) & (x <= x2)]
    ax.fill_between(x_region, prob_region, color='#10AC84', alpha=0.6, 
                    label=f'Region [{x1:.3f}, {x2:.3f}]\nP = {probability:.4f}')
    
    ax.axvline(x1, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax.axvline(x2, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax.axvline(0, color='black', linestyle=':', linewidth=1.5)
    ax.axvline(L, color='black', linestyle=':', linewidth=1.5)
    
    ax.set_title(f'Probability in Region [{x1:.3f}, {x2:.3f}] | n = {n} | P = {probability:.4f} ({probability*100:.2f}%)', 
                fontsize=13, fontweight='bold')
    ax.set_xlabel('Position x (a.u.)')
    ax.set_ylabel('Probability Density (a.u.⁻¹)')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    
    plt.tight_layout()
    return fig


def plot_time_evolution(n1, n2, L=1.0, t_max=10.0):
    """Visualize time evolution for superposition state."""
    x = np.linspace(0, L, 500)
    E1 = calculate_energy(n1, L)
    E2 = calculate_energy(n2, L)
    omega = (E2 - E1) / HBAR
    period = 2 * np.pi / omega if omega != 0 else float('inf')
    
    snapshot_times = np.linspace(0, min(t_max, 2*period) if period != float('inf') else t_max, 6)
    
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle(f'Time Evolution of Superposition State (n={n1} + n={n2})', 
                fontsize=14, fontweight='bold')
    
    for idx, t in enumerate(snapshot_times):
        row = idx // 3
        col = idx % 3
        ax = axes[row, col]
        
        psi1 = calculate_wavefunction(x, n1, L)
        psi2 = calculate_wavefunction(x, n2, L)
        
        phase1 = np.exp(-1j * E1 * t / HBAR)
        phase2 = np.exp(-1j * E2 * t / HBAR)
        psi_t = (psi1 * phase1 + psi2 * phase2) / np.sqrt(2)
        
        prob_t = np.abs(psi_t)**2
        
        ax.plot(x, prob_t, linewidth=2, color='#2E86DE')
        ax.fill_between(x, prob_t, alpha=0.3, color='#2E86DE')
        ax.set_title(f't = {t:.3f} a.u. ({t/period*100:.1f}% of period)' 
                    if period != float('inf') else f't = {t:.3f} a.u.', 
                    fontsize=11, fontweight='bold')
        ax.set_xlabel('Position x')
        ax.set_ylabel('|Ψ(x,t)|²')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, L)
        ax.set_ylim(0, None)
    
    plt.tight_layout()
    return fig


def plot_homo_lumo_trend(max_carbons=20):
    """Plot HOMO-LUMO gap vs conjugation length."""
    carbon_counts = np.arange(2, max_carbons + 1)
    gaps_eV = []
    wavelengths = []
    
    for num_c in carbon_counts:
        result = analyze_homo_lumo(num_c)
        gaps_eV.append(result['gap_eV'])
        wavelengths.append(result['lambda_nm'])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # HOMO-LUMO gap vs number of carbons
    ax1.plot(carbon_counts, gaps_eV, 'o-', linewidth=2.5, markersize=8, color='#2E86DE')
    ax1.set_xlabel('Number of Carbon Atoms', fontsize=12, fontweight='bold')
    ax1.set_ylabel('HOMO-LUMO Gap (eV)', fontsize=12, fontweight='bold')
    ax1.set_title('HOMO-LUMO Gap vs Conjugation Length', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Absorption wavelength vs number of carbons
    ax2.plot(carbon_counts, wavelengths, 's-', linewidth=2.5, markersize=8, color='#EE5A6F')
    ax2.axhline(400, color='purple', linestyle='--', alpha=0.5, label='UV-Visible boundary')
    ax2.axhline(750, color='red', linestyle='--', alpha=0.5, label='Visible-IR boundary')
    ax2.set_xlabel('Number of Carbon Atoms', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Absorption Wavelength (nm)', fontsize=12, fontweight='bold')
    ax2.set_title('Predicted Absorption Wavelength', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    return fig


# ============================================================================
# STREAMLIT APP LAYOUT
# ============================================================================

st.title("🔬 Quantum Particle in a Box Explorer")
st.markdown("**A comprehensive interactive tool for understanding quantum mechanics**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    app_mode = st.radio(
        "Select Mode:",
        [
            "📊 Wave Function & Probability",
            "⚡ Energy Levels",
            "🎯 Probability in Region",
            "📐 Expectation Values",
            "⏱️ Time Evolution",
            "🧪 Molecular Orbital Analysis",
            "📥 Data Export"
        ]
    )
    
    st.divider()
    
    # Common parameters
    L = st.slider("Box Length (a.u.)", min_value=0.5, max_value=5.0, value=1.0, step=0.1)
    num_points = st.slider("Number of Points", min_value=100, max_value=1000, value=500, step=50)

# ============================================================================
# MODE 1: WAVE FUNCTION & PROBABILITY
# ============================================================================

if app_mode == "📊 Wave Function & Probability":
    st.header("Wave Function and Probability Density Visualization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        n = st.slider("Quantum Number (n)", min_value=1, max_value=10, value=1)
        view_type = st.radio("View Type:", ["Single State", "Multiple States"])
    
    with col2:
        st.info(
            f"**Quantum State Information**\n\n"
            f"• Quantum Number: n = {n}\n"
            f"• Energy: E = {calculate_energy(n, L):.4f} a.u.\n"
            f"• Number of Nodes: {n-1}\n"
            f"• Wavelength: λ = {2*L/n:.4f} a.u."
        )
    
    if view_type == "Single State":
        fig = plot_piab(n, L, num_points)
        st.pyplot(fig)
        
        # Display detailed information
        col1, col2, col3 = st.columns(3)
        
        with col1:
            x_test = np.linspace(0, L, 5)
            psi_vals = calculate_wavefunction(x_test, n, L)
            st.subheader("Wave Function Values")
            df_psi = pd.DataFrame({
                'Position x': x_test,
                'ψ(x)': psi_vals
            })
            st.dataframe(df_psi, use_container_width=True)
        
        with col2:
            prob_vals = calculate_probability_density(x_test, n, L)
            st.subheader("Probability Density Values")
            df_prob = pd.DataFrame({
                'Position x': x_test,
                '|ψ(x)|²': prob_vals
            })
            st.dataframe(df_prob, use_container_width=True)
        
        with col3:
            st.subheader("Normalization Check")
            x_grid = np.linspace(0, L, 1000)
            prob_density = calculate_probability_density(x_grid, n, L)
            norm = np.trapz(prob_density, x_grid)
            
            st.metric("∫|ψ|²dx", f"{norm:.6f}", 
                     delta=f"{abs(norm - 1.0):.2e}" if abs(norm - 1.0) > 1e-4 else "✓ Normalized")
    
    else:  # Multiple States
        n_values = st.multiselect("Select Quantum Numbers:", 
                                  options=range(1, 11), 
                                  default=[1, 2, 3])
        
        if n_values:
            fig = plot_multiple_states(n_values, L)
            st.pyplot(fig)

# ============================================================================
# MODE 2: ENERGY LEVELS
# ============================================================================

elif app_mode == "⚡ Energy Levels":
    st.header("Energy Level Diagram")
    
    col1, col2 = st.columns(2)
    
    with col1:
        n_max = st.slider("Maximum Quantum Number", min_value=3, max_value=20, value=10)
    
    with col2:
        st.info(
            f"**Energy Formula**\n\n"
            f"E_n = n² / L² (atomic units)\n\n"
            f"where L = {L:.2f} a.u."
        )
    
    fig = plot_energy_levels(n_max, L)
    st.pyplot(fig)
    
    # Energy table
    st.subheader("Energy Values")
    energy_data = []
    for n in range(1, n_max + 1):
        E = calculate_energy(n, L)
        energy_data.append({
            'Quantum Number (n)': n,
            'Energy (E_n)': f"{E:.6f} a.u.",
            'Energy Ratio': f"{E:.2f} × E₁"
        })
    
    df_energies = pd.DataFrame(energy_data)
    st.dataframe(df_energies, use_container_width=True)

# ============================================================================
# MODE 3: PROBABILITY IN REGION
# ============================================================================

elif app_mode == "🎯 Probability in Region":
    st.header("Calculate Probability in Spatial Region")
    
    col1, col2 = st.columns(2)
    
    with col1:
        n = st.slider("Quantum Number (n)", min_value=1, max_value=10, value=2)
    
    with col2:
        st.info(f"Box boundaries: [0, {L}]")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        x1 = st.number_input("Start Position (x₁)", min_value=0.0, max_value=L*0.99, 
                            value=L*0.25, step=L*0.05)
    
    with col2:
        x2 = st.number_input("End Position (x₂)", min_value=x1+0.01, max_value=L, 
                            value=L*0.75, step=L*0.05)
    
    with col3:
        st.info(
            f"**Region Information**\n\n"
            f"• Region: [{x1:.4f}, {x2:.4f}]\n"
            f"• Width: {x2-x1:.4f} a.u.\n"
            f"• Percentage of box: {(x2-x1)/L*100:.1f}%"
        )
    
    try:
        probability, error = calculate_probability_in_region(n, L, x1, x2)
        
        fig = plot_probability_region(n, L, x1, x2)
        st.pyplot(fig)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Probability", f"{probability:.6f}", f"({probability*100:.4f}%)")
        
        with col2:
            st.metric("Integration Error", f"{error:.2e}")
        
        with col3:
            st.metric("Odds", f"1 in {1/probability:.1f}" if probability > 0 else "∞")
    
    except ValueError as e:
        st.error(str(e))

# ============================================================================
# MODE 4: EXPECTATION VALUES
# ============================================================================

elif app_mode == "📐 Expectation Values":
    st.header("Expectation Values & Heisenberg Uncertainty")
    
    n = st.slider("Quantum Number (n)", min_value=1, max_value=10, value=1)
    
    results = calculate_expectation_values(n, L)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 Position Statistics")
        st.metric("⟨x⟩ (Average Position)", f"{results['expectation_x']:.6f} a.u.")
        st.metric("⟨x²⟩", f"{results['expectation_x2']:.6f} a.u.²")
        st.metric("Δx (Position Uncertainty)", f"{results['delta_x']:.6f} a.u.")
    
    with col2:
        st.subheader("🚀 Momentum Statistics")
        st.metric("⟨p⟩ (Average Momentum)", f"0.000000 a.u. (symmetry)")
        st.metric("Δp (Momentum Uncertainty)", f"{results['delta_p']:.6f} a.u.")
        st.metric("⟨E⟩ (Energy)", f"{results['expectation_E']:.6f} a.u.")
    
    st.divider()
    
    st.subheader("🔬 Heisenberg Uncertainty Principle")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Δx × Δp", f"{results['uncertainty_product']:.6f}")
    
    with col2:
        st.metric("Minimum (ℏ/2)", f"{results['heisenberg_limit']:.6f}")
    
    with col3:
        ratio = results['uncertainty_product'] / results['heisenberg_limit']
        st.metric("Ratio", f"{ratio:.4f}")
    
    if results['satisfies_heisenberg']:
        st.success("✅ Heisenberg Uncertainty Principle SATISFIED!")
    else:
        st.error("❌ Heisenberg principle violated (check calculation)")
    
    # Visualization
    fig, ax = plt.subplots(figsize=(12, 6))
    
    labels = ['Δx', 'Δp', 'Δx·Δp', 'ℏ/2']
    values = [results['delta_x'], results['delta_p'], 
             results['uncertainty_product'], results['heisenberg_limit']]
    colors = ['#2E86DE', '#EE5A6F', '#10AC84', '#FFB627']
    
    bars = ax.bar(labels, values, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{val:.4f}', ha='center', va='bottom', fontweight='bold')
    
    ax.set_ylabel('Value (a.u.)', fontweight='bold')
    ax.set_title(f'Uncertainty Analysis for n={n}, L={L}', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    st.pyplot(fig)

# ============================================================================
# MODE 5: TIME EVOLUTION
# ============================================================================

elif app_mode == "⏱️ Time Evolution":
    st.header("Time Evolution of Quantum States")
    
    col1, col2 = st.columns(2)
    
    with col1:
        state_type = st.radio("State Type:", ["Eigenstate (Stationary)", "Superposition"])
    
    if state_type == "Eigenstate (Stationary)":
        n = st.slider("Quantum Number (n)", min_value=1, max_value=10, value=1)
        
        st.info(
            "**Eigenstate Properties**\n\n"
            "• Probability density is **TIME-INDEPENDENT**\n"
            "• |Ψ(x,t)|² = |ψ(x)|² (constant in time)\n"
            "• No visible time evolution\n"
            "• This is a **stationary state**"
        )
        
        x = np.linspace(0, L, 500)
        prob = calculate_probability_density(x, n, L)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(x, prob, linewidth=2.5, color='#EE5A6F')
        ax.fill_between(x, prob, alpha=0.3, color='#EE5A6F')
        ax.set_title(f'Stationary State: n = {n} (No Time Evolution)', 
                    fontsize=13, fontweight='bold')
        ax.set_xlabel('Position x (a.u.)')
        ax.set_ylabel('Probability Density')
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    else:  # Superposition
        col1, col2 = st.columns(2)
        
        with col1:
            n1 = st.slider("First Quantum Number (n₁)", min_value=1, max_value=10, value=1)
        
        with col2:
            n2 = st.slider("Second Quantum Number (n₂)", min_value=1, max_value=10, value=2)
        
        if n1 == n2:
            st.warning("n₁ and n₂ must be different for interesting dynamics!")
        else:
            E1 = calculate_energy(n1, L)
            E2 = calculate_energy(n2, L)
            omega = (E2 - E1) / HBAR
            period = 2 * np.pi / omega
            
            st.info(
                f"**Superposition Properties**\n\n"
                f"• Energy difference: ΔE = {E2-E1:.6f} a.u.\n"
                f"• Oscillation frequency: ω = {omega:.6f} rad/a.u.\n"
                f"• Oscillation period: T = {period:.6f} a.u.\n"
                f"• Observable: Quantum interference pattern!"
            )
            
            t_max_slider = st.slider("Maximum Time", min_value=period, max_value=5*period, value=2*period)
            
            fig = plot_time_evolution(n1, n2, L, t_max_slider)
            st.pyplot(fig)

# ============================================================================
# MODE 6: MOLECULAR ORBITAL ANALYSIS
# ============================================================================

elif app_mode == "🧪 Molecular Orbital Analysis":
    st.header("HOMO-LUMO Analysis for Conjugated Molecules")
    
    st.markdown("""
    The 1D Particle in a Box model provides insights into the electronic structure
    of conjugated organic molecules (polyenes) where π-electrons are delocalized
    across a chain of carbon atoms.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_carbons = st.slider("Number of Carbon Atoms", min_value=2, max_value=20, value=6)
        bond_length = st.number_input("C-C Bond Length (Å)", min_value=1.0, max_value=2.0, 
                                     value=1.4, step=0.1)
    
    with col2:
        st.info(
            "**Real Examples**\n\n"
            "• Ethylene (C₂): Colorless\n"
            "• Butadiene (C₄): Colorless\n"
            "• Hexatriene (C₆): Slightly yellow\n"
            "• β-Carotene (C₄₀): Orange 🥕"
        )
    
    result = analyze_homo_lumo(num_carbons, bond_length)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Chain Length", f"{result['L_angstrom']:.2f} Å")
    
    with col2:
        st.metric("HOMO-LUMO Gap", f"{result['gap_eV']:.4f} eV")
    
    with col3:
        st.metric("Absorption λ", f"{result['lambda_nm']:.1f} nm")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Molecular Orbital Energies")
        
        mo_data = {
            'Orbital': [f"ψ_{i}" for i in range(1, num_carbons + 1)],
            'Quantum #': list(range(1, num_carbons + 1)),
            'Type': ['HOMO' if i == result['n_HOMO'] else 
                    'LUMO' if i == result['n_LUMO'] else 
                    'Filled' if i < result['n_HOMO'] else 'Empty' 
                    for i in range(1, num_carbons + 1)],
            'Occupation': ['↑↓' if i < result['n_HOMO'] else 
                          '↑' if i == result['n_HOMO'] else '—' 
                          for i in range(1, num_carbons + 1)]
        }
        
        df_mo = pd.DataFrame(mo_data)
        st.dataframe(df_mo, use_container_width=True)
    
    with col2:
        st.subheader("UV-Vis Spectroscopy")
        
        spec_data = {
            'Property': ['HOMO Energy', 'LUMO Energy', 'Gap (ΔE)', 'Wavelength (λ)', 'Spectral Region'],
            'Value': [f"{result['E_HOMO_eV']:.4f} eV",
                     f"{result['E_LUMO_eV']:.4f} eV",
                     f"{result['gap_eV']:.4f} eV",
                     f"{result['lambda_nm']:.1f} nm",
                     result['color_region']]
        }
        
        df_spec = pd.DataFrame(spec_data)
        st.dataframe(df_spec, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Trend analysis
    st.subheader("Trend Analysis: Conjugation vs Absorption")
    
    fig = plot_homo_lumo_trend(15)
    st.pyplot(fig)
    
    # Chemistry insights
    with st.expander("🧬 Chemistry Insights"):
        st.markdown("""
        ### Why Longer Conjugation Means More Color
        
        1. **Box Length Effect**: As conjugation length increases, the effective "box" gets longer
        
        2. **Energy Levels Drop**: E_n ∝ n²/L². Larger L means lower energy levels
        
        3. **Gap Shrinks**: HOMO-LUMO gap decreases as chain length increases
        
        4. **Wavelength Redshifts**: 
           - λ = hc/ΔE
           - Smaller gap → larger wavelength
           - Visible light absorption becomes possible
        
        5. **Color Emerges**:
           - UV absorption → colorless
           - Blue absorption → yellow appearance
           - Green absorption → magenta appearance
           - Red absorption → cyan appearance
        
        ### Real Example: β-Carotene
        - Structure: 11 conjugated double bonds (C₄₀)
        - Absorbs blue-green light (~450-500 nm)
        - Appears **orange** (complementary color) 🥕
        - Why carrots are orange!
        """)

# ============================================================================
# MODE 7: DATA EXPORT
# ============================================================================

elif app_mode == "📥 Data Export":
    st.header("Export Quantum State Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        n = st.slider("Quantum Number (n)", min_value=1, max_value=10, value=1)
        export_type = st.radio("Export Type:", ["CSV", "JSON"])
    
    with col2:
        st.info(
            f"**Export Information**\n\n"
            f"• Quantum Number: n = {n}\n"
            f"• Box Length: L = {L} a.u.\n"
            f"• Data Points: {num_points}\n"
            f"• Energy: {calculate_energy(n, L):.4f} a.u."
        )
    
    # Generate data
    x = np.linspace(0, L, num_points)
    psi = calculate_wavefunction(x, n, L)
    prob = calculate_probability_density(x, n, L)
    
    df = pd.DataFrame({
        'position_x': x,
        'wavefunction_psi': psi,
        'probability_density': prob
    })
    
    st.subheader("Preview of Data")
    st.dataframe(df.head(10), use_container_width=True)
    
    st.info(f"Total rows: {len(df)}")
    
    if export_type == "CSV":
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"quantum_state_n{n}_L{L:.1f}.csv",
            mime="text/csv"
        )
    
    elif export_type == "JSON":
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name=f"quantum_state_n{n}_L{L:.1f}.json",
            mime="application/json"
        )
    
    st.divider()
    
    # Statistics
    st.subheader("Data Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Max ψ", f"{psi.max():.6f}")
    
    with col2:
        st.metric("Max |ψ|²", f"{prob.max():.6f}")
    
    with col3:
        st.metric("∫|ψ|²dx", f"{np.trapz(prob, x):.6f}")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()

st.markdown("""
---
**Quantum Particle in a Box Explorer** 🔬

A comprehensive interactive tool for understanding quantum mechanics through:
- Wave function visualization
- Energy level diagrams
- Probability calculations
- Heisenberg uncertainty principle
- Time evolution dynamics
- Molecular orbital theory connections
- Data export capabilities

**Physical Constants (Atomic Units):**
- ℏ = 1.0 (Reduced Planck constant)
- m = 1.0 (Particle mass)

**Made with ❤️ for quantum learning**
""")
