"""
FedSantize Visualization Master Package
=======================================
"""

from .network import (
    THEME,
    render_network_graph,
    render_network_fallback_html,
)
from .defense import (
    render_layer1_norm_chart,
    render_layer1_cosine_chart,
    render_mars_architecture_diagram,
    render_mars_cbe_chart,
    render_mars_wasserstein_heatmap,
    render_mars_clustering_scatter,
    render_aggregation_overview_chart,
)
from .attacks import (
    render_backdoor_stages_html,
    render_extreme_update_comparison,
    render_sign_flip_vector_diagram,
    render_byzantine_noise_scatter,
    render_label_flipping_card,
)
from .components import (
    render_arena_header_metrics,
    render_interactive_timeline_html,
    render_client_forensics_card,
    compute_threat_level,
    render_pipeline_status_bar,
    render_before_after_comparison,
)
from .effects import (
    render_alert_banner,
    render_quarantine_action_card,
    render_live_security_feed_html,
)

__all__ = [
    "THEME",
    "render_network_graph",
    "render_network_fallback_html",
    "render_layer1_norm_chart",
    "render_layer1_cosine_chart",
    "render_mars_architecture_diagram",
    "render_mars_cbe_chart",
    "render_mars_wasserstein_heatmap",
    "render_mars_clustering_scatter",
    "render_aggregation_overview_chart",
    "render_backdoor_stages_html",
    "render_extreme_update_comparison",
    "render_sign_flip_vector_diagram",
    "render_byzantine_noise_scatter",
    "render_label_flipping_card",
    "render_arena_header_metrics",
    "render_interactive_timeline_html",
    "render_client_forensics_card",
    "compute_threat_level",
    "render_pipeline_status_bar",
    "render_before_after_comparison",
    "render_alert_banner",
    "render_quarantine_action_card",
    "render_live_security_feed_html",
]
