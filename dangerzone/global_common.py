import sys
import os
import inspect
import tempfile
import appdirs
import platform
import subprocess
import shlex
import pipes
from PySide2 import QtCore, QtGui, QtWidgets

if platform.system() == "Darwin":
    import CoreServices
    import LaunchServices
    import plistlib

elif platform.system() == "Linux":
    import grp
    import getpass
    from xdg.DesktopEntry import DesktopEntry

from .settings import Settings
from .docker_installer import is_docker_ready


class GlobalCommon(object):
    """
    The GlobalCommon class is a singleton of shared functionality throughout the app
    """

    def __init__(self, app):
        # Qt app
        self.app = app

        # Temporary directory to store pixel data
        # Note in macOS, temp dirs must be in /tmp (or a few other paths) for Docker to mount them
        if platform.system() == "Windows":
            self.pixel_dir = tempfile.TemporaryDirectory(prefix="dangerzone-pixel-")
            self.safe_dir = tempfile.TemporaryDirectory(prefix="dangerzone-safe-")
        else:
            self.pixel_dir = tempfile.TemporaryDirectory(
                prefix="/tmp/dangerzone-pixel-"
            )
            self.safe_dir = tempfile.TemporaryDirectory(prefix="/tmp/dangerzone-safe-")

        # Name of input file
        self.document_filename = None

        # Name of output file
        self.save_filename = None

        # Preload font
        self.fixed_font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)

        # App data folder
        self.appdata_path = appdirs.user_config_dir("dangerzone")

        # In case we have a custom container
        self.custom_container = None

        # dangerzone-container path
        self.dz_container_path = self.get_dangerzone_container_path()

        # Preload list of PDF viewers on computer
        self.pdf_viewers = self._find_pdf_viewers()

        # Languages supported by tesseract
        self.ocr_languages = {
            "Afrikaans": "ar",
            "Albanian": "sqi",
            "Amharic": "amh",
            "Arabic": "ara",
            "Arabic script": "Arabic",
            "Armenian": "hye",
            "Armenian script": "Armenian",
            "Assamese": "asm",
            "Azerbaijani": "aze",
            "Azerbaijani (Cyrillic)": "aze_cyrl",
            "Basque": "eus",
            "Belarusian": "bel",
            "Bengali": "ben",
            "Bengali script": "Bengali",
            "Bosnian": "bos",
            "Breton": "bre",
            "Bulgarian": "bul",
            "Burmese": "mya",
            "Canadian Aboriginal script": "Canadian_Aboriginal",
            "Catalan": "cat",
            "Cebuano": "ceb",
            "Cherokee": "chr",
            "Cherokee script": "Cherokee",
            "Chinese - Simplified": "chi_sim",
            "Chinese - Simplified (vertical)": "chi_sim_vert",
            "Chinese - Traditional": "chi_tra",
            "Chinese - Traditional (vertical)": "chi_tra_vert",
            "Corsican": "cos",
            "Croatian": "hrv",
            "Cyrillic script": "Cyrillic",
            "Czech": "ces",
            "Danish": "dan",
            "Devanagari script": "Devanagari",
            "Divehi": "div",
            "Dutch": "nld",
            "Dzongkha": "dzo",
            "English": "eng",
            "English, Middle (1100-1500)": "enm",
            "Esperanto": "epo",
            "Estonian": "est",
            "Ethiopic script": "Ethiopic",
            "Faroese": "fao",
            "Filipino": "fil",
            "Finnish": "fin",
            "Fraktur script": "Fraktur",
            "Frankish": "frk",
            "French": "fra",
            "French, Middle (ca.1400-1600)": "frm",
            "Frisian (Western)": "fry",
            "Gaelic (Scots)": "gla",
            "Galician": "glg",
            "Georgian": "kat",
            "Georgian script": "Georgian",
            "German": "deu",
            "Greek": "ell",
            "Greek script": "Greek",
            "Gujarati": "guj",
            "Gujarati script": "Gujarati",
            "Gurmukhi script": "Gurmukhi",
            "Hangul script": "Hangul",
            "Hangul (vertical) script": "Hangul_vert",
            "Han - Simplified script": "HanS",
            "Han - Simplified (vertical) script": "HanS_vert",
            "Han - Traditional script": "HanT",
            "Han - Traditional (vertical) script": "HanT_vert",
            "Hatian": "hat",
            "Hebrew": "heb",
            "Hebrew script": "Hebrew",
            "Hindi": "hin",
            "Hungarian": "hun",
            "Icelandic": "isl",
            "Indonesian": "ind",
            "Inuktitut": "iku",
            "Irish": "gle",
            "Italian": "ita",
            "Italian - Old": "ita_old",
            "Japanese": "jpn",
            "Japanese script": "Japanese",
            "Japanese (vertical)": "jpn_vert",
            "Japanese (vertical) script": "Japanese_vert",
            "Javanese": "jav",
            "Kannada": "kan",
            "Kannada script": "Kannada",
            "Kazakh": "kaz",
            "Khmer": "khm",
            "Khmer script": "Khmer",
            "Korean": "kor",
            "Korean (vertical)": "kor_vert",
            "Kurdish (Arabic)": "kur_ara",
            "Kyrgyz": "kir",
            "Lao": "lao",
            "Lao script": "Lao",
            "Latin": "lat",
            "Latin script": "Latin",
            "Latvian": "lav",
            "Lithuanian": "lit",
            "Luxembourgish": "ltz",
            "Macedonian": "mkd",
            "Malayalam": "mal",
            "Malayalam script": "Malayalam",
            "Malay": "msa",
            "Maltese": "mlt",
            "Maori": "mri",
            "Marathi": "mar",
            "Mongolian": "mon",
            "Myanmar script": "Myanmar",
            "Nepali": "nep",
            "Norwegian": "nor",
            "Occitan (post 1500)": "oci",
            "Old Georgian": "kat_old",
            "Oriya (Odia) script": "Oriya",
            "Oriya": "ori",
            "Pashto": "pus",
            "Persian": "fas",
            "Polish": "pol",
            "Portuguese": "por",
            "Punjabi": "pan",
            "Quechua": "que",
            "Romanian": "ron",
            "Russian": "rus",
            "Sanskrit": "san",
            "script and orientation": "osd",
            "Serbian (Latin)": "srp_latn",
            "Serbian": "srp",
            "Sindhi": "snd",
            "Sinhala script": "Sinhala",
            "Sinhala": "sin",
            "Slovakian": "slk",
            "Slovenian": "slv",
            "Spanish, Castilian - Old": "spa_old",
            "Spanish": "spa",
            "Sundanese": "sun",
            "Swahili": "swa",
            "Swedish": "swe",
            "Syriac script": "Syriac",
            "Syriac": "syr",
            "Tajik": "tgk",
            "Tamil script": "Tamil",
            "Tamil": "tam",
            "Tatar": "tat",
            "Telugu script": "Telugu",
            "Telugu": "tel",
            "Thaana script": "Thaana",
            "Thai script": "Thai",
            "Thai": "tha",
            "Tibetan script": "Tibetan",
            "Tibetan Standard": "bod",
            "Tigrinya": "tir",
            "Tonga": "ton",
            "Turkish": "tur",
            "Ukrainian": "ukr",
            "Urdu": "urd",
            "Uyghur": "uig",
            "Uzbek (Cyrillic)": "uzb_cyrl",
            "Uzbek": "uzb",
            "Vietnamese script": "Vietnamese",
            "Vietnamese": "vie",
            "Welsh": "cym",
            "Yiddish": "yid",
            "Yoruba": "yor",
        }

        # Load settings
        self.settings = Settings(self)

    def get_container_name(self):
        if self.custom_container:
            return self.custom_container
        else:
            return "flmcode/dangerzone"

    def get_resource_path(self, filename):
        if getattr(sys, "dangerzone_dev", False):
            # Look for resources directory relative to python file
            prefix = os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(inspect.getfile(inspect.currentframe()))
                    )
                ),
                "share",
            )
        else:
            if platform.system() == "Darwin":
                prefix = os.path.join(
                    os.path.dirname(os.path.dirname(sys.executable)), "Resources/share"
                )
            elif platform.system() == "Linux":
                prefix = os.path.join(sys.prefix, "share", "dangerzone")
            else:
                # Windows
                prefix = os.path.join(os.path.dirname(sys.executable), "share")

        resource_path = os.path.join(prefix, filename)
        return resource_path

    def get_dangerzone_container_path(self):
        if getattr(sys, "dangerzone_dev", False):
            # Look for resources directory relative to python file
            return os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(inspect.getfile(inspect.currentframe()))
                    )
                ),
                "dev_scripts",
                "dangerzone-container",
            )
        else:
            if platform.system() == "Darwin":
                return os.path.join(
                    os.path.dirname(sys.executable), "dangerzone-container"
                )
            elif platform.system() == "Windows":
                return os.path.join(
                    os.path.dirname(sys.executable), "dangerzone-container.exe"
                )
            else:
                return "/usr/bin/dangerzone-container"

    def exec_dangerzone_container(self, args):
        # Prefix the args with the retainer runtime, and in the case linux when the user isn't in the docker group, pkexec
        if platform.system() == "Linux":
            if self.settings.get("linux_prefers_typing_password"):
                args = ["/usr/bin/pkexec", self.dz_container_path] + args
            else:
                args = [self.dz_container_path] + args
        else:
            args = [self.dz_container_path] + args

        # Execute dangerzone-container
        args_str = " ".join(pipes.quote(s) for s in args)
        print(f"Executing: {args_str}")
        return subprocess.Popen(
            args,
            startupinfo=self.get_subprocess_startupinfo(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def get_window_icon(self):
        if platform.system() == "Windows":
            path = self.get_resource_path("dangerzone.ico")
        else:
            path = self.get_resource_path("icon.png")
        return QtGui.QIcon(path)

    def open_pdf_viewer(self, filename):
        if self.settings.get("open_app") in self.pdf_viewers:
            if platform.system() == "Darwin":
                # Get the PDF reader bundle command
                bundle_identifier = self.pdf_viewers[self.settings.get("open_app")]
                args = ["open", "-b", bundle_identifier, filename]

                # Run
                print(f"Executing: {' '.join(args)}")
                subprocess.run(args)

            elif platform.system() == "Linux":
                # Get the PDF reader command
                args = shlex.split(self.pdf_viewers[self.settings.get("open_app")])
                # %f, %F, %u, and %U are filenames or URLS -- so replace with the file to open
                for i in range(len(args)):
                    if (
                        args[i] == "%f"
                        or args[i] == "%F"
                        or args[i] == "%u"
                        or args[i] == "%U"
                    ):
                        args[i] = filename

                # Open as a background process
                print(f"Executing: {' '.join(args)}")
                subprocess.Popen(args)

    def _find_pdf_viewers(self):
        pdf_viewers = {}

        if platform.system() == "Darwin":
            # Get all installed apps that can open PDFs
            bundle_identifiers = LaunchServices.LSCopyAllRoleHandlersForContentType(
                "com.adobe.pdf", CoreServices.kLSRolesAll
            )
            for bundle_identifier in bundle_identifiers:
                # Get the filesystem path of the app
                res = LaunchServices.LSCopyApplicationURLsForBundleIdentifier(
                    bundle_identifier, None
                )
                if res[0] is None:
                    continue
                app_url = res[0][0]
                app_path = str(app_url.path())

                # Load its plist file
                plist_path = os.path.join(app_path, "Contents/Info.plist")

                # Skip if there's not an Info.plist
                if not os.path.exists(plist_path):
                    continue

                with open(plist_path, "rb") as f:
                    plist_dict = plistlib.load(plist_path)

                if (
                    plist_dict.get("CFBundleName")
                    and plist_dict["CFBundleName"] != "Dangerzone"
                ):
                    pdf_viewers[plist_dict["CFBundleName"]] = bundle_identifier

        elif platform.system() == "Linux":
            # Find all .desktop files
            for search_path in [
                "/usr/share/applications",
                "/usr/local/share/applications",
                os.path.expanduser("~/.local/share/applications"),
            ]:
                try:
                    for filename in os.listdir(search_path):
                        full_filename = os.path.join(search_path, filename)
                        if os.path.splitext(filename)[1] == ".desktop":

                            # See which ones can open PDFs
                            desktop_entry = DesktopEntry(full_filename)
                            if (
                                "application/pdf" in desktop_entry.getMimeTypes()
                                and desktop_entry.getName() != "dangerzone"
                            ):
                                pdf_viewers[
                                    desktop_entry.getName()
                                ] = desktop_entry.getExec()

                except FileNotFoundError:
                    pass

        return pdf_viewers

    def ensure_docker_group_preference(self):
        # If the user prefers typing their password
        if self.settings.get("linux_prefers_typing_password") == True:
            return True

        # Get the docker group
        try:
            groupinfo = grp.getgrnam("docker")
        except:
            # Ignore if group is not found
            return True

        # See if the user is in the group
        username = getpass.getuser()
        if username not in groupinfo.gr_mem:
            # User is not in the docker group, ask if they prefer typing their password
            message = "<b>Dangerzone requires Docker</b><br><br>In order to use Docker, your user must be in the 'docker' group or you'll need to type your password each time you run dangerzone.<br><br><b>Adding your user to the 'docker' group is more convenient but less secure</b>, and will require just typing your password once. Which do you prefer?"
            return_code = Alert(
                self,
                message,
                ok_text="I'll type my password each time",
                extra_button_text="Add my user to the 'docker' group",
            ).launch()
            if return_code == QtWidgets.QDialog.Accepted:
                # Prefers typing password
                self.settings.set("linux_prefers_typing_password", True)
                self.settings.save()
                return True
            elif return_code == 2:
                # Prefers being in the docker group
                self.settings.set("linux_prefers_typing_password", False)
                self.settings.save()

                # Add user to the docker group
                p = subprocess.run(
                    [
                        "/usr/bin/pkexec",
                        "/usr/sbin/usermod",
                        "-a",
                        "-G",
                        "docker",
                        username,
                    ]
                )
                if p.returncode == 0:
                    message = "Great! Now you must log out of your computer and log back in, and then you can use Dangerzone."
                    Alert(self, message).launch()
                else:
                    message = "Failed to add your user to the 'docker' group, quitting."
                    Alert(self, message).launch()

                return False
            else:
                # Cancel
                return False

        return True

    def ensure_docker_service_is_started(self):
        if not is_docker_ready(self):
            message = "<b>Dangerzone requires Docker</b><br><br>Docker should be installed, but it looks like it's not running in the background.<br><br>Click Ok to try starting the docker service. You will have to type your login password."
            if Alert(self, message).launch() == QtWidgets.QDialog.Accepted:
                p = subprocess.run(
                    [
                        "/usr/bin/pkexec",
                        self.get_resource_path("enable_docker_service.sh"),
                    ]
                )
                if p.returncode == 0:
                    # Make sure docker is now ready
                    if is_docker_ready(self):
                        return True
                    else:
                        message = "Restarting docker appeared to work, but the service still isn't responding, quitting."
                        Alert(self, message).launch()
                else:
                    message = "Failed to start the docker service, quitting."
                    Alert(self, message).launch()

            return False

        return True

    def get_subprocess_startupinfo(self):
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            return startupinfo
        else:
            return None


class Alert(QtWidgets.QDialog):
    def __init__(self, common, message, ok_text="Ok", extra_button_text=None):
        super(Alert, self).__init__()
        self.common = common

        self.setWindowTitle("dangerzone")
        self.setWindowIcon(self.common.get_window_icon())
        self.setModal(True)

        flags = (
            QtCore.Qt.CustomizeWindowHint
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowCloseButtonHint
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setWindowFlags(flags)

        logo = QtWidgets.QLabel()
        logo.setPixmap(
            QtGui.QPixmap.fromImage(
                QtGui.QImage(self.common.get_resource_path("icon.png"))
            )
        )

        label = QtWidgets.QLabel()
        label.setText(message)
        label.setWordWrap(True)

        message_layout = QtWidgets.QHBoxLayout()
        message_layout.addWidget(logo)
        message_layout.addSpacing(10)
        message_layout.addWidget(label, stretch=1)

        ok_button = QtWidgets.QPushButton(ok_text)
        ok_button.clicked.connect(self.clicked_ok)
        if extra_button_text:
            extra_button = QtWidgets.QPushButton(extra_button_text)
            extra_button.clicked.connect(self.clicked_extra)
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.clicked_cancel)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_button)
        if extra_button_text:
            buttons_layout.addWidget(extra_button)
        buttons_layout.addWidget(cancel_button)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(message_layout)
        layout.addSpacing(10)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def clicked_ok(self):
        self.done(QtWidgets.QDialog.Accepted)

    def clicked_extra(self):
        self.done(2)

    def clicked_cancel(self):
        self.done(QtWidgets.QDialog.Rejected)

    def launch(self):
        return self.exec_()
