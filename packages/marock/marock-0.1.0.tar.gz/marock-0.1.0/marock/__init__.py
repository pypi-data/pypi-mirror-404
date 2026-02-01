fg_colors = {
	"black": "\033[90m",
	"red": "\033[91m",
	"green": "\033[92m",
	"yellow": "\033[93m",
	"blue": "\033[94m",
	"magenta": "\033[95m",
	"cyan": "\033[96m",
	"white": "\033[97m"
}

bg_colors = {
	"black": "\033[100m",
	"red": "\033[101m",
	"green": "\033[102m",
	"yellow": "\033[103m",
	"blue": "\033[104m",
	"magenta": "\033[105m",
	"cyan": "\033[106m",
	"white": "\033[107m"
}

def col(text, fg="white", bold=False, bg=None):
	prefix = ""
	if bold:
		prefix += "\033[1m"
	prefix += fg_colors.get(fg.lower(), "\033[97m")
	if bg:
		prefix += bg_colors.get(bg.lower(), "")
	return f"{prefix}{text}\033[0m"
def help():
	txt = """
		"black": cool and shocking. 
                "red": elegant and energetic. 
                "green": natural and fresh. 
                "yellow": bright and popular. 
                "blue": melancholy and maturely.
                "magenta": exiting and passionate. 
                "cyan": peaceful and relaxing. 
                "white": classic and purely. 
		"""
	return txt
