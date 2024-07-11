import sys

def main():

	try:
		title = sys.argv[1]
		bat = int(sys.argv[2][0])
		ing = int(sys.argv[2][1])
		ins = int(sys.argv[2][2])
		noe = int(sys.argv[2][3])
	except (IndexError, ValueError):
		print("make_rp.py requires 2 inputs: [title <str>] [section options <4-digit int>]")
		exit()

	try:
		file = f"recipes/{title.lower().replace(' ', '_')}.rp"
		new_rp = open(file, "r")
		
		print(f"[WARNING] You are about to overwrite {file}, do you wish to proceed? [Y/n]")
		rep = input()
		if rep not in ["Y", "y"]:
			exit()

	except FileNotFoundError:
		pass

	new_rp = open(file, "w+")

	out_lst = [
		"<title>",
		title,
		"",
		"<tags>",
		"" ,
		"<itags>",
		"",
		"<batch>" + "*"*int(not bat),
		"",
		"<tools>",
		"",
		"[ing]",
		"[ins]",
		"<notes>" + "*"*int(not noe)
		]

	out_txt = "\n".join(out_lst)

	for i in range(ing):
		out_txt = out_txt.replace("[ing]", f"<ingredients {i}>\n\n[ing]")
	out_txt = out_txt.replace("\n[ing]", "")

	for i in range(ins):
		out_txt = out_txt.replace("[ins]", f"<instructions {i}>\n\n[ins]")
	out_txt = out_txt.replace("\n[ins]", "")

	out_txt = out_txt.replace(" 0", "")
	
	if "-v" in sys.argv:
		print(out_txt)

	new_rp.write(out_txt)

	







if __name__ == '__main__':
	main()