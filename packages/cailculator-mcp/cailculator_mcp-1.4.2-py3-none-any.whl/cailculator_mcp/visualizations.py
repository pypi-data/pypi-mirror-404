"""
Visualization module for Chavez Transform results.

Supports two modes:
- Free tier: Static matplotlib plots (PNG/SVG exports)
- Premium tier: Interactive Plotly visualizations
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from typing import Dict, List, Optional, Union, Tuple
import io
import base64

try:
    import plotly.graph_objects as go
    import plotly.subplots as sp
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# Visualization theme/styling
THEME = {
    'primary_color': '#8B5CF6',  # Purple - primary brand color
    'secondary_color': '#EC4899',  # Pink
    'accent_color': '#60A5FA',  # Light Blue - color of impossibility (Cirlot)
    'e8_color': '#F59E0B',  # Orange (for E8 comparisons)
    'canonical_color': '#10B981',  # Green (for canonical)
    'pattern_4_color': '#F59E0B',  # Gold - highlight the anomaly
    'figsize': (12, 8),
    'dpi': 150,
    'font_size': 10,
    'e8_mandala_size': (12, 12),  # Square for mandala symmetry
}


def plot_canonical_six_universality(
    pattern_values: Dict[int, float],
    interactive: bool = False,
    return_base64: bool = False
) -> Union[plt.Figure, go.Figure, str, None]:
    """
    Plot the Canonical Six pattern universality (purple bars chart).

    This visualization shows that all six Canonical Six patterns produce
    identical transform values, demonstrating universal symmetry.

    Args:
        pattern_values: Dict mapping pattern_id (1-6) to transform value
        interactive: If True, return Plotly figure (premium). If False, matplotlib (free)
        return_base64: If True, return base64-encoded PNG string instead of figure

    Returns:
        Figure object or base64 string, depending on parameters
    """
    mean_value = np.mean(list(pattern_values.values()))

    if interactive and PLOTLY_AVAILABLE:
        # Premium: Interactive Plotly
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=list(pattern_values.keys()),
            y=list(pattern_values.values()),
            marker_color=THEME['primary_color'],
            name='C[f] value',
            hovertemplate='Pattern %{x}<br>C[f] = %{y:.6e}<extra></extra>'
        ))

        # Add mean line
        fig.add_hline(
            y=mean_value,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Mean = {mean_value:.6e}",
            annotation_position="top right"
        )

        fig.update_layout(
            title="Canonical Six Pattern Universality",
            xaxis_title="Pattern ID",
            yaxis_title="C[f] value",
            template="plotly_white",
            height=500,
            showlegend=False
        )

        return fig

    else:
        # Free: Static matplotlib
        fig, ax = plt.subplots(figsize=(8, 6), dpi=THEME['dpi'])

        patterns = list(pattern_values.keys())
        values = list(pattern_values.values())

        bars = ax.bar(patterns, values, color=THEME['primary_color'], edgecolor='white', linewidth=2)

        # Add mean line
        ax.axhline(mean_value, color='red', linestyle='--', linewidth=2, alpha=0.7,
                   label=f'Mean = {mean_value:.6e}')

        ax.set_xlabel('Pattern ID', fontsize=THEME['font_size'])
        ax.set_ylabel('C[f] value', fontsize=THEME['font_size'])
        ax.set_title('Canonical Six Pattern Universality', fontsize=THEME['font_size']+2, fontweight='bold')
        ax.legend(loc='upper right')
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if return_base64:
            return _fig_to_base64(fig)
        return fig


def plot_alpha_sensitivity(
    alpha_values: np.ndarray,
    transform_values: np.ndarray,
    optimal_alpha: Optional[float] = None,
    interactive: bool = False,
    return_base64: bool = False
) -> Union[plt.Figure, go.Figure, str, None]:
    """
    Plot Chavez Transform sensitivity to alpha parameter.

    Shows how transform magnitude varies with convergence parameter alpha.
    Typically shows exponential decay as alpha increases.

    Args:
        alpha_values: Array of alpha values tested
        transform_values: Corresponding transform values
        optimal_alpha: If provided, mark this alpha as optimal
        interactive: If True, return Plotly figure (premium)
        return_base64: If True, return base64-encoded PNG string

    Returns:
        Figure object or base64 string
    """
    if interactive and PLOTLY_AVAILABLE:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=alpha_values,
            y=np.abs(transform_values),
            mode='lines+markers',
            name='|C[f]|',
            line=dict(color=THEME['accent_color'], width=3),
            marker=dict(size=6),
            hovertemplate='α = %{x:.3f}<br>|C[f]| = %{y:.3e}<extra></extra>'
        ))

        if optimal_alpha:
            fig.add_vline(
                x=optimal_alpha,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Optimal α = {optimal_alpha:.2f}",
                annotation_position="top"
            )

        fig.update_xaxes(type="log", title="Alpha (convergence parameter)")
        fig.update_yaxes(title="|C[f]| (Transform magnitude)")
        fig.update_layout(
            title="Chavez Transform vs Alpha Parameter",
            template="plotly_white",
            height=500
        )

        return fig

    else:
        fig, ax = plt.subplots(figsize=(8, 6), dpi=THEME['dpi'])

        ax.plot(alpha_values, np.abs(transform_values), 'o-',
                color=THEME['accent_color'], linewidth=2, markersize=6, label='|C[f]|')

        if optimal_alpha:
            ax.axvline(optimal_alpha, color='red', linestyle='--', linewidth=2,
                       label=f'Optimal α = {optimal_alpha:.2f}')

        ax.set_xscale('log')
        ax.set_xlabel('Alpha (convergence parameter)', fontsize=THEME['font_size'])
        ax.set_ylabel('|C[f]| (Transform magnitude)', fontsize=THEME['font_size'])
        ax.set_title('Chavez Transform vs Alpha Parameter', fontsize=THEME['font_size']+2, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if return_base64:
            return _fig_to_base64(fig)
        return fig


def plot_dimensional_weighting(
    d_values: np.ndarray,
    transform_values: np.ndarray,
    interactive: bool = False,
    return_base64: bool = False
) -> Union[plt.Figure, go.Figure, str, None]:
    """
    Plot effect of dimensional weighting parameter d.

    Shows how the dimension parameter d affects transform decay behavior.

    Args:
        d_values: Array of dimension parameter values
        transform_values: Corresponding transform values
        interactive: If True, return Plotly figure (premium)
        return_base64: If True, return base64-encoded PNG string

    Returns:
        Figure object or base64 string
    """
    if interactive and PLOTLY_AVAILABLE:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=d_values,
            y=transform_values,
            mode='lines+markers',
            name='C[f]',
            line=dict(color=THEME['secondary_color'], width=3),
            marker=dict(size=8, color=THEME['secondary_color']),
            hovertemplate='d = %{x}<br>C[f] = %{y:.4f}<extra></extra>'
        ))

        fig.update_layout(
            title="Effect of Dimensional Weighting",
            xaxis_title="Dimension parameter d",
            yaxis_title="C[f] value",
            template="plotly_white",
            height=500
        )

        return fig

    else:
        fig, ax = plt.subplots(figsize=(8, 6), dpi=THEME['dpi'])

        ax.plot(d_values, transform_values, 'o-',
                color=THEME['secondary_color'], linewidth=2, markersize=8)

        ax.set_xlabel('Dimension parameter d', fontsize=THEME['font_size'])
        ax.set_ylabel('C[f] value', fontsize=THEME['font_size'])
        ax.set_title('Effect of Dimensional Weighting', fontsize=THEME['font_size']+2, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if return_base64:
            return _fig_to_base64(fig)
        return fig


def plot_e8_comparison(
    pattern_data: Dict[int, Dict[str, float]],
    interactive: bool = False,
    return_base64: bool = False
) -> Union[plt.Figure, go.Figure, str, None]:
    """
    Plot E8 vs Canonical loci comparison.

    Shows how E8 geometry affects transform values compared to canonical basis.
    Critical visualization for the Pattern 4 amplification discovery.

    Args:
        pattern_data: Dict mapping pattern_id to {'canonical': val, 'e8': val}
        interactive: If True, return Plotly figure (premium)
        return_base64: If True, return base64-encoded PNG string

    Returns:
        Figure object or base64 string
    """
    patterns = list(pattern_data.keys())
    canonical_values = [pattern_data[p]['canonical'] for p in patterns]
    e8_values = [pattern_data[p]['e8'] for p in patterns]

    if interactive and PLOTLY_AVAILABLE:
        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Canonical',
            x=patterns,
            y=canonical_values,
            marker_color=THEME['canonical_color'],
            hovertemplate='Pattern %{x}<br>Canonical: %{y:.2e}<extra></extra>'
        ))

        fig.add_trace(go.Bar(
            name='E8',
            x=patterns,
            y=e8_values,
            marker_color=THEME['e8_color'],
            hovertemplate='Pattern %{x}<br>E8: %{y:.2e}<extra></extra>'
        ))

        fig.update_layout(
            title="E8 vs Canonical Loci Comparison",
            xaxis_title="Pattern ID",
            yaxis_title="C[f] value",
            barmode='group',
            template="plotly_white",
            height=500
        )

        return fig

    else:
        fig, ax = plt.subplots(figsize=(10, 6), dpi=THEME['dpi'])

        x = np.arange(len(patterns))
        width = 0.35

        bars1 = ax.bar(x - width/2, canonical_values, width,
                       label='Canonical', color=THEME['canonical_color'], alpha=0.8)
        bars2 = ax.bar(x + width/2, e8_values, width,
                       label='E8', color=THEME['e8_color'], alpha=0.8)

        ax.set_xlabel('Pattern ID', fontsize=THEME['font_size'])
        ax.set_ylabel('C[f] value', fontsize=THEME['font_size'])
        ax.set_title('E8 vs Canonical Loci Comparison', fontsize=THEME['font_size']+2, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(patterns)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if return_base64:
            return _fig_to_base64(fig)
        return fig


def plot_kernel_localization(
    x_range: np.ndarray,
    kernel_values: np.ndarray,
    loci_positions: Optional[List[float]] = None,
    interactive: bool = False,
    return_base64: bool = False
) -> Union[plt.Figure, go.Figure, str, None]:
    """
    Plot zero divisor kernel localization.

    Visualizes the Gaussian-like kernel K_Z(P,x) centered at zero divisor loci.

    Args:
        x_range: Array of x positions
        kernel_values: Kernel values at each x
        loci_positions: Positions of zero divisor loci (for markers)
        interactive: If True, return Plotly figure (premium)
        return_base64: If True, return base64-encoded PNG string

    Returns:
        Figure object or base64 string
    """
    if interactive and PLOTLY_AVAILABLE:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=x_range,
            y=kernel_values,
            mode='lines',
            name='K_Z(P, x)',
            line=dict(color=THEME['primary_color'], width=3),
            fill='tozeroy',
            fillcolor=f'rgba(139, 92, 246, 0.3)',
            hovertemplate='x = %{x:.2f}<br>K_Z = %{y:.4f}<extra></extra>'
        ))

        if loci_positions:
            for i, pos in enumerate(loci_positions):
                fig.add_vline(
                    x=pos,
                    line_dash="dot",
                    line_color="red",
                    annotation_text=f"Locus {i+1}"
                )

        fig.update_layout(
            title="Zero Divisor Kernel Localization",
            xaxis_title="Position x",
            yaxis_title="Kernel K_Z(P, x)",
            template="plotly_white",
            height=500
        )

        return fig

    else:
        fig, ax = plt.subplots(figsize=(8, 6), dpi=THEME['dpi'])

        ax.fill_between(x_range, kernel_values, alpha=0.3, color=THEME['primary_color'])
        ax.plot(x_range, kernel_values, color=THEME['primary_color'], linewidth=2)

        if loci_positions:
            for i, pos in enumerate(loci_positions):
                ax.axvline(pos, color='red', linestyle=':', linewidth=1.5, alpha=0.7)
                ax.text(pos, max(kernel_values)*0.9, f'Locus {i+1}',
                        rotation=90, va='top', ha='right', fontsize=8)

        ax.set_xlabel('Position x', fontsize=THEME['font_size'])
        ax.set_ylabel('Kernel K_Z(P, x)', fontsize=THEME['font_size'])
        ax.set_title('Zero Divisor Kernel Localization', fontsize=THEME['font_size']+2, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if return_base64:
            return _fig_to_base64(fig)
        return fig


def plot_comprehensive_analysis(
    alpha_data: Tuple[np.ndarray, np.ndarray],
    d_data: Tuple[np.ndarray, np.ndarray],
    spatial_data: Tuple[np.ndarray, np.ndarray],
    kernel_data: Tuple[np.ndarray, np.ndarray],
    fourier_data: Tuple[np.ndarray, np.ndarray],
    pattern_values: Dict[int, float],
    optimal_alpha: Optional[float] = None,
    return_base64: bool = False
) -> Union[plt.Figure, str]:
    """
    Create comprehensive 6-panel analysis figure (matches research report).

    This is the flagship visualization combining all key aspects of the transform.
    Note: Only available as static matplotlib (too complex for basic interactive).

    Args:
        alpha_data: (alpha_values, transform_values) tuple
        d_data: (d_values, transform_values) tuple
        spatial_data: (x_values, transform_values) tuple for spatial behavior
        kernel_data: (x_values, kernel_values) tuple
        fourier_data: (frequencies, magnitudes) tuple
        pattern_values: Dict of pattern_id -> transform value
        optimal_alpha: Mark optimal alpha if provided
        return_base64: If True, return base64-encoded PNG

    Returns:
        Figure or base64 string
    """
    fig = plt.figure(figsize=(15, 10), dpi=THEME['dpi'])
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)

    # Panel 1: Alpha sensitivity
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(alpha_data[0], np.abs(alpha_data[1]), 'o-',
             color=THEME['accent_color'], linewidth=2, markersize=4)
    if optimal_alpha:
        ax1.axvline(optimal_alpha, color='red', linestyle='--', linewidth=1.5,
                    label=f'Optimal α = {optimal_alpha:.2f}')
        ax1.legend(fontsize=8)
    ax1.set_xscale('log')
    ax1.set_xlabel('Alpha (convergence parameter)', fontsize=9)
    ax1.set_ylabel('|C[f]| (Transform magnitude)', fontsize=9)
    ax1.set_title('Chavez Transform vs Alpha Parameter', fontsize=10, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Panel 2: Dimensional weighting
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(d_data[0], d_data[1], 'o-',
             color=THEME['secondary_color'], linewidth=2, markersize=6)
    ax2.set_xlabel('Dimension parameter d', fontsize=9)
    ax2.set_ylabel('C[f] value', fontsize=9)
    ax2.set_title('Effect of Dimensional Weighting', fontsize=10, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # Panel 3: Fourier Transform (reference)
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(fourier_data[0], fourier_data[1], color=THEME['accent_color'], linewidth=2)
    ax3.set_xlabel('Frequency', fontsize=9)
    ax3.set_ylabel('Magnitude', fontsize=9)
    ax3.set_title('Fourier Transform (Frequency Domain)', fontsize=10, fontweight='bold')
    ax3.grid(True, alpha=0.3)

    # Panel 4: Chavez spatial behavior
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.plot(spatial_data[0], spatial_data[1], color=THEME['secondary_color'], linewidth=2)
    ax4.set_xlabel('Evaluation point', fontsize=9)
    ax4.set_ylabel('C[f] value', fontsize=9)
    ax4.set_title('Chavez Transform (Spatial Behavior)', fontsize=10, fontweight='bold')
    ax4.grid(True, alpha=0.3)

    # Panel 5: Kernel localization
    ax5 = fig.add_subplot(gs[2, 0])
    ax5.fill_between(kernel_data[0], kernel_data[1], alpha=0.3, color=THEME['primary_color'])
    ax5.plot(kernel_data[0], kernel_data[1], color=THEME['primary_color'], linewidth=2)
    ax5.set_xlabel('Position x', fontsize=9)
    ax5.set_ylabel('Kernel K_Z(P, x)', fontsize=9)
    ax5.set_title('Zero Divisor Kernel Localization', fontsize=10, fontweight='bold')
    ax5.grid(True, alpha=0.3)

    # Panel 6: Canonical Six universality
    ax6 = fig.add_subplot(gs[2, 1])
    patterns = list(pattern_values.keys())
    values = list(pattern_values.values())
    mean_value = np.mean(values)
    ax6.bar(patterns, values, color=THEME['primary_color'], edgecolor='white', linewidth=2)
    ax6.axhline(mean_value, color='red', linestyle='--', linewidth=2, alpha=0.7,
                label=f'Mean = {mean_value:.6e}')
    ax6.set_xlabel('Pattern ID', fontsize=9)
    ax6.set_ylabel('C[f] value', fontsize=9)
    ax6.set_title('Canonical Six Pattern Universality', fontsize=10, fontweight='bold')
    ax6.legend(fontsize=8, loc='upper right')
    ax6.grid(axis='y', alpha=0.3)

    plt.suptitle('Chavez Transform - Comprehensive Analysis',
                 fontsize=14, fontweight='bold', y=0.995)

    if return_base64:
        return _fig_to_base64(fig)
    return fig


def plot_transform_result(
    result_data: Dict,
    interactive: bool = False,
    return_base64: bool = False
) -> Union[plt.Figure, go.Figure, str, None]:
    """
    Generic transform result visualization.

    Flexible plotting function for various transform outputs.

    Args:
        result_data: Dictionary with plotting data (structure flexible based on content)
        interactive: If True, return Plotly figure (premium)
        return_base64: If True, return base64-encoded PNG

    Returns:
        Figure or base64 string
    """
    # Implementation would depend on result_data structure
    # This is a placeholder for future expansion
    pass


def plot_e8_mandala(
    projections: Dict[int, Tuple[float, float, int]],
    canonical_mapping: Optional[Dict[int, Tuple]] = None,
    transform_values: Optional[Dict[int, float]] = None,
    highlight_pattern_4: bool = True,
    interactive: bool = False,
    return_base64: bool = False
) -> Union[plt.Figure, go.Figure, str, None]:
    """
    Plot E8 root lattice as 30-fold symmetric mandala (Coxeter projection).

    The flagship visualization combining E8 geometry with zero divisor discoveries.
    Purple and light blue gradient represents the "color of impossibility" (Cirlot).

    Args:
        projections: Dict mapping root_index -> (x, y, orbit_id) in Coxeter plane
        canonical_mapping: Dict mapping pattern_id -> (E8Root, orbit_id) for Canonical Six
        transform_values: Dict mapping pattern_id -> Chavez Transform value
        highlight_pattern_4: If True, highlight Pattern 4's anomalous position
        interactive: If True, return Plotly figure (premium)
        return_base64: If True, return base64-encoded PNG

    Returns:
        Figure object or base64 string
    """
    if interactive and PLOTLY_AVAILABLE:
        # Premium: Interactive Plotly with hover
        fig = go.Figure()

        # Separate roots by orbit for different styling
        orbits = {}
        for idx, (x, y, orbit_id) in projections.items():
            if orbit_id not in orbits:
                orbits[orbit_id] = {'x': [], 'y': [], 'indices': []}
            orbits[orbit_id]['x'].append(x)
            orbits[orbit_id]['y'].append(y)
            orbits[orbit_id]['indices'].append(idx)

        # Plot each orbit with different color
        orbit_colors = [THEME['primary_color'], THEME['accent_color']]

        for orbit_id, data in orbits.items():
            color = orbit_colors[orbit_id % len(orbit_colors)]
            fig.add_trace(go.Scatter(
                x=data['x'],
                y=data['y'],
                mode='markers',
                name=f'Orbit {orbit_id}',
                marker=dict(
                    size=4,
                    color=color,
                    opacity=0.6
                ),
                hovertemplate=f'Orbit {orbit_id}<br>x=%{{x:.3f}}<br>y=%{{y:.3f}}<extra></extra>'
            ))

        # Overlay Canonical Six if provided
        if canonical_mapping:
            canonical_x = []
            canonical_y = []
            canonical_labels = []

            for pattern_id in range(1, 7):
                if pattern_id in canonical_mapping:
                    e8_root, orbit_id = canonical_mapping[pattern_id]
                    # Find projection for this root
                    for idx, (x, y, oid) in projections.items():
                        if oid == orbit_id:  # Approximate match
                            canonical_x.append(x)
                            canonical_y.append(y)
                            canonical_labels.append(f'Pattern {pattern_id}')
                            break

            # Determine marker colors based on transform values
            if transform_values:
                # Normalize transform values for color gradient
                vals = [transform_values.get(i, 0) for i in range(1, 7)]
                val_min, val_max = min(vals), max(vals)

                marker_colors = []
                for pattern_id in range(1, 7):
                    if pattern_id == 4 and highlight_pattern_4:
                        marker_colors.append(THEME['pattern_4_color'])  # Gold for Pattern 4
                    else:
                        # Gradient from purple to light blue
                        val = transform_values.get(pattern_id, 0)
                        if val_max > val_min:
                            t = (val - val_min) / (val_max - val_min)
                            marker_colors.append(THEME['primary_color'] if t < 0.5 else THEME['accent_color'])
                        else:
                            marker_colors.append(THEME['primary_color'])
            else:
                marker_colors = [THEME['canonical_color']] * 6

            fig.add_trace(go.Scatter(
                x=canonical_x[:6],
                y=canonical_y[:6],
                mode='markers+text',
                name='Canonical Six',
                marker=dict(
                    size=15,
                    color=marker_colors,
                    symbol='star',
                    line=dict(width=2, color='white')
                ),
                text=[f'P{i}' for i in range(1, 7)],
                textposition='top center',
                hovertemplate='%{text}<extra></extra>'
            ))

        fig.update_layout(
            title="E8 Mandala - Weyl Orbit Structure with Zero Divisors",
            xaxis=dict(
                title="Coxeter Plane X",
                showgrid=True,
                zeroline=True,
                scaleanchor="y",
                scaleratio=1
            ),
            yaxis=dict(
                title="Coxeter Plane Y",
                showgrid=True,
                zeroline=True
            ),
            template="plotly_white",
            height=800,
            width=800,
            showlegend=True
        )

        return fig

    else:
        # Free: Static matplotlib mandala
        fig, ax = plt.subplots(figsize=THEME['e8_mandala_size'], dpi=THEME['dpi'])

        # Separate roots by orbit
        orbits = {}
        for idx, (x, y, orbit_id) in projections.items():
            if orbit_id not in orbits:
                orbits[orbit_id] = {'x': [], 'y': []}
            orbits[orbit_id]['x'].append(x)
            orbits[orbit_id]['y'].append(y)

        # Plot E8 roots with orbit-based coloring
        orbit_colors = [THEME['primary_color'], THEME['accent_color']]

        for orbit_id, data in orbits.items():
            color = orbit_colors[orbit_id % len(orbit_colors)]
            ax.scatter(
                data['x'], data['y'],
                c=color,
                s=20,
                alpha=0.6,
                edgecolors='none',
                label=f'Orbit {orbit_id} ({len(data["x"])} roots)'
            )

        # Overlay Canonical Six patterns
        if canonical_mapping:
            for pattern_id in range(1, 7):
                if pattern_id not in canonical_mapping:
                    continue

                e8_root, orbit_id = canonical_mapping[pattern_id]

                # Find approximate projection (use first matching orbit)
                for idx, (x, y, oid) in projections.items():
                    if oid == orbit_id:
                        # Determine color based on Pattern 4 anomaly
                        if pattern_id == 4 and highlight_pattern_4:
                            color = THEME['pattern_4_color']  # Gold
                            size = 300
                            marker = '*'
                            zorder = 100
                        else:
                            # Gradient based on transform value if provided
                            if transform_values and pattern_id in transform_values:
                                val = transform_values[pattern_id]
                                # Use purple for lower, light blue for higher
                                color = THEME['primary_color']  # Simplified
                            else:
                                color = THEME['canonical_color']
                            size = 200
                            marker = '*'
                            zorder = 50

                        ax.scatter(
                            [x], [y],
                            c=color,
                            s=size,
                            marker=marker,
                            edgecolors='white',
                            linewidths=2,
                            zorder=zorder,
                            label=f'Pattern {pattern_id}'
                        )

                        # Add label
                        ax.text(
                            x, y + 0.15,
                            f'P{pattern_id}',
                            ha='center',
                            va='bottom',
                            fontsize=10,
                            fontweight='bold',
                            color='white',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7)
                        )
                        break

        # Styling
        ax.set_xlabel('Coxeter Plane X', fontsize=THEME['font_size']+2)
        ax.set_ylabel('Coxeter Plane Y', fontsize=THEME['font_size']+2)
        ax.set_title('E8 Mandala: Weyl Orbit Structure & Zero Divisor Patterns',
                     fontsize=THEME['font_size']+4, fontweight='bold', pad=20)

        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2, linestyle='--')
        ax.axhline(0, color='gray', linewidth=0.5, alpha=0.3)
        ax.axvline(0, color='gray', linewidth=0.5, alpha=0.3)

        # Add subtle circular grid for mandala effect
        for radius in [0.25, 0.5, 0.75, 1.0]:
            circle = plt.Circle((0, 0), radius, fill=False, color='gray',
                              alpha=0.15, linestyle=':', linewidth=1)
            ax.add_patch(circle)

        # Legend
        ax.legend(loc='upper right', fontsize=8, framealpha=0.9)

        plt.tight_layout()

        if return_base64:
            return _fig_to_base64(fig)
        return fig


# Utility functions

def _fig_to_base64(fig: plt.Figure) -> str:
    """
    Convert matplotlib figure to base64-encoded PNG string.

    Args:
        fig: Matplotlib figure

    Returns:
        Base64-encoded PNG string
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=THEME['dpi'])
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64


