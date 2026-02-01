"""CLI for installing/uninstalling Cynex viewer in MLflow."""

import argparse
import shutil
import sys
from pathlib import Path


def get_mlflow_static_dir() -> Path:
    """Find MLflow's static files directory."""
    try:
        import mlflow.server
        server_path = Path(mlflow.server.__file__).parent
        static_dir = server_path / "js" / "build"
        if static_dir.exists():
            return static_dir
    except ImportError:
        pass

    print("Error: Could not find MLflow installation", file=sys.stderr)
    sys.exit(1)


def get_package_static_dir() -> Path:
    """Get the static files bundled with this package."""
    return Path(__file__).parent / "static"


INJECTOR_SCRIPT = '''\
// Cynex viewer integration for MLflow
(function() {
  const CYNEX_BASE = '/static-files/cynex/index.html';

  function isTrajectoryFile(path) {
    if (!path || !path.endsWith('.json')) return false;
    // Check if in trajectories/ folder
    if (path.includes('trajectories/') || path.startsWith('trajectories/')) return true;
    // Check if filename matches *-trajectory.json or *_trajectory.json
    const filename = path.split('/').pop();
    return /-trajectory\\.json$/.test(filename) || /_trajectory\\.json$/.test(filename);
  }

  function getArtifactPath() {
    const spans = document.querySelectorAll('span[title*="/"]');
    for (const span of spans) {
      const title = span.getAttribute('title');
      if (title && title.endsWith('.json') && !title.startsWith('mlflow-artifacts:')) {
        return title;
      }
    }

    const pathDivs = document.querySelectorAll('div[title*="mlflow-artifacts:"]');
    for (const div of pathDivs) {
      const title = div.getAttribute('title');
      if (title && title.endsWith('.json')) {
        const match = title.match(/artifacts\\/(.+)$/);
        if (match) return match[1];
      }
    }

    return null;
  }

  function addCynexButton() {
    const url = window.location.href;
    const runMatch = url.match(/runs\\/([a-f0-9]+)/);
    if (!runMatch) return;

    const runId = runMatch[1];
    const artifactPath = getArtifactPath();

    if (!artifactPath || !isTrajectoryFile(artifactPath)) {
      removeButton();
      return;
    }

    const cynexUrl = `${CYNEX_BASE}?file=/get-artifact?path=${encodeURIComponent(artifactPath)}%26run_uuid=${runId}`;

    let btn = document.getElementById('cynex-view-btn');
    if (btn) {
      btn.href = cynexUrl;
      return;
    }

    const downloadBtn = document.querySelector('[data-component-id*="artifactview"][data-component-id*="337"]');
    if (!downloadBtn) return;

    const container = downloadBtn.parentElement;
    if (!container) return;

    btn = document.createElement('a');
    btn.id = 'cynex-view-btn';
    btn.href = cynexUrl;
    btn.target = '_blank';
    btn.textContent = 'View in Cynex';
    btn.className = 'du-bois-light-btn du-bois-light-btn-link';
    btn.style.cssText = `
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin-left: 8px;
      padding: 0 8px;
      height: 32px;
      text-decoration: none;
      font-size: 14px;
      color: #2272b4;
      white-space: nowrap;
    `;

    container.parentElement.appendChild(btn);
  }

  function removeButton() {
    const btn = document.getElementById('cynex-view-btn');
    if (btn) btn.remove();
  }

  let lastPath = '';
  setInterval(() => {
    const url = window.location.href;
    if (url.includes('/runs/') && url.includes('/artifacts')) {
      const currentPath = getArtifactPath();
      if (currentPath !== lastPath) {
        lastPath = currentPath;
        if (currentPath && isTrajectoryFile(currentPath)) {
          addCynexButton();
        } else {
          removeButton();
        }
      }
    } else {
      removeButton();
      lastPath = '';
    }
  }, 500);
})();
'''


def install():
    """Install Cynex viewer into MLflow."""
    mlflow_dir = get_mlflow_static_dir()
    package_static = get_package_static_dir()
    cynex_source = package_static / "cynex"

    if not cynex_source.exists():
        print("Error: Cynex static files not found in package", file=sys.stderr)
        print(f"Expected at: {cynex_source}", file=sys.stderr)
        sys.exit(1)

    # Copy cynex viewer
    cynex_dest = mlflow_dir / "cynex"
    if cynex_dest.exists():
        shutil.rmtree(cynex_dest)
    shutil.copytree(cynex_source, cynex_dest)
    print(f"Copied Cynex viewer to {cynex_dest}")

    # Write injector script
    injector_path = mlflow_dir / "cynex-injector.js"
    injector_path.write_text(INJECTOR_SCRIPT)
    print(f"Created injector script at {injector_path}")

    # Patch index.html
    index_path = mlflow_dir / "index.html"
    index_content = index_path.read_text()

    script_tag = '<script src="static-files/cynex-injector.js"></script>'
    if script_tag not in index_content:
        index_content = index_content.replace(
            '</body></html>',
            f'{script_tag}</body></html>'
        )
        index_path.write_text(index_content)
        print("Patched MLflow index.html")
    else:
        print("MLflow index.html already patched")

    print("\nCynex viewer installed successfully!")
    print("Restart MLflow server to see changes.")


def uninstall():
    """Remove Cynex viewer from MLflow."""
    mlflow_dir = get_mlflow_static_dir()

    # Remove cynex directory
    cynex_dir = mlflow_dir / "cynex"
    if cynex_dir.exists():
        shutil.rmtree(cynex_dir)
        print(f"Removed {cynex_dir}")

    # Remove injector script
    injector_path = mlflow_dir / "cynex-injector.js"
    if injector_path.exists():
        injector_path.unlink()
        print(f"Removed {injector_path}")

    # Unpatch index.html
    index_path = mlflow_dir / "index.html"
    index_content = index_path.read_text()
    script_tag = '<script src="static-files/cynex-injector.js"></script>'
    if script_tag in index_content:
        index_content = index_content.replace(script_tag, '')
        index_path.write_text(index_content)
        print("Removed script tag from index.html")

    print("\nCynex viewer uninstalled.")


def status():
    """Check if Cynex is installed in MLflow."""
    mlflow_dir = get_mlflow_static_dir()

    cynex_installed = (mlflow_dir / "cynex").exists()
    injector_installed = (mlflow_dir / "cynex-injector.js").exists()

    index_path = mlflow_dir / "index.html"
    index_patched = '<script src="static-files/cynex-injector.js"></script>' in index_path.read_text()

    print(f"MLflow static directory: {mlflow_dir}")
    print(f"Cynex viewer: {'installed' if cynex_installed else 'not installed'}")
    print(f"Injector script: {'installed' if injector_installed else 'not installed'}")
    print(f"Index.html: {'patched' if index_patched else 'not patched'}")

    if cynex_installed and injector_installed and index_patched:
        print("\nStatus: Fully installed")
    elif not cynex_installed and not injector_installed and not index_patched:
        print("\nStatus: Not installed")
    else:
        print("\nStatus: Partially installed (run 'mlflow-cynex install' to fix)")


def main():
    parser = argparse.ArgumentParser(
        description="Manage Cynex trajectory viewer integration with MLflow"
    )
    parser.add_argument(
        "command",
        choices=["install", "uninstall", "status"],
        help="Command to run"
    )

    args = parser.parse_args()

    if args.command == "install":
        install()
    elif args.command == "uninstall":
        uninstall()
    elif args.command == "status":
        status()


if __name__ == "__main__":
    main()
