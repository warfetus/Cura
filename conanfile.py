import os
import shutil
import pathlib

from conan.tools.env.virtualbuildenv import VirtualBuildEnv
from conan.tools.env.environment import Environment
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake
from conan.tools.layout import cmake_layout
from conans import ConanFile, tools

required_conan_version = ">=1.44.1"


class CuraConan(ConanFile):
    name = "cura"
    version = "5.0.0"
    license = "LGPL-3.0"
    author = "Ultimaker B.V."
    url = "https://github.com/Ultimaker/cura"
    description = "3D printer / slicing GUI built on top of the Uranium framework"
    topics = ("conan", "python", "pyqt5", "qt", "qml", "3d-printing", "slicer")
    settings = "os", "compiler", "build_type", "arch"
    revision_mode = "scm"
    build_policy = "missing"
    default_user = "ultimaker"
    default_channel = "testing"
    exports = ["LICENSE*",
               str(os.path.join(".conan_gen", "Cura.run.xml.jinja")),
               str(os.path.join(".conan_gen", "CuraVersion.py"))]
    base_path = pathlib.Path(__file__).parent.absolute()
    python_requires = ["VirtualEnvironmentBuildTool/0.2@ultimaker/testing",
                       "PyCharmRunEnvironment/0.1@ultimaker/testing",
                       "UltimakerBase/0.1@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    pycharm_targets = [
        {
            "jinja_path": str(os.path.join(base_path, ".conan_gen", "Cura.run.xml.jinja")),
            "name": "cura_app",
            "entry_point": "cura_app.py",
            "arguments": "",
            "run_path": str(os.path.join(base_path, ".run"))
        },
        {
            "jinja_path": str(os.path.join(base_path, ".conan_gen", "Cura.run.xml.jinja")),
            "name": "cura_app_external_engine",
            "entry_point": "cura_app.py",
            "arguments": "--external",
            "run_path": str(os.path.join(base_path, ".run"))
        }
    ]
    options = {
        "enterprise": [True, False],
        "staging": [True, False],
        "external_engine": [True, False],
        "testing": [True, False],
        "devtools": [True, False]
    }
    default_options = {
        "enterprise": False,
        "staging": False,
        "external_engine": False,
        "testing": False,
        "devtools": False
    }
    scm = {
        "type": "git",
        "subfolder": ".",
        "url": "auto",
        "revision": "auto"
    }
    build_requires = ["python/3.10.2@python/stable"]

    def requirements(self):
        self.requires("python/3.10.2@python/stable")
        self.requires("charon/[~=5.0.0-a]@ultimaker/testing")
        self.requires("pynest2d/[~=5.0.0-a]@ultimaker/testing")
        self.requires("savitar/[~=5.0.0-a]@ultimaker/testing")
        self.requires("uranium/[~=5.0.0-a]@ultimaker/testing")
        self.requires("curaengine/[~=5.0.0-a]@ultimaker/testing")
        self.requires("fdm_materials/[~=5.0.0-a]@ultimaker/testing")
        self.requires("numpy/1.21.5@python/stable")
        self.requires("pyqt5/5.15.2@python/stable")
        self.requires("sentry-sdk/0.13.5@python/stable")
        self.requires("trimesh/3.9.36@python/stable")
        self.requires("certifi/2019.11.28@python/stable")
        self.requires("keyring/23.0.1@python/stable")
        self.requires("pyserial/3.4@python/stable")
        self.requires("zeroconf/0.31.0@python/stable")
        if self.options.testing:
            self.requires("pytest/5.2.1@python/stable")
        if self.options.devtools:
            self.requires("mypy/0.740@python/stable")

    def layout(self):
        cmake_layout(self)
        self.folders.imports = "venv"
        self.folders.generators = "venv"

    def generate(self):
        v = tools.Version(self.version)
        env = Environment()
        env.define("CURA_APP_DISPLAY_NAME", self.name)
        env.define("CURA_VERSION", f"{self.version}")
        env.define("CURA_BUILD_TYPE", "Enterprise" if self.options.enterprise else "")
        staging = "-staging" if self.options.staging else ""
        env.define("CURA_CLOUD_API_ROOT", f"https://api{staging}.ultimaker.com")
        env.define("CURA_CLOUD_ACCOUNT_API_ROOT", f"https://account{staging}.ultimaker.com")
        env.define("CURA_DIGITAL_FACTORY_URL", f"https://digitalfactory{staging}.ultimaker.com")
        envvars = env.vars(self, scope = "run")
        envvars.save_script("test")

        cmake = CMakeDeps(self)
        cmake.generate()

        tc = CMakeToolchain(self)
        tc.variables["Python_VERSION"] = self.dependencies["python"].ref.version
        tc.variables["URANIUM_DIR"] = os.path.join(self.dependencies["uranium"].package_folder, "")
        tc.generate()

        be = VirtualBuildEnv(self)  # Make sure we use our own Python
        be.generate()

        # Create the Virtual environment
        vb = self.python_requires["VirtualEnvironmentBuildTool"].module.VirtualEnvironmentBuildTool(self)
        vb.configure(os.path.join(self.dependencies["python"].package_folder, self.dependencies["python"].cpp_info.bindirs[0], "python3"))
        vb.generate(pip_deps = "")

        # create the pycharm run configurations
        pb = self.python_requires["PyCharmRunEnvironment"].module.PyCharmRunEnvironment(self)
        pb.generate(env)

        # Install CuraVersion.py
        curaversion_src = pathlib.Path(os.path.join(self.base_path, ".conan_gen", "CuraVersion.py"))
        curaversion_dst = pathlib.Path(os.path.join(self.base_path, "cura", "CuraVersion.py"))

        if curaversion_dst.exists():
            os.remove(curaversion_dst)
        shutil.copy(curaversion_src, curaversion_dst)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
        cmake.install()

    def imports(self):
        v = tools.Version(self.dependencies["python"].ref.version)
        self.copy("*", dst = os.path.join("lib", f"python{v.major}.{v.minor}", "site-packages"), src = os.path.join("lib", f"python{v.major}.{v.minor}", "site-packages"))
        self.copy("CuraEngine*", dst = "..", src = "bin", root_package = "curaengine")
        self.copy("*.fdm_material", dst = os.path.join("..", "resources", "materials"), src = "res", root_package = "fdm_materials")
