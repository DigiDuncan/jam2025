# nuitka-project: --include-package-data=resources
# nuitka-project: --force-stderr-spec=err.txt
# nuitka-project: --report=compilation-report.xml
# nuitka-project: --standalone
# nuitka-project: --product-name="template"
# nuitka-project: --product-version="0.0.0.0"
# nuitka-project: --file-description=""
# nuitka-project-if: {OS} == "Darwin":
#   nuitka-project: --macos-create-app-bundle
#   nuitka-project: --macos-app-icon=icon.png
# nuitka-project-if: {OS} == "Windows":
#   nuitka-project: --windows-console-mode=disable
#   nuitka-project: --windows-icon-from-ico=icon.png

from .launch import launch

if __name__ == "__main__":
    launch()
