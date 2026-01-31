class Speed:

    FASTEST=0.0005
    FAST=0.001
    MIDDLE=0.005
    SLOW=0.01
    SLOWEST=0.05

SYS_SPEED=Speed.MIDDLE
SHOW_DEBUG=True
SHOW_Log=True

class BColors:
    
    TWHITE = '\033[32m'
    TGREY = '\033[90m'
    TRED = '\033[31m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    LOG ='\033[96m'
    WARNING = '\033[45m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

def debug(*msg):
    if(SHOW_DEBUG):
        print(BColors.TGREY,msg,BColors.ENDC)

def log(*msg):
    if(SHOW_Log):
        print(BColors.LOG,msg,BColors.ENDC)

def warn(*msg):
    print(BColors.WARNING,msg,BColors.ENDC)
