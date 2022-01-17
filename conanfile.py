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
        "external_engine": [True, False]
    }
    default_options = {
        "enterprise": False,
        "staging": False,
        "external_engine": False
    }
    scm = {
        "type": "git",
        "subfolder": ".",
        "url": "auto",
        "revision": "auto"
    }
    build_requires = ["python/3.10.0@python/stable"]

    def layout(self):
        cmake_layout(self)
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

        # Make sure CuraEngine exist at the root
        ext = ""
        if self.settings.os == "Windows":
            ext = ".exe"
        curaengine_src = pathlib.Path(os.path.join(self.dependencies['curaengine'].package_folder, self.dependencies["curaengine"].cpp_info.bindirs[0], f"CuraEngine{ext}"))
        curaengine_dst = pathlib.Path(os.path.join(self.base_path, f"CuraEngine{ext}"))
        if os.path.exists(curaengine_dst):
            os.remove(curaengine_dst)
        try:
            curaengine_dst.symlink_to(curaengine_src)
        except OSError as e:
            self.output.warn("Could not create symlink to CuraEngine copying instead")
            shutil.copy(curaengine_src, curaengine_dst)

        tc = CMakeToolchain(self)
        tc.variables["Python_VERSION"] = self.dependencies["python"].ref.version
        tc.variables["URANIUM_DIR"] = os.path.join(self.dependencies["uranium"].package_folder, "")
        tc.generate()

        be = VirtualBuildEnv(self)  # Make sure we use our own Python
        be.generate()

        # Create the Virtual environment
        vb = self.python_requires["VirtualEnvironmentBuildTool"].module.VirtualEnvironmentBuildTool(self)
        vb.configure(os.path.join(self.dependencies["python"].package_folder, self.dependencies["python"].cpp_info.bindirs[0], "python3"))
        # FIXME: create propper deps
        vb.generate(pip_deps = "numpy==1.21.5 scipy==1.7.3 shapely==1.7.1 appdirs==1.4.3 certifi==2019.11.28 cffi==1.14.1 chardet==3.0.4 cryptography==3.4.6 decorator==4.4.0 idna==2.8 importlib-metadata==3.7.2 netifaces==0.10.9 networkx==2.3 numpy-stl==2.10.1 packaging==18.0 pycollada==0.6 pycparser==2.19 pyparsing==2.4.2 PyQt5==5.15.4 pyserial==3.4 python-dateutil==2.8.0 python-utils==2.3.0 requests==2.22.0 sentry-sdk==0.13.5 six==1.12.0 trimesh==3.2.33 twisted==21.2.0 urllib3==1.25.8 zeroconf==0.31.0 keyring==23.0.1")

        # create the pycharm run configurations
        pb = self.python_requires["PyCharmRunEnvironment"].module.PyCharmRunEnvironment(self)
        pb.generate(env)

        # Install materials
        materials_src = pathlib.Path(os.path.join(self.dependencies['fdm_materials'].package_folder, self.dependencies["fdm_materials"].cpp_info.resdirs[0], "fdm_materials"))
        materials_dst = pathlib.Path(os.path.join(self.base_path, "resources", "materials", "fdm_materials"))
        material_root = os.path.join(self.base_path, "resources", "materials")
        os.makedirs(material_root, exist_ok = True)
        if os.path.exists(materials_dst):
            if materials_dst.is_symlink():
                os.remove(materials_dst)
            else:
                materials_dst.rmdir()
        try:
            materials_dst.symlink_to(materials_src)
        except OSError as e:
            self.output.warn("Could not create symlink to fdm_materials copying instead")
            shutil.copy(materials_src, materials_dst)

        # Install CuraVersion.py
        curaversion_src = pathlib.Path(os.path.join(self.base_path, ".conan_gen", "CuraVersion.py"))
        curaversion_dst = pathlib.Path(os.path.join(self.base_path, "cura", "CuraVersion.py"))

        if curaversion_dst.exists():
            os.remove(curaengine_dst)
        shutil.copy(curaversion_src, curaversion_dst)

    def requirements(self):
        self.requires(f"python/3.10.0@python/stable")
        self.requires(f"charon/[~=5.0.0-a]@ultimaker/testing")
        self.requires(f"pynest2d/[~=5.0.0-a]@ultimaker/testing")
        self.requires(f"savitar/[~=5.0.0-a]@ultimaker/testing")
        self.requires(f"uranium/[~=5.0.0-a]@ultimaker/testing")
        self.requires(f"curaengine/[~=5.0.0-a]@ultimaker/testing")
        self.requires(f"fdm_materials/[~=5.0.0-a]@ultimaker/testing")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
        cmake.install()
