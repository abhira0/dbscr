ROOT_URL = "https://scrolller.com/"

BASE_PATH = "scrolller"  # base


IDM_PATH = "C:\Program Files (x86)\Internet Download Manager\IDMan.exe"
BATCH_PATH = "scrolller\\download.bat"

SAVING_INTERVAL = 10
CONF = {
    "thread": {"media": 30, "album": 30, "download": 30},
    "reset": {"query": 500},
    "stop": 100000,
}

CN = 105  # [i] normal-text -> purple-magenta
CC = (78, 201, 176)  # Class name -> Greenish (vscode-clr)
CU = "magenta"  # URL -> magenta
CA = 99  # contrast of CB -> light magenta
CB = 201  # contrast of CA -> pink
CT = (167, 206, 155)  # time, numbers -> light green (vscode-clr)

CS = (22, 198, 12)  # success -> green
CW = (252, 225, 0)  # warning -> yellow
CE = "red"  # error -> red

TMP_I = ["i", CB, CA]
TMP_E = ["!", CA, "red"]
