# Pyth-on-line

> A browser-based Python development environment with hot module reloading

Pyth-on-line is a comprehensive web-based Python development platform that runs entirely in your browser using WebAssembly. Built with SvelteKit and powered by Pyodide, it provides a modern, interactive Python development experience without requiring any local installations.

## 🚀 Features

### Core Capabilities

- **Browser-based Python interpreter** - Full CPython experience running on WebAssembly via Pyodide
- **Interactive code execution** - Run Python code with real-time output and interactive debugging
- **Package management** - Support for pure Python packages and many popular libraries (NumPy, Pandas, SciPy, etc.)
- **Hot Module Reloading** - Advanced reactivity system for efficient code reloading
- **Multi-format support** - Work with Jupyter notebooks, Python scripts, and interactive sessions

### Development Environment

- **Workspace management** - Organize projects with file trees and multiple editors
- **GitHub integration** - Import and export projects directly from/to GitHub repositories
- **Gist support** - Share code snippets via GitHub Gists
- **Real-time collaboration** - Share interactive Python sessions with others

### Advanced Features

- **Top-level await support** - Use async/await at the module level
- **Web API access** - Interact with browser APIs and make HTTP requests
- **Rich debugging** - Native Python tracebacks and error handling
- **Package installation** - Install packages from PyPI using micropip

## 🏗️ Architecture

This project is structured as a monorepo containing:

### Web Application (`src/`)

- **SvelteKit frontend** - Modern web interface built with Svelte and TypeScript
- **Pyodide integration** - WebAssembly Python runtime
- **Monaco Editor** - Advanced code editing with syntax highlighting
- **Workspace system** - File management and project organization

### HMR Library (`packages/hmr/`)

Hot Module Reload system for Python that provides:

- **Dependency tracking** - Runtime analysis of module dependencies
- **Selective reloading** - Only reload modules that have changed
- **Push-pull reactivity** - Efficient update propagation
- **CLI interface** - Command-line tool for local development

## 🛠️ Development

### Prerequisites

- Node.js 18+ and pnpm
- Python 3.13+ (for HMR development)

### Getting Started

```bash
# Clone the repository
git clone https://github.com/promplate/pyth-on-line.git
cd pyth-on-line

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

### Project Structure

```
├── src/                    # SvelteKit web application
│   ├── routes/            # Page routes and API endpoints
│   ├── lib/               # Shared components and utilities
│   ├── content/           # Static content (about page, etc.)
│   └── python/            # Python runtime configuration
├── packages/
│   └── hmr/              # Hot Module Reload library
├── tests/                 # Python test suite
└── static/               # Static assets
```

### Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm preview` - Preview production build
- `pnpm check` - Type checking with svelte-check
- `pnpm lint` - Lint code with ESLint

## 🔧 HMR Library

The included HMR (Hot Module Reload) library provides efficient code reloading for Python development:

```bash
# Install HMR globally
pip install hmr

# Use instead of python command
hmr your_script.py

# Or with arguments
hmr your_script.py --arg1 value1
```

### HMR Features

- **Runtime dependency tracking** - Monitors module relationships during execution
- **Selective reloading** - Only reloads changed modules and their dependents
- **Preserves state** - Maintains application state across reloads where possible
- **Virtual environment support** - Works with all Python package managers

## 🌐 Deployment

The application is designed for easy deployment on modern web platforms:

- **Netlify** - Configured with `@sveltejs/adapter-netlify`
- **Static hosting** - Can be deployed as a static site
- **CDN friendly** - Optimized for content delivery networks

## 🤝 Contributing

We welcome contributions! Please see our [contributing guidelines](./CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](./LICENSE).

## 🙏 Acknowledgments

- **[Pyodide](https://github.com/pyodide/pyodide)** - WebAssembly Python runtime
- **[StackBlitz](https://stackblitz.com/)** - Inspiration for browser-based development
- **[Marimo](https://github.com/marimo-team/marimo)** - Reactive notebook concepts
- **[CodePen](https://codepen.io/)** - Interactive code sharing ideas

## 📞 Support

- **Discussions** - [GitHub Discussions](https://github.com/promplate/pyth-on-line/discussions)
- **Issues** - [GitHub Issues](https://github.com/promplate/pyth-on-line/issues)
- **Documentation** - [Project Wiki](https://github.com/promplate/pyth-on-line/wiki)

---

Built with ❤️ by the Promplate team
