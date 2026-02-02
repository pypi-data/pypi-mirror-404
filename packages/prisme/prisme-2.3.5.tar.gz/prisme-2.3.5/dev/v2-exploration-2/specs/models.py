PRISME_SPEC_VERSION = 2

from prisme.spec import (  # noqa: E402
    DeliveryOverrides,
    Field,
    FrontendOverrides,
    MCPOverrides,
    Model,
    Relationship,
    StackSpec,
)

stack = StackSpec(
    name="wind-pipeline",
    models=[
        # ──────────────────────────────────────────────
        # Project — top-level container
        # ──────────────────────────────────────────────
        Model(
            name="Project",
            description="A wind energy project containing multiple sites for analysis.",
            fields=[
                Field(
                    "name",
                    type="string",
                    required=True,
                    max_length=255,
                    searchable=True,
                    filter_operators=["eq", "ilike", "contains"],
                    label="Project Name",
                    description="User-provided name for this project",
                    ui_placeholder="e.g., Nordic Wind Farm Development",
                ),
                Field("description", type="text", label="Description", ui_widget="textarea"),
                Field(
                    "address",
                    type="string",
                    max_length=500,
                    label="Address",
                    searchable=True,
                    filter_operators=["ilike", "contains"],
                ),
                Field(
                    "status",
                    type="enum",
                    choices=["planning", "active", "completed", "archived"],
                    default="planning",
                    label="Status",
                    filterable=True,
                ),
                Field("notes", type="text", label="Notes", ui_widget="textarea"),
            ],
            relationships=[
                Relationship(
                    "sites",
                    target="Site",
                    type="one-to-many",
                    back_populates="project",
                    cascade="all, delete-orphan",
                ),
            ],
            expose=True,
            operations=["create", "read", "update", "delete", "list"],
            soft_delete=True,
            timestamps=True,
            delivery_overrides=DeliveryOverrides(
                rest_tags=["projects"],
            ),
            frontend_overrides=FrontendOverrides(
                nav_label="Projects",
                nav_icon="folder",
                table_columns=["name", "status", "created_at"],
            ),
            mcp_overrides=MCPOverrides(
                tool_prefix="project",
                tool_descriptions={
                    "list": "List wind energy projects",
                    "read": "Get details of a specific project by ID",
                    "create": "Create a new wind energy project",
                },
            ),
        ),
        # ──────────────────────────────────────────────
        # Site — location within a project
        # ──────────────────────────────────────────────
        Model(
            name="Site",
            description="A specific geographical location within a wind energy project.",
            fields=[
                Field(
                    "project_id",
                    type="foreign_key",
                    references="Project",
                    required=True,
                    on_delete="CASCADE",
                ),
                Field(
                    "name",
                    type="string",
                    required=True,
                    max_length=255,
                    searchable=True,
                    filter_operators=["eq", "ilike", "contains"],
                    label="Site Name",
                ),
                Field(
                    "latitude",
                    type="float",
                    required=True,
                    min_value=-90.0,
                    max_value=90.0,
                    label="Latitude",
                    ui_widget="coordinates",
                ),
                Field(
                    "longitude",
                    type="float",
                    required=True,
                    min_value=-180.0,
                    max_value=180.0,
                    label="Longitude",
                    ui_widget="coordinates",
                ),
                Field("address", type="string", max_length=500, label="Address", searchable=True),
                Field("notes", type="text", label="Notes", ui_widget="textarea"),
            ],
            relationships=[
                Relationship(
                    "project", target="Project", type="many-to-one", back_populates="sites"
                ),
                Relationship(
                    "wind_data_jobs",
                    target="WindDataJob",
                    type="one-to-many",
                    back_populates="site",
                    cascade="all, delete-orphan",
                ),
            ],
            expose=True,
            operations=["create", "read", "update", "delete", "list"],
            soft_delete=True,
            timestamps=True,
            list_fields=["id", "name", "latitude", "longitude", "project_id", "created_at"],
            delivery_overrides=DeliveryOverrides(
                rest_tags=["sites"],
            ),
            frontend_overrides=FrontendOverrides(
                include_in_nav=False,  # Accessed via project detail
                table_columns=["name", "latitude", "longitude", "created_at"],
            ),
            mcp_overrides=MCPOverrides(
                tool_prefix="site",
                tool_descriptions={
                    "list": "List sites within a wind energy project",
                    "read": "Get details of a specific site",
                    "create": "Create a new site within a project",
                },
            ),
        ),
        # ──────────────────────────────────────────────
        # EnvironmentAnalysis — 3D environment analysis
        # ──────────────────────────────────────────────
        Model(
            name="EnvironmentAnalysis",
            description="A saved 3D environment analysis for a site.",
            fields=[
                Field(
                    "name",
                    type="string",
                    required=True,
                    max_length=255,
                    searchable=True,
                    label="Analysis Name",
                ),
                Field(
                    "center_lat",
                    type="float",
                    required=True,
                    min_value=-90.0,
                    max_value=90.0,
                    label="Center Latitude",
                ),
                Field(
                    "center_lon",
                    type="float",
                    required=True,
                    min_value=-180.0,
                    max_value=180.0,
                    label="Center Longitude",
                ),
                Field(
                    "radius",
                    type="float",
                    required=True,
                    default=500.0,
                    min_value=100.0,
                    max_value=5000.0,
                    label="Radius (m)",
                    ui_widget="slider",
                    ui_widget_props={"min": 100, "max": 5000, "step": 100},
                ),
                Field(
                    "hub_height",
                    type="float",
                    required=True,
                    default=50.0,
                    min_value=10.0,
                    max_value=200.0,
                    label="Hub Height (m)",
                    ui_widget="slider",
                    ui_widget_props={"min": 10, "max": 200, "step": 5},
                ),
                Field(
                    "status",
                    type="enum",
                    choices=["pending", "processing", "completed", "failed"],
                    default="pending",
                    label="Status",
                    filterable=True,
                ),
                Field(
                    "terrain_data",
                    type="json",
                    hidden=True,
                    label="Terrain Data",
                    description="Processed terrain mesh data",
                ),
                Field("buildings_data", type="json", hidden=True, label="Buildings Data"),
                Field("sectors_data", type="json", hidden=True, label="Sectors Data"),
                Field("building_count", type="integer", label="Building Count"),
                Field(
                    "avg_roughness", type="float", label="Average Roughness", ui_widget="roughness"
                ),
                Field(
                    "dominant_land_cover",
                    type="string",
                    max_length=100,
                    label="Dominant Land Cover",
                ),
                Field(
                    "wind_data_job_id",
                    type="foreign_key",
                    references="WindDataJob",
                    on_delete="SET NULL",
                ),
            ],
            relationships=[
                Relationship(
                    "sectors",
                    target="WindSector",
                    type="one-to-many",
                    back_populates="analysis",
                    cascade="all, delete-orphan",
                ),
                Relationship(
                    "wind_data_job",
                    target="WindDataJob",
                    type="many-to-one",
                    back_populates="environment_analyses",
                ),
            ],
            expose=True,
            operations=["create", "read", "update", "delete", "list"],
            soft_delete=True,
            timestamps=True,
            read_fields=[
                "id",
                "name",
                "center_lat",
                "center_lon",
                "radius",
                "hub_height",
                "status",
                "building_count",
                "avg_roughness",
                "dominant_land_cover",
                "wind_data_job_id",
                "created_at",
                "updated_at",
            ],
            delivery_overrides=DeliveryOverrides(rest_tags=["environment"]),
            frontend_overrides=FrontendOverrides(
                nav_label="Analyses",
                nav_icon="layers",
                table_columns=["name", "status", "avg_roughness", "building_count", "created_at"],
            ),
            mcp_overrides=MCPOverrides(tool_prefix="analysis"),
        ),
        # ──────────────────────────────────────────────
        # WindSector — roughness per wind direction
        # ──────────────────────────────────────────────
        Model(
            name="WindSector",
            description="Roughness data for a specific wind direction sector.",
            fields=[
                Field(
                    "analysis_id",
                    type="foreign_key",
                    references="EnvironmentAnalysis",
                    required=True,
                    on_delete="CASCADE",
                ),
                Field(
                    "index",
                    type="integer",
                    required=True,
                    min_value=0,
                    max_value=15,
                    label="Sector Index",
                    description="Sector index (0-15, representing 16 wind directions)",
                ),
                Field("start_angle", type="float", required=True, label="Start Angle (deg)"),
                Field("end_angle", type="float", required=True, label="End Angle (deg)"),
                Field(
                    "z0",
                    type="float",
                    required=True,
                    label="Roughness Length (z0)",
                    ui_widget="roughness",
                ),
                Field("displacement_height", type="float", label="Displacement Height"),
                Field(
                    "dominant_cover",
                    type="enum",
                    choices=[
                        "tree_cover",
                        "shrubland",
                        "grassland",
                        "cropland",
                        "built_up",
                        "bare_vegetation",
                        "snow_ice",
                        "permanent_water",
                        "herbaceous_wetland",
                        "mangroves",
                        "moss_lichen",
                    ],
                    label="Dominant Land Cover",
                ),
                Field("obstacle_count", type="integer", default=0, label="Obstacle Count"),
            ],
            relationships=[
                Relationship(
                    "analysis",
                    target="EnvironmentAnalysis",
                    type="many-to-one",
                    back_populates="sectors",
                ),
            ],
            expose=True,
            operations=["read", "list"],
            timestamps=True,
            delivery_overrides=DeliveryOverrides(rest_tags=["environment"]),
            frontend_overrides=FrontendOverrides(
                include_in_nav=False,  # Accessed via analysis detail
                generate_form=False,
                generate_detail_view=False,
            ),
            mcp_overrides=MCPOverrides(
                tool_prefix="sector",
                tool_descriptions={
                    "list": "List wind sectors for an environment analysis",
                    "read": "Get roughness details for a specific wind sector",
                },
            ),
        ),
        # ──────────────────────────────────────────────
        # WindDataJob — wind data preparation job
        # ──────────────────────────────────────────────
        Model(
            name="WindDataJob",
            description="A wind data preparation job for downloading and processing ERA5/CERRA data.",
            fields=[
                Field(
                    "site_id",
                    type="foreign_key",
                    references="Site",
                    required=True,
                    on_delete="CASCADE",
                ),
                Field(
                    "name",
                    type="string",
                    required=True,
                    max_length=255,
                    searchable=True,
                    label="Job Name",
                ),
                Field(
                    "site_lat",
                    type="float",
                    required=True,
                    min_value=-90.0,
                    max_value=90.0,
                    label="Site Latitude",
                ),
                Field(
                    "site_lon",
                    type="float",
                    required=True,
                    min_value=-180.0,
                    max_value=180.0,
                    label="Site Longitude",
                ),
                Field("time_start", type="datetime", required=True, label="Time Start"),
                Field("time_end", type="datetime", required=True, label="Time End"),
                Field(
                    "z_hub",
                    type="float",
                    required=True,
                    default=100.0,
                    min_value=10.0,
                    max_value=300.0,
                    label="Hub Height (m)",
                    ui_widget="slider",
                    ui_widget_props={"min": 10, "max": 300, "step": 5},
                ),
                Field(
                    "z_blend",
                    type="float",
                    default=120.0,
                    min_value=10.0,
                    max_value=500.0,
                    label="Blending Height (m)",
                    ui_widget="slider",
                    ui_widget_props={"min": 10, "max": 500, "step": 10},
                ),
                Field(
                    "dataset",
                    type="enum",
                    choices=["ERA5", "CERRA", "AUTO"],
                    default="AUTO",
                    label="Dataset",
                    filterable=True,
                ),
                Field(
                    "use_neutral_winds", type="boolean", default=False, label="Use Neutral Winds"
                ),
                Field(
                    "num_sectors",
                    type="integer",
                    default=12,
                    min_value=4,
                    max_value=36,
                    label="Number of Sectors",
                ),
                Field(
                    "status",
                    type="enum",
                    choices=["pending", "downloading", "processing", "completed", "failed"],
                    default="pending",
                    label="Status",
                    filterable=True,
                    filter_operators=["eq", "in"],
                ),
                Field(
                    "progress_percent",
                    type="float",
                    default=0.0,
                    min_value=0.0,
                    max_value=100.0,
                    label="Progress (%)",
                ),
                Field("error_message", type="text", label="Error Message"),
                Field("dataset_used", type="string", max_length=50, label="Dataset Used"),
                Field(
                    "download_path",
                    type="string",
                    max_length=500,
                    hidden=True,
                    label="Download Path",
                ),
                Field(
                    "timeseries_file",
                    type="string",
                    max_length=500,
                    hidden=True,
                    label="Timeseries File",
                ),
                Field("qc_flags", type="json", hidden=True, label="QC Flags"),
                Field("records_count", type="integer", label="Records Count"),
                Field(
                    "mean_wind_speed",
                    type="float",
                    label="Mean Wind Speed",
                    filterable=True,
                    filter_operators=["eq", "gt", "lt", "between"],
                ),
                Field("dominant_direction", type="float", label="Dominant Direction"),
                Field("missing_data_percent", type="float", label="Missing Data (%)"),
                Field("notes", type="text", label="Notes", ui_widget="textarea"),
            ],
            relationships=[
                Relationship(
                    "site", target="Site", type="many-to-one", back_populates="wind_data_jobs"
                ),
                Relationship(
                    "wind_rose",
                    target="WindRoseSector",
                    type="one-to-many",
                    back_populates="job",
                    cascade="all, delete-orphan",
                ),
                Relationship(
                    "environment_analyses",
                    target="EnvironmentAnalysis",
                    type="one-to-many",
                    back_populates="wind_data_job",
                ),
            ],
            expose=True,
            operations=["create", "read", "update", "list"],
            soft_delete=True,
            timestamps=True,
            list_fields=[
                "id",
                "name",
                "status",
                "dataset",
                "progress_percent",
                "mean_wind_speed",
                "site_id",
                "created_at",
            ],
            delivery_overrides=DeliveryOverrides(
                page_size=25,
                rest_tags=["wind-data"],
            ),
            frontend_overrides=FrontendOverrides(
                nav_label="Wind Data Jobs",
                nav_icon="wind",
                table_columns=["name", "status", "dataset", "mean_wind_speed", "created_at"],
            ),
            mcp_overrides=MCPOverrides(
                tool_prefix="windjob",
                tool_descriptions={
                    "list": "List wind data preparation jobs",
                    "read": "Get details of a wind data job",
                    "create": "Create a new wind data preparation job",
                },
            ),
        ),
        # ──────────────────────────────────────────────
        # WindRoseSector — wind rose statistics
        # ──────────────────────────────────────────────
        Model(
            name="WindRoseSector",
            description="Wind rose statistics for a specific directional sector.",
            fields=[
                Field(
                    "job_id",
                    type="foreign_key",
                    references="WindDataJob",
                    required=True,
                    on_delete="CASCADE",
                ),
                Field("sector_index", type="integer", required=True, label="Sector Index"),
                Field("sector_center", type="float", required=True, label="Sector Center (deg)"),
                Field("sector_start", type="float", required=True, label="Sector Start (deg)"),
                Field("sector_end", type="float", required=True, label="Sector End (deg)"),
                Field(
                    "frequency",
                    type="float",
                    required=True,
                    label="Frequency",
                    filterable=True,
                    filter_operators=["gt", "lt", "between"],
                ),
                Field(
                    "mean_speed",
                    type="float",
                    required=True,
                    label="Mean Speed (m/s)",
                    filterable=True,
                ),
                Field("max_speed", type="float", label="Max Speed (m/s)"),
                Field("sample_count", type="integer", label="Sample Count"),
                Field("weibull_k", type="float", label="Weibull k"),
                Field("weibull_a", type="float", label="Weibull A"),
            ],
            relationships=[
                Relationship(
                    "job", target="WindDataJob", type="many-to-one", back_populates="wind_rose"
                ),
            ],
            expose=True,
            operations=["read", "list"],
            delivery_overrides=DeliveryOverrides(rest_tags=["wind-data"]),
            frontend_overrides=FrontendOverrides(
                include_in_nav=False,  # Accessed via job detail
                generate_form=False,
                generate_detail_view=False,
            ),
            mcp_overrides=MCPOverrides(
                tool_prefix="windrose",
                tool_descriptions={
                    "list": "List wind rose sectors for a job",
                    "read": "Get details of a specific wind rose sector",
                },
            ),
        ),
        # ──────────────────────────────────────────────
        # LandCoverType — reference data (read-only)
        # ──────────────────────────────────────────────
        Model(
            name="LandCoverType",
            description="ESA WorldCover land classification reference data.",
            fields=[
                Field(
                    "code", type="integer", required=True, unique=True, indexed=True, label="Code"
                ),
                Field(
                    "name",
                    type="string",
                    required=True,
                    max_length=100,
                    searchable=True,
                    label="Name",
                ),
                Field("description", type="text", label="Description"),
                Field("z0", type="float", required=True, label="Roughness Length (z0)"),
                Field(
                    "color_hex",
                    type="string",
                    required=True,
                    max_length=7,
                    pattern=r"^#[0-9A-Fa-f]{6}$",
                    label="Display Color",
                    ui_widget="color",
                ),
                Field(
                    "color_rgb",
                    type="json",
                    required=True,
                    json_item_type="int",
                    label="RGB Color",
                    description="RGB color values [r, g, b] for Three.js",
                ),
            ],
            expose=True,
            operations=["read", "list"],
            delivery_overrides=DeliveryOverrides(rest_tags=["reference"]),
            frontend_overrides=FrontendOverrides(
                include_in_nav=False,  # Reference data, not primary navigation
                nav_label="Land Cover Types",
                nav_icon="tree-pine",
                table_columns=["code", "name", "z0", "color_hex"],
                generate_form=False,
            ),
            mcp_overrides=MCPOverrides(tool_prefix="landcover"),
        ),
        # ──────────────────────────────────────────────
        # DataSource — external data source config
        # ──────────────────────────────────────────────
        Model(
            name="DataSource",
            description="Configuration for external data sources (terrain, buildings, land cover).",
            fields=[
                Field(
                    "name",
                    type="string",
                    required=True,
                    unique=True,
                    max_length=255,
                    searchable=True,
                    label="Source Name",
                ),
                Field(
                    "type",
                    type="enum",
                    choices=["terrain", "buildings", "landcover"],
                    required=True,
                    label="Data Type",
                    filterable=True,
                ),
                Field("provider", type="string", required=True, max_length=255, label="Provider"),
                Field("api_url", type="string", max_length=500, label="API URL", ui_widget="url"),
                Field(
                    "requires_auth", type="boolean", default=False, label="Requires Authentication"
                ),
                Field(
                    "api_key_env_var", type="string", max_length=255, label="API Key Env Variable"
                ),
                Field("resolution", type="string", max_length=100, label="Resolution"),
                Field("is_active", type="boolean", default=True, label="Active", filterable=True),
                Field("config", type="json", label="Additional Config", ui_widget="json"),
            ],
            expose=True,
            operations=["create", "read", "update", "delete", "list"],
            timestamps=True,
            delivery_overrides=DeliveryOverrides(rest_tags=["config"]),
            frontend_overrides=FrontendOverrides(
                nav_label="Data Sources",
                nav_icon="database",
                table_columns=["name", "type", "provider", "is_active"],
            ),
            mcp_overrides=MCPOverrides(tool_prefix="datasource"),
        ),
        # ──────────────────────────────────────────────
        # CDSCredential — Copernicus CDS API credentials
        # ──────────────────────────────────────────────
        Model(
            name="CDSCredential",
            description="Copernicus Climate Data Store API credentials.",
            fields=[
                Field(
                    "name",
                    type="string",
                    required=True,
                    unique=True,
                    max_length=255,
                    searchable=True,
                    label="Credential Name",
                ),
                Field(
                    "api_url",
                    type="string",
                    max_length=500,
                    default="https://cds.climate.copernicus.eu/api/v2",
                    label="API URL",
                    ui_widget="url",
                ),
                Field(
                    "api_key",
                    type="string",
                    required=True,
                    max_length=255,
                    hidden=True,
                    label="API Key",
                    ui_widget="password",
                ),
                Field("is_active", type="boolean", default=True, label="Active", filterable=True),
                Field("notes", type="text", label="Notes", ui_widget="textarea"),
            ],
            expose=True,
            operations=["create", "read", "update", "delete", "list"],
            timestamps=True,
            delivery_overrides=DeliveryOverrides(rest_tags=["config"]),
            frontend_overrides=FrontendOverrides(
                nav_label="CDS Credentials",
                nav_icon="key",
                table_columns=["name", "api_url", "is_active"],
            ),
            mcp_overrides=MCPOverrides(tool_prefix="cds"),
        ),
    ],
)
