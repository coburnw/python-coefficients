import cmd

def getChar():
    # https://stackoverflow.com/a/36974338
    try:
        # for Windows-based systems
        import msvcrt # If successful, we are on Windows
        return msvcrt.getch()

    except ImportError:
        # for POSIX-based systems (with termios & tty support)
        import tty, sys, termios  # raises ImportError if unsupported

        fd = sys.stdin.fileno()
        oldSettings = termios.tcgetattr(fd)

        try:
            tty.setcbreak(fd)
            answer = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)

        return answer

class Shell(cmd.Cmd):
    intro = 'Shell Base Class.'
    prompt = 'shell: '

    def __init__(self, *kwargs):
        super().__init__(*kwargs)

        # https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
        self.Black = '\u001b[30m'
        self.Red = '\u001b[31m'
        self.Green = '\u001b[32m'
        self.Yellow = '\u001b[33m'
        self.Blue = '\u001b[34m'
        self.Magenta= '\u001b[35m'
        self.Cyan = '\u001b[36m'
        self.White = '\u001b[37m'
        self.Reset = '\u001b[0m'

        # self.prompt = '{}'.format(self.cyan(self.prompt))

        return

    def black(self, text):
        return '{}{}{}'.format(self.Black, text, self.Reset)
    
    def red(self, text):
        return '{}{}{}'.format(self.Red, text, self.Reset)
    
    def green(self, text):
        return '{}{}{}'.format(self.Green, text, self.Reset)

    def yellow(self, text):
        return '{}{}{}'.format(self.Yellow, text, self.Reset)

    def blue(self, text):
        return '{}{}{}'.format(self.Blue, text, self.Reset)

    def magenta(self, text):
        return '{}{}{}'.format(self.Magenta, text, self.Reset)

    def cyan(self, text):
        return '{}{}{}'.format(self.Cyan, text, self.Reset)

    def white(self, text):
        return '{}{}{}'.format(self.White, text, self.Reset)

    def get_char(self):
        return getChar()
    
