"""Router generator for Prism.

Generates React Router configuration, App.tsx with RouterProvider,
and main.tsx with urql Provider for frontend applications.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.generators.base import GeneratedFile, GeneratorBase
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import pluralize, to_kebab_case, to_snake_case
from prisme.utils.template_engine import TemplateRenderer

if TYPE_CHECKING:
    from prisme.spec.model import ModelSpec


class RouterGenerator(GeneratorBase):
    """Generator for React Router configuration and app entry files."""

    REQUIRED_TEMPLATES = [
        "frontend/router/router.tsx.jinja2",
        "frontend/router/App.tsx.jinja2",
        "frontend/router/main_urql.tsx.jinja2",
        "frontend/router/main_apollo.tsx.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        frontend_base = Path(self.generator_config.frontend_output)
        self.src_path = frontend_base

        # Initialize template renderer
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_files(self) -> list[GeneratedFile]:
        """Generate router, App.tsx, and main.tsx files."""
        # Only generate if there are frontend-enabled models
        frontend_models = [m for m in self.spec.models if m.expose]
        if not frontend_models:
            return []

        return [
            self._generate_router(frontend_models),
            self._generate_app(),
            self._generate_main(),
        ]

    def _generate_router(self, models: list[ModelSpec]) -> GeneratedFile:
        """Generate router.tsx with routes for all models."""
        imports = []
        routes = []

        # Add auth routes if auth is enabled
        auth_enabled = self.auth_config.enabled
        auth_config = self.auth_config
        if auth_enabled:
            imports.append("import { ProtectedRoute } from './components/auth/ProtectedRoute';")
            imports.append("import { Login } from './pages/Login';")
            imports.append("import { Signup } from './pages/Signup';")
            imports.append("import ProfilePage from './pages/ProfilePage';")
            imports.append("import SettingsPage from './pages/SettingsPage';")
            if auth_config.password_reset:
                imports.append(
                    "import { ForgotPasswordForm } from './components/auth/ForgotPasswordForm';"
                )
                imports.append("import ResetPassword from './pages/ResetPassword';")
            if auth_config.email_verification:
                imports.append("import VerifyEmail from './pages/VerifyEmail';")
            if auth_config.oauth_providers:
                imports.append("import AuthCallback from './pages/AuthCallback';")

        def wrap_element(jsx: str) -> str:
            """Wrap a JSX element with ProtectedRoute if auth is enabled."""
            if auth_enabled:
                return f"<ProtectedRoute>{jsx}</ProtectedRoute>"
            return jsx

        # Error pages (always)
        imports.append("import NotFoundPage from './pages/NotFoundPage';")

        # Dashboard page
        imports.append("import DashboardPage from './pages/DashboardPage';")

        # Search page
        imports.append("import SearchPage from './pages/SearchPage';")
        search_el = wrap_element("<SearchPage />")
        routes.append(f"  {{ path: '/search', element: {search_el} }},")

        for model in models:
            snake_name = to_snake_case(model.name)
            kebab_name = to_kebab_case(snake_name)
            plural_name = pluralize(model.name)
            plural_kebab = pluralize(kebab_name)
            has_form = model.get_frontend_override("generate_form", True)
            has_detail = model.get_frontend_override("generate_detail_view", True)

            if model.has_operation("list"):
                imports.append(f"import {plural_name}ListPage from './pages/{plural_kebab}';")
                el = wrap_element(f"<{plural_name}ListPage />")
                routes.append(f"  {{ path: '/{plural_kebab}', element: {el} }},")

            # Only generate detail route if both operation is enabled AND detail component exists
            if model.has_operation("read") and has_detail:
                imports.append(f"import {model.name}DetailPage from './pages/{plural_kebab}/[id]';")
                el = wrap_element(f"<{model.name}DetailPage />")
                routes.append(f"  {{ path: '/{plural_kebab}/:id', element: {el} }},")

            # Only generate create/edit routes if both operation is enabled AND form exists
            if model.has_operation("create") and has_form:
                imports.append(f"import {model.name}CreatePage from './pages/{plural_kebab}/new';")
                el = wrap_element(f"<{model.name}CreatePage />")
                routes.append(f"  {{ path: '/{plural_kebab}/new', element: {el} }},")

            if model.has_operation("update") and has_form:
                imports.append(
                    f"import {model.name}EditPage from './pages/{plural_kebab}/[id]/edit';"
                )
                el = wrap_element(f"<{model.name}EditPage />")
                routes.append(f"  {{ path: '/{plural_kebab}/:id/edit', element: {el} }},")

            # Import route when enabled
            enable_import = model.get_frontend_override("enable_import", False)
            if enable_import and model.has_operation("create"):
                imports.append(
                    f"import {model.name}ImportPage from './pages/{plural_kebab}/import';"
                )
                el = wrap_element(f"<{model.name}ImportPage />")
                routes.append(f"  {{ path: '/{plural_kebab}/import', element: {el} }},")

        # Profile/settings routes (auth-dependent)
        if auth_enabled:
            profile_el = "<ProtectedRoute><ProfilePage /></ProtectedRoute>"
            settings_el = "<ProtectedRoute><SettingsPage /></ProtectedRoute>"
            routes.append(f"  {{ path: '/profile', element: {profile_el} }},")
            routes.append(f"  {{ path: '/settings', element: {settings_el} }},")

        # Admin panel routes
        admin_panel_enabled = auth_enabled and auth_config.admin_panel.enabled
        admin_path = auth_config.admin_panel.path if admin_panel_enabled else ""
        if admin_panel_enabled:
            imports.append("import AdminLayout from './components/admin/AdminLayout';")
            imports.append("import AdminDashboard from './pages/admin/AdminDashboard';")
            imports.append("import AdminUsers from './pages/admin/AdminUsers';")
            imports.append("import AdminUserDetail from './pages/admin/AdminUserDetail';")
            imports.append("import AdminWhitelist from './pages/admin/AdminWhitelist';")
            imports.append("import AdminRoles from './pages/admin/AdminRoles';")
            imports.append("import AdminPermissions from './pages/admin/AdminPermissions';")
            imports.append("import AdminActivityLog from './pages/admin/AdminActivityLog';")
            imports.append("import BootstrapPage from './pages/auth/BootstrapPage';")

            # Admin routes (wrapped with ProtectedRoute roles={["admin"]})
            routes.append(
                f"  {{ path: '{admin_path}', element: "
                f"<ProtectedRoute roles={{['admin']}}><AdminLayout /></ProtectedRoute>, children: ["
            )
            routes.append("    { index: true, element: <AdminDashboard /> },")
            routes.append("    { path: 'users', element: <AdminUsers /> },")
            routes.append("    { path: 'users/:id', element: <AdminUserDetail /> },")
            routes.append("    { path: 'whitelist', element: <AdminWhitelist /> },")
            routes.append("    { path: 'roles', element: <AdminRoles /> },")
            routes.append("    { path: 'permissions', element: <AdminPermissions /> },")
            routes.append("    { path: 'activity', element: <AdminActivityLog /> },")
            routes.append("  ] },")

        # Build auth routes (rendered outside Layout) if enabled
        auth_routes: list[str] = []
        if auth_enabled:
            auth_routes.append("  { path: '/login', element: <Login /> },")
            auth_routes.append("  { path: '/signup', element: <Signup /> },")
            if auth_config.password_reset:
                auth_routes.append(
                    "  { path: '/forgot-password', element: <ForgotPasswordForm /> },",
                )
                auth_routes.append("  { path: '/reset-password', element: <ResetPassword /> },")
            if auth_config.email_verification:
                auth_routes.append("  { path: '/verify-email', element: <VerifyEmail /> },")
            if auth_config.oauth_providers:
                auth_routes.append("  { path: '/auth/callback', element: <AuthCallback /> },")
            if admin_panel_enabled:
                auth_routes.append("  { path: '/bootstrap', element: <BootstrapPage /> },")

        imports_str = "\n".join(imports)
        routes_str = "\n".join(routes)
        auth_routes_str = "\n".join(auth_routes)

        # Build navigation links for the sidebar (only for models with include_in_nav=True)
        nav_links = []
        for model in models:
            # Skip models that should not appear in navigation
            if not model.get_frontend_override("include_in_nav", True):
                continue

            snake_name = to_snake_case(model.name)
            kebab_name = to_kebab_case(snake_name)
            plural_kebab = pluralize(kebab_name)
            nav_label = model.get_frontend_override("nav_label") or pluralize(model.name)
            backtick = "`"
            nav_links.append(
                f"""          <NavLink
            to="/{plural_kebab}"
            className={{({{ isActive }}) =>
              {backtick}flex items-center gap-3 px-3 py-2 rounded-nordic text-sm font-medium transition-colors ${{
                isActive
                  ? 'bg-nordic-100 text-nordic-900'
                  : 'text-nordic-600 hover:bg-nordic-50 hover:text-nordic-900'
              }}{backtick}
            }}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={{1.5}} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            {nav_label}
          </NavLink>"""
            )

        # Admin nav link is now rendered in the sidebar footer (discrete), not in main nav

        nav_links_str = "\n".join(nav_links)

        # Get project title and description from spec
        project_title = self.spec.effective_title
        project_initial = project_title[0].upper() if project_title else "P"
        project_description = self.spec.description or f"{project_title} - Built with Prism"

        # Auth imports if enabled
        auth_hook_import = (
            "\nimport { useAuth } from './contexts/AuthContext';" if auth_enabled else ""
        )

        # Check if dark mode is enabled
        dark_mode = self.design_config.dark_mode

        content = self.renderer.render_file(
            "frontend/router/router.tsx.jinja2",
            context={
                "imports_str": imports_str,
                "auth_hook_import": auth_hook_import,
                "project_title": project_title,
                "project_initial": project_initial,
                "project_description": project_description,
                "auth_enabled": auth_enabled,
                "dark_mode": dark_mode,
                "nav_links_str": nav_links_str,
                "routes_str": routes_str,
                "auth_routes_str": auth_routes_str,
                "admin_panel_enabled": admin_panel_enabled,
                "admin_path": admin_path,
            },
        )

        return GeneratedFile(
            path=self.src_path / "router.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="React Router configuration with protected regions",
        )

    def _generate_app(self) -> GeneratedFile:
        """Generate App.tsx with RouterProvider."""
        content = self.renderer.render_file(
            "frontend/router/App.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.src_path / "App.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="App component with RouterProvider and protected regions",
        )

    def _generate_main(self) -> GeneratedFile:
        """Generate main.tsx with urql Provider."""
        # Check which GraphQL client is configured
        graphql_client = (
            self.exposure_config.frontend.graphql_client if self.exposure_config else "urql"
        )

        # Check if auth is enabled
        auth_enabled = self.auth_config.enabled

        # Choose the appropriate template based on GraphQL client
        if graphql_client == "urql":
            template_path = "frontend/router/main_urql.tsx.jinja2"
        else:  # Apollo
            template_path = "frontend/router/main_apollo.tsx.jinja2"

        content = self.renderer.render_file(
            template_path,
            context={
                "auth_enabled": auth_enabled,
            },
        )

        return GeneratedFile(
            path=self.src_path / "main.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Application entry point with GraphQL Provider",
        )


__all__ = ["RouterGenerator"]