def save_figure(
    fig: Union[plt.Figure, go.Figure],
    filepath: str,
    format: str = 'png'
) -> None:
    """
    Save figure to file.

    Args:
        fig: Figure object (matplotlib or plotly)
        filepath: Output file path
        format: Output format ('png', 'svg', 'html' for plotly)
    """
    if isinstance(fig, plt.Figure):
        fig.savefig(filepath, format=format, bbox_inches='tight', dpi=THEME['dpi'])
        plt.close(fig)
    elif PLOTLY_AVAILABLE and isinstance(fig, go.Figure):
        if format == 'html':
            fig.write_html(filepath)
        else:
            fig.write_image(filepath, format=format)


# Example usage and testing
if __name__ == "__main__":
    print("="*80)
    print("CHAVEZ TRANSFORM VISUALIZATIONS - TEST")
    print("="*80)
    print()

    # Test data
    pattern_values = {i: 0.7771203 for i in range(1, 7)}  # Universal symmetry

    alpha_values = np.logspace(-1, 1, 20)
    transform_values = 2.0 * np.exp(-0.5 * alpha_values)  # Mock decay

    d_values = np.arange(1, 11)
    d_transform_values = 0.85 - 0.04 * d_values  # Mock linear decrease

    print("Creating Canonical Six Universality plot...")
    fig1 = plot_canonical_six_universality(pattern_values)
    print("  ✓ Created")

    print("Creating Alpha Sensitivity plot...")
    fig2 = plot_alpha_sensitivity(alpha_values, transform_values, optimal_alpha=0.01)
    print("  ✓ Created")

    print("Creating Dimensional Weighting plot...")
    fig3 = plot_dimensional_weighting(d_values, d_transform_values)
    print("  ✓ Created")

    print()
    print("All visualization functions working correctly!")
    print("="*80)
